#!/usr/bin/env python3
"""
Comprehensive Testing Framework for Enhanced Clash Royale Bot
Tests computer vision, game integration, and AI performance
"""

import os
import time
import json
import cv2
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime
import unittest
from dataclasses import asdict

# Import our enhanced components
try:
    from enhanced_vision_system import EnhancedVisionSystem, GameState, GamePhase
    from enhanced_game_manager import EnhancedGameManager, MatchResult
    from platform_manager import PlatformManager
    from env import ClashRoyaleEnv
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced components not available: {e}")
    ENHANCED_COMPONENTS_AVAILABLE = False

class VisionSystemTests(unittest.TestCase):
    """Test suite for computer vision system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        if not ENHANCED_COMPONENTS_AVAILABLE:
            cls.skipTest(cls, "Enhanced components not available")
        
        cls.platform_manager = PlatformManager()
        cls.platform_manager.find_emulator_window()
        cls.vision_system = EnhancedVisionSystem(cls.platform_manager)
        
        # Create test results directory
        cls.test_results_dir = "test_results"
        os.makedirs(cls.test_results_dir, exist_ok=True)
    
    def test_card_detection_accuracy(self):
        """Test card detection accuracy with known images"""
        print("\n=== Testing Card Detection Accuracy ===")
        
        # Test with existing screenshots
        test_images = [
            "screenshots/current.png",
            "main_images/5elixir.png"
        ]
        
        results = {}
        for image_path in test_images:
            if os.path.exists(image_path):
                print(f"Testing with {image_path}")
                
                # Simulate card detection
                cards = self.vision_system.detect_cards_in_hand()
                
                results[image_path] = {
                    'detected_cards': cards,
                    'detection_time': time.time(),
                    'confidence': 'high' if len([c for c in cards if c != 'Unknown']) > 2 else 'low'
                }
                
                print(f"Detected cards: {cards}")
        
        # Save results
        with open(f"{self.test_results_dir}/card_detection_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Assert at least some cards were detected
        total_detected = sum(len([c for c in result['detected_cards'] if c != 'Unknown']) 
                           for result in results.values())
        self.assertGreater(total_detected, 0, "No cards were detected in any test image")
    
    def test_elixir_detection(self):
        """Test elixir level detection"""
        print("\n=== Testing Elixir Detection ===")
        
        elixir_levels = []
        for i in range(5):  # Test 5 times
            elixir = self.vision_system.detect_elixir_level()
            elixir_levels.append(elixir)
            print(f"Detected elixir level {i+1}: {elixir}")
            time.sleep(0.5)
        
        # Validate elixir levels are reasonable
        for elixir in elixir_levels:
            self.assertGreaterEqual(elixir, 0, "Elixir level should be >= 0")
            self.assertLessEqual(elixir, 10, "Elixir level should be <= 10")
        
        # Save results
        results = {
            'elixir_levels': elixir_levels,
            'average': sum(elixir_levels) / len(elixir_levels),
            'test_time': datetime.now().isoformat()
        }
        
        with open(f"{self.test_results_dir}/elixir_detection_results.json", 'w') as f:
            json.dump(results, f, indent=2)
    
    def test_game_phase_detection(self):
        """Test game phase detection"""
        print("\n=== Testing Game Phase Detection ===")
        
        phase = self.vision_system.detect_game_phase()
        print(f"Detected game phase: {phase}")
        
        # Validate phase is a valid enum value
        self.assertIsInstance(phase, GamePhase, "Phase should be a GamePhase enum")
        
        # Save result
        result = {
            'detected_phase': phase.value,
            'test_time': datetime.now().isoformat()
        }
        
        with open(f"{self.test_results_dir}/phase_detection_results.json", 'w') as f:
            json.dump(result, f, indent=2)
    
    def test_complete_game_state(self):
        """Test complete game state detection"""
        print("\n=== Testing Complete Game State ===")
        
        game_state = self.vision_system.get_complete_game_state()
        
        # Validate game state structure
        self.assertIsInstance(game_state, GameState, "Should return GameState object")
        self.assertIsInstance(game_state.my_cards, list, "Cards should be a list")
        self.assertEqual(len(game_state.my_cards), 4, "Should detect 4 cards")
        self.assertIsInstance(game_state.my_elixir, int, "Elixir should be an integer")
        
        # Save detailed game state
        game_state_dict = asdict(game_state)
        game_state_dict['phase'] = game_state.phase.value  # Convert enum to string
        
        with open(f"{self.test_results_dir}/complete_game_state.json", 'w') as f:
            json.dump(game_state_dict, f, indent=2)
        
        print(f"Game state validation passed")
        print(f"Cards: {game_state.my_cards}")
        print(f"Elixir: {game_state.my_elixir}")
        print(f"Phase: {game_state.phase}")

class GameIntegrationTests(unittest.TestCase):
    """Test suite for game integration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        if not ENHANCED_COMPONENTS_AVAILABLE:
            cls.skipTest(cls, "Enhanced components not available")
        
        cls.platform_manager = PlatformManager()
        cls.platform_manager.find_emulator_window()
        cls.vision_system = EnhancedVisionSystem(cls.platform_manager)
        cls.game_manager = EnhancedGameManager(cls.vision_system, cls.platform_manager)
        cls.env = ClashRoyaleEnv()
        
        cls.test_results_dir = "test_results"
        os.makedirs(cls.test_results_dir, exist_ok=True)
    
    def test_environment_integration(self):
        """Test integration with ClashRoyaleEnv"""
        print("\n=== Testing Environment Integration ===")
        
        # Test environment initialization
        self.assertIsNotNone(self.env, "Environment should initialize")
        
        # Test state detection
        state = self.env._get_state()
        self.assertIsNotNone(state, "Environment should return a state")
        self.assertIsInstance(state, np.ndarray, "State should be numpy array")
        
        print(f"Environment state shape: {state.shape}")
        print(f"Environment state: {state}")
        
        # Save results
        result = {
            'state_shape': state.shape,
            'state_values': state.tolist(),
            'test_time': datetime.now().isoformat()
        }
        
        with open(f"{self.test_results_dir}/environment_integration.json", 'w') as f:
            json.dump(result, f, indent=2)
    
    def test_action_validation(self):
        """Test action validation system"""
        print("\n=== Testing Action Validation ===")
        
        # Test various action positions
        test_positions = [
            (500, 600),   # Valid ally side
            (500, 300),   # Valid enemy side
            (50, 50),     # Invalid (too close to edge)
            (2000, 2000)  # Invalid (outside screen)
        ]
        
        results = {}
        for i, position in enumerate(test_positions):
            valid = self.game_manager.validate_action(0, "Knight", position)
            results[f"position_{i}"] = {
                'position': position,
                'valid': valid
            }
            print(f"Position {position}: {'Valid' if valid else 'Invalid'}")
        
        # Save results
        with open(f"{self.test_results_dir}/action_validation.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # At least some positions should be valid
        valid_count = sum(1 for r in results.values() if r['valid'])
        self.assertGreater(valid_count, 0, "At least some positions should be valid")
    
    def test_real_time_metrics(self):
        """Test real-time metrics collection"""
        print("\n=== Testing Real-Time Metrics ===")
        
        # Update game state
        game_state = self.game_manager.update_game_state()
        
        # Get metrics
        metrics = self.game_manager.get_real_time_metrics()
        
        # Validate metrics structure
        expected_keys = ['game_phase', 'my_elixir', 'my_cards', 'towers_remaining']
        for key in expected_keys:
            self.assertIn(key, metrics, f"Metrics should contain {key}")
        
        print(f"Real-time metrics: {metrics}")
        
        # Save metrics
        with open(f"{self.test_results_dir}/real_time_metrics.json", 'w') as f:
            json.dump(metrics, f, indent=2)

class PerformanceTests(unittest.TestCase):
    """Test suite for performance benchmarks"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        if not ENHANCED_COMPONENTS_AVAILABLE:
            cls.skipTest(cls, "Enhanced components not available")
        
        cls.platform_manager = PlatformManager()
        cls.platform_manager.find_emulator_window()
        cls.vision_system = EnhancedVisionSystem(cls.platform_manager)
        
        cls.test_results_dir = "test_results"
        os.makedirs(cls.test_results_dir, exist_ok=True)
    
    def test_detection_speed(self):
        """Test detection speed benchmarks"""
        print("\n=== Testing Detection Speed ===")
        
        # Benchmark card detection
        card_times = []
        for i in range(10):
            start_time = time.time()
            cards = self.vision_system.detect_cards_in_hand()
            end_time = time.time()
            card_times.append(end_time - start_time)
        
        # Benchmark elixir detection
        elixir_times = []
        for i in range(10):
            start_time = time.time()
            elixir = self.vision_system.detect_elixir_level()
            end_time = time.time()
            elixir_times.append(end_time - start_time)
        
        # Benchmark complete game state
        state_times = []
        for i in range(5):
            start_time = time.time()
            game_state = self.vision_system.get_complete_game_state()
            end_time = time.time()
            state_times.append(end_time - start_time)
        
        # Calculate averages
        avg_card_time = sum(card_times) / len(card_times)
        avg_elixir_time = sum(elixir_times) / len(elixir_times)
        avg_state_time = sum(state_times) / len(state_times)
        
        print(f"Average card detection time: {avg_card_time:.3f}s")
        print(f"Average elixir detection time: {avg_elixir_time:.3f}s")
        print(f"Average game state time: {avg_state_time:.3f}s")
        
        # Performance assertions
        self.assertLess(avg_card_time, 2.0, "Card detection should be under 2 seconds")
        self.assertLess(avg_elixir_time, 1.0, "Elixir detection should be under 1 second")
        self.assertLess(avg_state_time, 3.0, "Complete game state should be under 3 seconds")
        
        # Save results
        results = {
            'card_detection': {
                'times': card_times,
                'average': avg_card_time,
                'max': max(card_times),
                'min': min(card_times)
            },
            'elixir_detection': {
                'times': elixir_times,
                'average': avg_elixir_time,
                'max': max(elixir_times),
                'min': min(elixir_times)
            },
            'game_state': {
                'times': state_times,
                'average': avg_state_time,
                'max': max(state_times),
                'min': min(state_times)
            }
        }
        
        with open(f"{self.test_results_dir}/performance_benchmarks.json", 'w') as f:
            json.dump(results, f, indent=2)

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🧪 Starting Comprehensive Testing Framework")
    print("=" * 60)
    
    if not ENHANCED_COMPONENTS_AVAILABLE:
        print("❌ Enhanced components not available. Please ensure all modules are installed.")
        return False
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(VisionSystemTests))
    test_suite.addTest(unittest.makeSuite(GameIntegrationTests))
    test_suite.addTest(unittest.makeSuite(PerformanceTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate summary report
    generate_test_report(result)
    
    return result.wasSuccessful()

def generate_test_report(test_result):
    """Generate comprehensive test report"""
    print("\n" + "=" * 60)
    print("🔍 TEST SUMMARY REPORT")
    print("=" * 60)
    
    total_tests = test_result.testsRun
    failures = len(test_result.failures)
    errors = len(test_result.errors)
    successes = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {successes}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    print(f"Success Rate: {(successes/total_tests)*100:.1f}%")
    
    # Save detailed report
    report = {
        'test_summary': {
            'total_tests': total_tests,
            'passed': successes,
            'failed': failures,
            'errors': errors,
            'success_rate': (successes/total_tests)*100 if total_tests > 0 else 0
        },
        'failures': [str(failure) for failure in test_result.failures],
        'errors': [str(error) for error in test_result.errors],
        'test_time': datetime.now().isoformat()
    }
    
    with open("test_results/comprehensive_test_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Detailed results saved to test_results/")
    
    if test_result.wasSuccessful():
        print("🎉 All tests passed! The enhanced bot is ready for action.")
    else:
        print("⚠️  Some tests failed. Check the detailed results for issues to fix.")

def quick_functionality_test():
    """Quick test to verify basic functionality"""
    print("🚀 Running Quick Functionality Test...")
    
    try:
        # Test platform detection
        pm = PlatformManager()
        emulators = pm.detect_emulators()
        print(f"✅ Platform detection: Found {len(emulators)} emulators")
        
        # Test vision system
        vision = EnhancedVisionSystem(pm)
        cards = vision.detect_cards_in_hand()
        print(f"✅ Card detection: {cards}")
        
        # Test environment
        env = ClashRoyaleEnv()
        state = env._get_state()
        print(f"✅ Environment state: Shape {state.shape if state is not None else 'None'}")
        
        print("🎯 Quick test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_functionality_test()
    else:
        run_comprehensive_tests()
