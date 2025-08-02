#!/usr/bin/env python3
"""
Enhanced Integration Test Script
Tests all enhanced components working together
"""

import os
import sys
import time
import traceback
from typing import Dict, Any

def test_imports():
    """Test that all enhanced components can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test basic imports
        import numpy as np
        import cv2
        print("✅ Basic dependencies (numpy, cv2)")
        
        # Test platform manager
        from platform_manager import PlatformManager
        print("✅ Platform manager")
        
        # Test enhanced vision system
        from enhanced_vision_system import EnhancedVisionSystem, GameState, GamePhase
        print("✅ Enhanced vision system")
        
        # Test enhanced game manager
        from enhanced_game_manager import EnhancedGameManager, MatchResult
        print("✅ Enhanced game manager")
        
        # Test environment
        from env import ClashRoyaleEnv
        print("✅ Enhanced environment")
        
        # Test training system
        from enhanced_training import EnhancedTrainingSystem
        print("✅ Enhanced training system")
        
        # Test comprehensive testing
        from comprehensive_testing import run_comprehensive_tests
        print("✅ Comprehensive testing framework")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False

def test_platform_detection():
    """Test platform and emulator detection"""
    print("\n🖥️  Testing platform detection...")
    
    try:
        from platform_manager import PlatformManager
        
        pm = PlatformManager()
        print(f"Platform: {pm.platform}")
        
        # Test emulator detection
        emulators = pm.detect_emulators()
        print(f"Detected emulators: {len(emulators)}")
        
        for emulator in emulators:
            print(f"  - {emulator['name']}: {emulator['status']}")
        
        # Test window finding
        window_found = pm.find_emulator_window()
        if window_found:
            print(f"✅ Emulator window found: {pm.emulator_window}")
        else:
            print("⚠️  No emulator window found (this is OK if no emulator is running)")
        
        return True
        
    except Exception as e:
        print(f"❌ Platform detection failed: {e}")
        traceback.print_exc()
        return False

def test_vision_system():
    """Test enhanced vision system"""
    print("\n👁️  Testing enhanced vision system...")
    
    try:
        from platform_manager import PlatformManager
        from enhanced_vision_system import EnhancedVisionSystem
        
        # Initialize components
        pm = PlatformManager()
        pm.find_emulator_window()
        
        vision = EnhancedVisionSystem(pm)
        print("✅ Vision system initialized")
        
        # Test card detection
        print("Testing card detection...")
        cards = vision.detect_cards_in_hand()
        print(f"Detected cards: {cards}")
        
        # Test elixir detection
        print("Testing elixir detection...")
        elixir = vision.detect_elixir_level()
        print(f"Detected elixir: {elixir}")
        
        # Test game phase detection
        print("Testing game phase detection...")
        phase = vision.detect_game_phase()
        print(f"Detected phase: {phase}")
        
        # Test complete game state
        print("Testing complete game state...")
        game_state = vision.get_complete_game_state()
        print(f"Game state phase: {game_state.phase}")
        print(f"Game state elixir: {game_state.my_elixir}")
        print(f"Game state cards: {game_state.my_cards}")
        
        # Save debug images
        vision.save_debug_images("integration_test")
        print("✅ Debug images saved")
        
        return True
        
    except Exception as e:
        print(f"❌ Vision system test failed: {e}")
        traceback.print_exc()
        return False

def test_game_manager():
    """Test enhanced game manager"""
    print("\n🎮 Testing enhanced game manager...")
    
    try:
        from platform_manager import PlatformManager
        from enhanced_vision_system import EnhancedVisionSystem
        from enhanced_game_manager import EnhancedGameManager
        
        # Initialize components
        pm = PlatformManager()
        pm.find_emulator_window()
        
        vision = EnhancedVisionSystem(pm)
        game_manager = EnhancedGameManager(vision, pm)
        print("✅ Game manager initialized")
        
        # Test game state update
        print("Testing game state update...")
        game_state = game_manager.update_game_state()
        if game_state:
            print(f"✅ Game state updated: {game_state.phase}")
        else:
            print("⚠️  Game state is None")
        
        # Test action validation
        print("Testing action validation...")
        valid_positions = [
            (500, 600),   # Ally side
            (500, 300),   # Enemy side
        ]
        
        for pos in valid_positions:
            valid = game_manager.validate_action(0, "Knight", pos)
            print(f"Position {pos}: {'Valid' if valid else 'Invalid'}")
        
        # Test real-time metrics
        print("Testing real-time metrics...")
        metrics = game_manager.get_real_time_metrics()
        print(f"Metrics keys: {list(metrics.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Game manager test failed: {e}")
        traceback.print_exc()
        return False

def test_environment_integration():
    """Test environment with enhanced features"""
    print("\n🌍 Testing environment integration...")
    
    try:
        from env import ClashRoyaleEnv
        
        # Initialize environment
        env = ClashRoyaleEnv()
        print("✅ Environment initialized")
        
        # Check enhanced mode
        if hasattr(env, 'enhanced_mode') and env.enhanced_mode:
            print("✅ Enhanced mode detected")
        else:
            print("⚠️  Enhanced mode not available")
        
        # Test state detection
        print("Testing state detection...")
        state = env._get_state()
        if state is not None:
            print(f"✅ State detected: shape {state.shape}")
        else:
            print("⚠️  State is None")
        
        # Test card detection
        print("Testing card detection...")
        cards = env.detect_cards_in_hand()
        print(f"Detected cards: {cards}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment integration test failed: {e}")
        traceback.print_exc()
        return False

def test_training_system():
    """Test enhanced training system"""
    print("\n🏋️  Testing enhanced training system...")
    
    try:
        from enhanced_training import EnhancedTrainingSystem
        
        # Initialize training system
        trainer = EnhancedTrainingSystem()
        print("✅ Training system initialized")
        
        # Check enhanced mode
        if trainer.enhanced_mode:
            print("✅ Enhanced mode active in training")
        else:
            print("⚠️  Enhanced mode not active in training")
        
        # Test game manager integration
        if trainer.game_manager:
            print("✅ Game manager integrated")
        else:
            print("⚠️  Game manager not available")
        
        print("✅ Training system test completed")
        return True
        
    except Exception as e:
        print(f"❌ Training system test failed: {e}")
        traceback.print_exc()
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 ENHANCED CLASH ROYALE BOT - INTEGRATION TESTS")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Imports", test_imports),
        ("Platform Detection", test_platform_detection),
        ("Vision System", test_vision_system),
        ("Game Manager", test_game_manager),
        ("Environment Integration", test_environment_integration),
        ("Training System", test_training_system),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            test_results[test_name] = result
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
            test_results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("🔍 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("The enhanced Clash Royale bot is ready for action! 🤖⚔️")
        return True
    else:
        print(f"\n⚠️  {total-passed} tests failed. Check the output above for details.")
        return False

def quick_smoke_test():
    """Quick smoke test for basic functionality"""
    print("💨 Running quick smoke test...")
    
    try:
        # Test basic imports
        from platform_manager import PlatformManager
        from enhanced_vision_system import EnhancedVisionSystem
        from env import ClashRoyaleEnv
        
        # Test basic initialization
        pm = PlatformManager()
        vision = EnhancedVisionSystem(pm)
        env = ClashRoyaleEnv()
        
        print("✅ Quick smoke test passed - basic components work!")
        return True
        
    except Exception as e:
        print(f"❌ Quick smoke test failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_smoke_test()
    else:
        success = run_integration_tests()
        sys.exit(0 if success else 1)
