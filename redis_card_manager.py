import redis
import json
import time
from typing import Dict, List, Optional
from config import BotConfig

class RedisCardManager:
    def __init__(self, config: BotConfig = None):
        self.config = config or BotConfig()
        self.cards_json_path = 'cards.json'
        self.card_prefix = "card:"
        self.counter_prefix = "counter:"
        self.synergy_prefix = "synergy:"
        self.redis_available = False
        self.last_fallback_time = 0
        self.fallback_count = 0

        # Always load JSON as backup
        self._load_json_fallback()

        # Try Redis only if enabled
        if self.config.ENABLE_REDIS:
            self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis with comprehensive error handling"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                decode_responses=True,
                socket_timeout=self.config.REDIS_TIMEOUT,
                socket_connect_timeout=self.config.REDIS_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30
            )

            # Test connection with timeout
            start_time = time.time()
            self.redis_client.ping()
            latency = (time.time() - start_time) * 1000

            if latency > self.config.MAX_REDIS_LATENCY_MS:
                print(f"Redis latency too high ({latency:.1f}ms), using JSON fallback")
                self.redis_available = False
                return

            self.redis_available = True
            print(f"Redis connection established (latency: {latency:.1f}ms)")

        except Exception as e:
            print(f"Redis initialization failed: {e}")
            self.redis_available = False
            self.fallback_count += 1

    def _load_json_fallback(self):
        """Load cards.json as fallback when Redis is unavailable"""
        try:
            with open(self.cards_json_path, 'r') as f:
                self.json_cards = json.load(f)
            print(f"Loaded {len(self.json_cards)} cards from JSON fallback")
        except Exception as e:
            print(f"CRITICAL: Cannot load cards.json: {e}")
            self.json_cards = {}

    def _redis_operation_with_fallback(self, operation, *args, **kwargs):
        """Execute Redis operation with automatic fallback"""
        if not self.redis_available:
            return None

        try:
            start_time = time.time()
            result = operation(*args, **kwargs)
            latency = (time.time() - start_time) * 1000

            if latency > self.config.MAX_REDIS_LATENCY_MS:
                print(f"Redis operation too slow ({latency:.1f}ms), falling back")
                self._trigger_fallback()
                return None

            return result

        except Exception as e:
            print(f"Redis operation failed: {e}")
            self._trigger_fallback()
            return None

    def _trigger_fallback(self):
        """Trigger fallback to JSON mode"""
        self.redis_available = False
        self.last_fallback_time = time.time()
        self.fallback_count += 1
        print(f"Switched to JSON fallback mode (fallback #{self.fallback_count})")

    def get_card_data(self, card_name: str) -> Dict:
        """Get card data with automatic fallback"""
        if self.redis_available:
            result = self._redis_operation_with_fallback(
                self.redis_client.hgetall, f"{self.card_prefix}{card_name}"
            )
            if result:
                return result

        # Fallback to JSON
        return self.json_cards.get(card_name, {})

    def load_cards_from_json(self, json_path: str):
        """Load initial card data from cards.json into Redis"""
        with open(json_path, 'r') as f:
            cards_data = json.load(f)

        # Always update JSON fallback
        self.json_cards = cards_data

        # Try to populate Redis if available
        if self.redis_available:
            for card_name, card_data in cards_data.items():
                self.store_card(card_name, card_data)

    def store_card(self, card_name: str, card_data: Dict):
        """Store card data in Redis with error handling"""
        if not self.redis_available:
            return False

        try:
            card_key = f"{self.card_prefix}{card_name}"

            # Store static properties as hash
            static_props = {k: v for k, v in card_data.items()
                           if k not in ['counters', 'countered_by', 'synergies']}
            self._redis_operation_with_fallback(
                self.redis_client.hset, card_key, mapping=static_props
            )

            # Store dynamic lists as sorted sets with confidence scores
            for counter in card_data.get('counters', []):
                self._redis_operation_with_fallback(
                    self.redis_client.zadd, f"{card_key}:counters", {counter: 1.0}
                )

            for synergy in card_data.get('synergies', []):
                self._redis_operation_with_fallback(
                    self.redis_client.zadd, f"{card_key}:synergies", {synergy: 1.0}
                )

            for countered in card_data.get('countered_by', []):
                self._redis_operation_with_fallback(
                    self.redis_client.zadd, f"{card_key}:countered_by", {countered: 1.0}
                )
            return True

        except Exception as e:
            print(f"Failed to store card {card_name}: {e}")
            return False
