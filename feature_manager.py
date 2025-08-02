import os
import json
import time
from typing import Dict, List
from config import BotConfig

class FeatureManager:
    def __init__(self, config: BotConfig = None):
        self.config = config or BotConfig()
        self.features_file = "feature_flags.json"
        self.features = {
            'REDIS': False,
            'LEARNING': False,
            'COUNTER_STRATEGY': False,
            'OPPONENT_TRACKING': False,
            'PERFORMANCE_MONITORING': True  # Always enabled for safety
        }
        self.feature_tests = {}
        self.load_feature_flags()

    def load_feature_flags(self):
        """Load feature flags from file"""
        try:
            if os.path.exists(self.features_file):
                with open(self.features_file, 'r') as f:
                    saved_features = json.load(f)
                    self.features.update(saved_features)
                print(f"Loaded feature flags from {self.features_file}")
        except Exception as e:
            print(f"Failed to load feature flags: {e}")

    def save_feature_flags(self):
        """Save current feature flags to file"""
        try:
            with open(self.features_file, 'w') as f:
                json.dump(self.features, f, indent=2)
            print(f"Saved feature flags to {self.features_file}")
        except Exception as e:
            print(f"Failed to save feature flags: {e}")

    def enable_feature(self, feature_name: str, force: bool = False) -> bool:
        """Safely enable a feature with validation"""
        if feature_name not in self.features:
            print(f"Unknown feature: {feature_name}")
            return False

        if not force and not self._test_feature(feature_name):
            print(f"Feature {feature_name} failed validation, keeping disabled")
            return False

        self.features[feature_name] = True
        self.save_feature_flags()
        print(f"Feature {feature_name} enabled successfully")
        return True

    def disable_feature(self, feature_name: str) -> bool:
        """Disable a feature"""
        if feature_name not in self.features:
            print(f"Unknown feature: {feature_name}")
            return False

        if feature_name == 'PERFORMANCE_MONITORING':
            print("Cannot disable performance monitoring - it's required for safety")
            return False

        self.features[feature_name] = False
        self.save_feature_flags()
        print(f"Feature {feature_name} disabled")
        return True

    def _test_feature(self, feature_name: str) -> bool:
        """Test if a feature can be safely enabled"""
        test_results = {
            'REDIS': self._test_redis_connection,
            'LEARNING': self._test_learning_system,
            'COUNTER_STRATEGY': self._test_counter_strategy,
            'OPPONENT_TRACKING': self._test_opponent_tracking,
            'PERFORMANCE_MONITORING': lambda: True  # Always passes
        }

        if feature_name in test_results:
            try:
                result = test_results[feature_name]()
                self.feature_tests[feature_name] = {
                    'result': result,
                    'timestamp': time.time(),
                    'error': None
                }
                return result
            except Exception as e:
                self.feature_tests[feature_name] = {
                    'result': False,
                    'timestamp': time.time(),
                    'error': str(e)
                }
                print(f"Feature test failed for {feature_name}: {e}")
                return False

        return False

    def _test_redis_connection(self) -> bool:
        """Test Redis connection"""
        try:
            from redis_card_manager import RedisCardManager
            manager = RedisCardManager(self.config)
            return manager.redis_available
        except Exception as e:
            print(f"Redis test failed: {e}")
            return False

    def _test_learning_system(self) -> bool:
        """Test learning system"""
        try:
            from card_learning_system import CardLearningSystem
            from redis_card_manager import RedisCardManager
            
            manager = RedisCardManager(self.config)
            learning = CardLearningSystem(manager)
            
            # Basic functionality test
            learning.track_card_play("Knight", ["Archers"], (100, 200), time.time())
            return len(learning.battle_history) > 0
        except Exception as e:
            print(f"Learning system test failed: {e}")
            return False

    def _test_counter_strategy(self) -> bool:
        """Test counter strategy system"""
        try:
            from counter_strategy import CounterStrategy
            from redis_card_manager import RedisCardManager
            
            manager = RedisCardManager(self.config)
            strategy = CounterStrategy(manager)
            
            # Basic functionality test
            counter = strategy.get_best_counter("Knight", ["Archers", "Minions"])
            return True  # If no exception, test passes
        except Exception as e:
            print(f"Counter strategy test failed: {e}")
            return False

    def _test_opponent_tracking(self) -> bool:
        """Test opponent tracking system"""
        try:
            from opponent_tracker import OpponentTracker
            from redis_card_manager import RedisCardManager
            
            manager = RedisCardManager(self.config)
            tracker = OpponentTracker(manager)
            
            # Basic functionality test
            tracker.track_opponent_card("Knight", 3)
            return "Knight" in tracker.opponent_deck
        except Exception as e:
            print(f"Opponent tracking test failed: {e}")
            return False

    def emergency_disable_all(self):
        """Emergency disable all enhanced features"""
        for feature in self.features:
            if feature != 'PERFORMANCE_MONITORING':
                self.features[feature] = False
        
        self.save_feature_flags()
        print("EMERGENCY: All enhanced features disabled - running in legacy mode")

    def get_feature_status(self) -> Dict:
        """Get current feature status"""
        status = {}
        for feature, enabled in self.features.items():
            status[feature] = {
                'enabled': enabled,
                'last_test': self.feature_tests.get(feature, {})
            }
        return status

    def print_feature_status(self):
        """Print current feature status"""
        print("\n=== Feature Status ===")
        for feature, enabled in self.features.items():
            status = "ENABLED" if enabled else "DISABLED"
            print(f"{feature}: {status}")
            
            if feature in self.feature_tests:
                test = self.feature_tests[feature]
                test_status = "PASS" if test['result'] else "FAIL"
                print(f"  Last test: {test_status}")
                if test['error']:
                    print(f"  Error: {test['error']}")
        print("=====================\n")

    def gradual_rollout(self, features_order: List[str] = None):
        """Gradually enable features in safe order"""
        if features_order is None:
            features_order = ['REDIS', 'OPPONENT_TRACKING', 'COUNTER_STRATEGY', 'LEARNING']

        print("Starting gradual feature rollout...")
        
        for feature in features_order:
            if feature in self.features:
                print(f"\nTesting {feature}...")
                if self.enable_feature(feature):
                    print(f"✓ {feature} enabled successfully")
                    time.sleep(2)  # Brief pause between features
                else:
                    print(f"✗ {feature} failed to enable, stopping rollout")
                    break
            else:
                print(f"Unknown feature in rollout: {feature}")

        print("\nRollout complete!")
        self.print_feature_status()

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return self.features.get(feature_name, False)

    def get_enabled_features(self) -> List[str]:
        """Get list of currently enabled features"""
        return [feature for feature, enabled in self.features.items() if enabled]
