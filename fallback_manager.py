import time
from redis_card_manager import RedisCardManager

class FallbackManager:
    def __init__(self, redis_manager: RedisCardManager):
        self.redis_manager = redis_manager
        self.fallback_triggers = {
            'connection_lost': 0,      # Immediate fallback
            'timeout': 100,            # 100ms timeout = fallback
            'high_latency': 50,        # >50ms = fallback
            'memory_full': 0,          # Immediate fallback
            'corruption': 0            # Immediate fallback
        }

    def check_fallback_conditions(self, operation_time_ms: float, error_type: str = None) -> bool:
        """Determine if fallback should be triggered"""
        if error_type and error_type in self.fallback_triggers:
            threshold = self.fallback_triggers[error_type]
            if threshold == 0:  # Immediate fallback
                return True
            elif operation_time_ms > threshold:
                return True

        # General performance fallback
        if operation_time_ms > 50:  # 50ms threshold
            return True

        return False

    def execute_fallback(self, reason: str):
        """Execute fallback with specific procedures"""
        print(f"Executing fallback due to: {reason}")

        # Step 1: Disable Redis immediately
        self.redis_manager.redis_available = False

        # Step 2: Ensure JSON fallback is ready
        if not hasattr(self.redis_manager, 'json_cards') or not self.redis_manager.json_cards:
            self.redis_manager._load_json_fallback()

        # Step 3: Log fallback for monitoring
        self.redis_manager.fallback_count += 1
        self.redis_manager.last_fallback_time = time.time()

        print(f"Fallback complete - using JSON mode (fallback #{self.redis_manager.fallback_count})")

    def attempt_recovery(self) -> bool:
        """Attempt to recover Redis connection"""
        if not self.redis_manager.config.ENABLE_REDIS:
            return False
            
        try:
            print("Attempting Redis recovery...")
            self.redis_manager._initialize_redis()
            if self.redis_manager.redis_available:
                print("Redis recovery successful")
                return True
            else:
                print("Redis recovery failed")
                return False
        except Exception as e:
            print(f"Redis recovery failed with error: {e}")
            return False

    def get_fallback_stats(self) -> dict:
        """Get fallback statistics"""
        return {
            'fallback_count': self.redis_manager.fallback_count,
            'last_fallback_time': self.redis_manager.last_fallback_time,
            'redis_available': self.redis_manager.redis_available,
            'time_since_last_fallback': time.time() - self.redis_manager.last_fallback_time if self.redis_manager.last_fallback_time > 0 else 0
        }
