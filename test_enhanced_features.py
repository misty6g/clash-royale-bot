#!/usr/bin/env python3
"""
Test suite for enhanced Clash Royale bot features
Tests Redis integration, fallback mechanisms, and performance monitoring
"""

import unittest
import time
import os
import tempfile
import json
from unittest.mock import Mock, patch

# Import our enhanced modules
from config import BotConfig
from redis_card_manager import RedisCardManager
from card_learning_system import CardLearningSystem
from opponent_tracker import OpponentTracker
from counter_strategy import CounterStrategy
from performance_monitor import PerformanceMonitor
from fallback_manager import FallbackManager
from data_backup_manager import DataBackupManager

class TestBotConfig(unittest.TestCase):
    def test_default_config(self):
        """Test default configuration values"""
        config = BotConfig()
        self.assertTrue(config.ENABLE_REDIS)
        self.assertFalse(config.ENABLE_LEARNING)
        self.assertFalse(config.ENABLE_COUNTER_STRATEGY)
        self.assertEqual(config.REDIS_HOST, 'localhost')
        self.assertEqual(config.REDIS_PORT, 6379)

    def test_safe_defaults(self):
        """Test safe defaults preserve existing behavior"""
        config = BotConfig()
        defaults = config.get_safe_defaults()
        self.assertFalse(defaults['ENABLE_REDIS'])
        self.assertFalse(defaults['ENABLE_LEARNING'])

class TestRedisCardManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.config = BotConfig()
        self.config.ENABLE_REDIS = False  # Start with Redis disabled for testing
        
        # Create temporary cards.json for testing
        self.temp_cards_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        test_cards = {
            "Knight": {
                "elixir_cost": 3,
                "type": "troop",
                "danger_level": 4,
                "counters": ["Archers", "Minions"],
                "countered_by": ["Valkyrie", "Bomber"],
                "synergies": ["Archers", "Hog Rider"]
            }
        }
        json.dump(test_cards, self.temp_cards_file)
        self.temp_cards_file.close()

    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_cards_file.name)

    def test_json_fallback_loading(self):
        """Test that JSON fallback works correctly"""
        manager = RedisCardManager(self.config)
        manager.cards_json_path = self.temp_cards_file.name
        manager._load_json_fallback()
        
        self.assertIn("Knight", manager.json_cards)
        self.assertEqual(manager.json_cards["Knight"]["elixir_cost"], 3)

    def test_get_card_data_fallback(self):
        """Test getting card data with JSON fallback"""
        manager = RedisCardManager(self.config)
        manager.cards_json_path = self.temp_cards_file.name
        manager._load_json_fallback()
        
        card_data = manager.get_card_data("Knight")
        self.assertEqual(card_data["elixir_cost"], 3)
        self.assertEqual(card_data["type"], "troop")

    def test_redis_unavailable_handling(self):
        """Test behavior when Redis is unavailable"""
        manager = RedisCardManager(self.config)
        self.assertFalse(manager.redis_available)
        
        # Should still work with JSON fallback
        manager.cards_json_path = self.temp_cards_file.name
        manager._load_json_fallback()
        card_data = manager.get_card_data("Knight")
        self.assertIsNotNone(card_data)

class TestPerformanceMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = PerformanceMonitor()

    def test_decision_time_tracking(self):
        """Test decision time tracking"""
        self.monitor.track_decision_time(150.0)
        self.monitor.track_decision_time(200.0)
        
        self.assertEqual(self.monitor.metrics['total_decisions'], 2)
        self.assertEqual(self.monitor.metrics['avg_decision_time'], 175.0)
        self.assertEqual(self.monitor.metrics['max_decision_time'], 200.0)

    def test_performance_warnings(self):
        """Test performance warning detection"""
        # Should trigger warning for slow decision
        self.monitor.track_decision_time(600.0)  # Very slow
        self.assertGreater(self.monitor.metrics['performance_warnings'], 0)

    def test_should_disable_features(self):
        """Test feature disabling logic"""
        # Add many slow decisions
        for _ in range(15):
            self.monitor.track_decision_time(600.0)
        
        self.assertTrue(self.monitor.should_disable_features())

    def test_performance_report(self):
        """Test performance report generation"""
        self.monitor.track_decision_time(100.0)
        self.monitor.track_decision_time(200.0)
        
        report = self.monitor.get_performance_report()
        self.assertIn('total_decisions', report)
        self.assertIn('avg_decision_time', report)
        self.assertIn('status', report)

class TestCardLearningSystem(unittest.TestCase):
    def setUp(self):
        config = BotConfig()
        config.ENABLE_REDIS = False
        self.redis_manager = RedisCardManager(config)
        self.learning_system = CardLearningSystem(self.redis_manager)

    def test_track_card_play(self):
        """Test card play tracking"""
        timestamp = time.time()
        self.learning_system.track_card_play(
            "Knight", ["Archers", "Minions"], (100, 200), timestamp
        )
        
        self.assertEqual(len(self.learning_system.battle_history), 1)
        event = self.learning_system.battle_history[0]
        self.assertEqual(event['my_card'], "Knight")
        self.assertEqual(event['enemy_cards'], ["Archers", "Minions"])

    def test_cleanup_old_history(self):
        """Test battle history cleanup"""
        old_timestamp = time.time() - 400  # 400 seconds ago
        recent_timestamp = time.time()
        
        self.learning_system.track_card_play("Knight", [], (0, 0), old_timestamp)
        self.learning_system.track_card_play("Archers", [], (0, 0), recent_timestamp)
        
        self.learning_system.cleanup_old_history(max_age_seconds=300)
        self.assertEqual(len(self.learning_system.battle_history), 1)
        self.assertEqual(self.learning_system.battle_history[0]['my_card'], "Archers")

class TestOpponentTracker(unittest.TestCase):
    def setUp(self):
        config = BotConfig()
        config.ENABLE_REDIS = False
        self.redis_manager = RedisCardManager(config)
        self.tracker = OpponentTracker(self.redis_manager)

    def test_track_opponent_card(self):
        """Test opponent card tracking"""
        self.tracker.track_opponent_card("Knight", 3)
        
        self.assertIn("Knight", self.tracker.opponent_deck)
        self.assertEqual(self.tracker.opponent_elixir, 7)  # 10 - 3
        self.assertEqual(len(self.tracker.opponent_card_cycle), 1)

    def test_elixir_estimation(self):
        """Test elixir estimation over time"""
        self.tracker.track_opponent_card("Knight", 3)
        initial_time = self.tracker.last_opponent_play_time
        
        # Simulate time passing
        self.tracker.last_opponent_play_time = initial_time - 5.6  # 5.6 seconds ago
        estimated = self.tracker.estimate_opponent_elixir()
        
        # Should have gained ~2 elixir (5.6 / 2.8)
        self.assertGreater(estimated, 8.5)

    def test_strategy_prediction(self):
        """Test strategy prediction"""
        # Add high-cost cards for beatdown strategy
        self.tracker.opponent_deck = {"Golem", "P.E.K.K.A", "Giant"}
        
        # Mock card data
        self.redis_manager.json_cards = {
            "Golem": {"elixir_cost": 8},
            "P.E.K.K.A": {"elixir_cost": 7},
            "Giant": {"elixir_cost": 5}
        }
        
        strategy = self.tracker.predict_opponent_strategy()
        self.assertEqual(strategy, "beatdown")

class TestCounterStrategy(unittest.TestCase):
    def setUp(self):
        config = BotConfig()
        config.ENABLE_REDIS = False
        self.redis_manager = RedisCardManager(config)
        
        # Mock card data
        self.redis_manager.json_cards = {
            "Knight": {
                "elixir_cost": 3,
                "counters": ["Archers", "Minions"],
                "countered_by": ["Valkyrie"]
            },
            "Archers": {"elixir_cost": 3},
            "Minions": {"elixir_cost": 3},
            "Valkyrie": {"elixir_cost": 4}
        }
        
        self.strategy = CounterStrategy(self.redis_manager)

    def test_get_best_counter(self):
        """Test counter selection"""
        my_hand = ["Knight", "Archers"]
        best_counter = self.strategy.get_best_counter("Minions", my_hand)
        
        # Knight should be a good counter to Minions based on our mock data
        self.assertIn(best_counter, my_hand)

    def test_predict_opponent_response(self):
        """Test opponent response prediction"""
        responses = self.strategy.predict_opponent_response("Knight")
        self.assertIn("Valkyrie", responses)

if __name__ == '__main__':
    print("Running enhanced features test suite...")
    unittest.main(verbosity=2)
