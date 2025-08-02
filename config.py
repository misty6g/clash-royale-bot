import os
from typing import Dict, Any

class BotConfig:
    def __init__(self):
        # Redis Configuration with safe defaults
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        self.REDIS_TIMEOUT = int(os.getenv('REDIS_TIMEOUT', 2))  # Reduced for real-time gameplay
        self.REDIS_MAX_RETRIES = int(os.getenv('REDIS_MAX_RETRIES', 1))  # Quick fallback

        # Feature Flags for gradual rollout
        self.ENABLE_REDIS = os.getenv('ENABLE_REDIS', 'true').lower() == 'true'
        self.ENABLE_LEARNING = os.getenv('ENABLE_LEARNING', 'false').lower() == 'true'  # Start disabled
        self.ENABLE_COUNTER_STRATEGY = os.getenv('ENABLE_COUNTER_STRATEGY', 'false').lower() == 'true'
        self.ENABLE_OPPONENT_TRACKING = os.getenv('ENABLE_OPPONENT_TRACKING', 'false').lower() == 'true'

        # Performance Requirements
        self.MAX_REDIS_LATENCY_MS = int(os.getenv('MAX_REDIS_LATENCY_MS', 50))
        self.MAX_DECISION_TIME_MS = int(os.getenv('MAX_DECISION_TIME_MS', 200))
        self.CACHE_TTL = int(os.getenv('CACHE_TTL', 30))  # Shorter for real-time updates

        # Learning Parameters (conservative defaults)
        self.LEARNING_RATE = float(os.getenv('LEARNING_RATE', 0.02))  # Very conservative
        self.CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.8))  # Higher threshold
        self.BATTLE_OUTCOME_WINDOW = int(os.getenv('BATTLE_OUTCOME_WINDOW', 5))  # Shorter window
        self.MAX_BATTLE_HISTORY = int(os.getenv('MAX_BATTLE_HISTORY', 500))  # Smaller for memory

        # Fallback and Recovery
        self.ENABLE_REDIS_FALLBACK = True  # Always enabled for safety
        self.BACKUP_INTERVAL = int(os.getenv('BACKUP_INTERVAL', 1800))  # 30 minutes
        self.FALLBACK_THRESHOLD_MS = int(os.getenv('FALLBACK_THRESHOLD_MS', 100))

        # Preserve existing DQN parameters (NEVER change these)
        self.DQN_EPSILON_DECAY = 0.997  # From existing dqn_agent.py
        self.DQN_LEARNING_RATE = 0.001  # From existing dqn_agent.py
        self.DQN_GAMMA = 0.95  # From existing dqn_agent.py

    def get_safe_defaults(self) -> Dict[str, Any]:
        """Return configuration that preserves existing behavior"""
        return {
            'ENABLE_REDIS': False,
            'ENABLE_LEARNING': False,
            'ENABLE_COUNTER_STRATEGY': False,
            'ENABLE_OPPONENT_TRACKING': False
        }
