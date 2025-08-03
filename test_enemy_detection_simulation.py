#!/usr/bin/env python3
"""
Test enemy detection with simulated unit data
"""

import os
import sys
from unittest.mock import Mock, patch
from env import ClashRoyaleEnv

def test_simulated_enemy_detection():
    """Test enemy detection with simulated enemy units"""
    print("🎯 Testing Enemy Detection with Simulated Units")
    print("=" * 60)
    
    # Initialize environment
    env = ClashRoyaleEnv()
    
    # Create mock Roboflow results with actual enemy units
    mock_results = [{
        'count_objects': 8,
        'output_image': 'mock_image.jpg',
        'predictions': {
            'predictions': [
                # Enemy units (upper area)
                {
                    'width': 50.0, 'height': 60.0, 'x': 150.0, 'y': 300.0,
                    'confidence': 0.85, 'class_id': 10, 'class': 'knight',
                    'detection_id': 'enemy-1', 'parent_id': 'image'
                },
                {
                    'width': 40.0, 'height': 45.0, 'x': 200.0, 'y': 250.0,
                    'confidence': 0.78, 'class_id': 11, 'class': 'archers',
                    'detection_id': 'enemy-2', 'parent_id': 'image'
                },
                {
                    'width': 35.0, 'height': 40.0, 'x': 100.0, 'y': 350.0,
                    'confidence': 0.72, 'class_id': 12, 'class': 'goblins',
                    'detection_id': 'enemy-3', 'parent_id': 'image'
                },
                # Ally units (lower area)
                {
                    'width': 50.0, 'height': 60.0, 'x': 180.0, 'y': 500.0,
                    'confidence': 0.88, 'class_id': 10, 'class': 'giant',
                    'detection_id': 'ally-1', 'parent_id': 'image'
                },
                {
                    'width': 30.0, 'height': 35.0, 'x': 250.0, 'y': 550.0,
                    'confidence': 0.75, 'class_id': 13, 'class': 'musketeer',
                    'detection_id': 'ally-2', 'parent_id': 'image'
                },
                # Towers (should be filtered out)
                {
                    'width': 83.0, 'height': 108.0, 'x': 62.5, 'y': 184.0,
                    'confidence': 0.97, 'class_id': 6, 'class': 'enemy princess tower',
                    'detection_id': 'tower-1', 'parent_id': 'image'
                },
                {
                    'width': 88.0, 'height': 96.0, 'x': 214.0, 'y': 671.0,
                    'confidence': 0.96, 'class_id': 1, 'class': 'ally king tower',
                    'detection_id': 'tower-2', 'parent_id': 'image'
                },
                # Low confidence unit (should be filtered out)
                {
                    'width': 25.0, 'height': 30.0, 'x': 120.0, 'y': 280.0,
                    'confidence': 0.25, 'class_id': 14, 'class': 'minions',
                    'detection_id': 'low-conf', 'parent_id': 'image'
                }
            ]
        }
    }]
    
    # Mock the Roboflow workflow call
    with patch.object(env.rf_model, 'run_workflow', return_value=mock_results):
        print("1. Testing with simulated enemy units...")
        enemy_cards = env.detect_enemy_cards()
        
        print(f"\n📊 Results:")
        print(f"   🎯 Enemy units detected: {len(enemy_cards)}")
        print(f"   🎯 Enemy units: {enemy_cards}")
        
        # Expected results:
        # - knight (y=300, enemy territory)
        # - archers (y=250, enemy territory) 
        # - goblins (y=350, enemy territory)
        # Should NOT include:
        # - giant (y=500, ally territory)
        # - musketeer (y=550, ally territory)
        # - towers (filtered out)
        # - minions (low confidence)
        
        expected_enemies = ['knight', 'archers', 'goblins']
        
        print(f"\n✅ Expected enemies: {expected_enemies}")
        print(f"✅ Actual enemies: {enemy_cards}")
        
        # Verify results
        success = True
        if len(enemy_cards) != len(expected_enemies):
            print(f"❌ Wrong number of enemies: expected {len(expected_enemies)}, got {len(enemy_cards)}")
            success = False
        
        for expected in expected_enemies:
            if expected not in enemy_cards:
                print(f"❌ Missing expected enemy: {expected}")
                success = False
        
        for detected in enemy_cards:
            if detected not in expected_enemies:
                print(f"❌ Unexpected enemy detected: {detected}")
                success = False
        
        if success:
            print("🎉 Enemy detection test PASSED!")
        else:
            print("❌ Enemy detection test FAILED!")
        
        return success

def test_edge_cases():
    """Test edge cases for enemy detection"""
    print("\n🔍 Testing Edge Cases")
    print("=" * 40)
    
    env = ClashRoyaleEnv()
    
    # Test 1: No units detected
    mock_empty = [{'count_objects': 0, 'predictions': {'predictions': []}}]
    with patch.object(env.rf_model, 'run_workflow', return_value=mock_empty):
        result = env.detect_enemy_cards()
        print(f"Empty battlefield: {result} (expected: [])")
        assert result == [], "Should return empty list for no units"
    
    # Test 2: Only towers
    mock_towers = [{
        'count_objects': 2,
        'predictions': {
            'predictions': [
                {'x': 100, 'y': 200, 'confidence': 0.9, 'class': 'enemy king tower'},
                {'x': 200, 'y': 600, 'confidence': 0.9, 'class': 'ally princess tower'}
            ]
        }
    }]
    with patch.object(env.rf_model, 'run_workflow', return_value=mock_towers):
        result = env.detect_enemy_cards()
        print(f"Only towers: {result} (expected: [])")
        assert result == [], "Should filter out towers"
    
    # Test 3: All units in ally territory
    mock_ally_only = [{
        'count_objects': 2,
        'predictions': {
            'predictions': [
                {'x': 100, 'y': 500, 'confidence': 0.8, 'class': 'knight'},
                {'x': 200, 'y': 600, 'confidence': 0.7, 'class': 'archers'}
            ]
        }
    }]
    with patch.object(env.rf_model, 'run_workflow', return_value=mock_ally_only):
        result = env.detect_enemy_cards()
        print(f"Ally territory only: {result} (expected: [])")
        assert result == [], "Should not detect allies as enemies"
    
    print("✅ All edge cases passed!")

if __name__ == "__main__":
    try:
        success1 = test_simulated_enemy_detection()
        test_edge_cases()
        
        if success1:
            print("\n🎉 All tests PASSED! Enemy detection is working correctly.")
        else:
            print("\n❌ Some tests FAILED. Check the output above.")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
