import time
from typing import List, Dict
from redis_card_manager import RedisCardManager

class CardLearningSystem:
    def __init__(self, redis_manager: RedisCardManager):
        self.redis = redis_manager
        self.learning_rate = 0.1
        self.battle_history = []

    def track_card_play(self, my_card: str, enemy_cards_on_field: List[str],
                       placement_coords: tuple, timestamp: float):
        """Track when we play a card and what enemies are present"""
        play_event = {
            'my_card': my_card,
            'enemy_cards': enemy_cards_on_field.copy(),
            'placement': placement_coords,
            'timestamp': timestamp,
            'outcome_measured': False
        }
        self.battle_history.append(play_event)

    def update_counter_effectiveness(self, my_card: str, enemy_card: str,
                                   success: bool, damage_dealt: float):
        """Update counter relationships based on battle outcomes"""
        if not self.redis.redis_available:
            return

        counter_key = f"{self.redis.card_prefix}{my_card}:counters"

        # Get current confidence score
        current_score = self.redis.redis_client.zscore(counter_key, enemy_card) or 0.5

        # Update based on success/failure
        if success:
            new_score = min(1.0, current_score + self.learning_rate)
        else:
            new_score = max(0.1, current_score - self.learning_rate)

        self.redis.redis_client.zadd(counter_key, {enemy_card: new_score})

    def measure_battle_outcome(self, damage_dealt: float, damage_received: float,
                             elixir_trade: float, timestamp: float):
        """Measure outcome of recent card plays"""
        # Find recent plays within last 10 seconds
        recent_plays = [p for p in self.battle_history
                       if timestamp - p['timestamp'] <= 10.0 and not p['outcome_measured']]

        for play in recent_plays:
            success = damage_dealt > damage_received and elixir_trade > 0
            for enemy_card in play['enemy_cards']:
                self.update_counter_effectiveness(play['my_card'], enemy_card,
                                                success, damage_dealt)
            play['outcome_measured'] = True

    def update_danger_level(self, card_name: str, observed_threat: float):
        """Dynamically adjust danger level based on gameplay"""
        if not self.redis.redis_available:
            return

        card_key = f"{self.redis.card_prefix}{card_name}"
        current_danger = float(self.redis.redis_client.hget(card_key, 'danger_level') or 5)

        # Exponential moving average
        new_danger = current_danger * 0.9 + observed_threat * 0.1
        self.redis.redis_client.hset(card_key, 'danger_level', new_danger)

    def cleanup_old_history(self, max_age_seconds: int = 300):
        """Clean up old battle history to prevent memory bloat"""
        current_time = time.time()
        self.battle_history = [
            event for event in self.battle_history
            if current_time - event['timestamp'] <= max_age_seconds
        ]

    def get_learning_stats(self) -> Dict:
        """Get current learning statistics"""
        return {
            'battle_events': len(self.battle_history),
            'redis_available': self.redis.redis_available,
            'fallback_count': self.redis.fallback_count,
            'last_fallback': self.redis.last_fallback_time
        }
