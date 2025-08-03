#!/usr/bin/env python3
"""
Simple test script to debug detection issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env import ClashRoyaleEnv

def test_hand_detection():
    """Test hand detection"""
    print("=== Testing Hand Detection ===")
    env = ClashRoyaleEnv()
    
    try:
        cards = env.detect_cards_in_hand()
        print(f"✅ Hand detection result: {cards}")
        return True
    except Exception as e:
        print(f"❌ Hand detection failed: {e}")
        return False

def test_enemy_detection():
    """Test enemy detection with detailed debugging"""
    print("\n=== Testing Enemy Detection ===")
    env = ClashRoyaleEnv()
    
    try:
        # Test the Roboflow call directly
        screenshot_path = env.screenshot_path
        print(f"📸 Using screenshot: {screenshot_path}")
        
        results = env.rf_model.run_workflow(
            workspace_name="clash-royale-tgua7",
            workflow_id="detect-count-and-visualize",
            images={"image": screenshot_path}
        )
        
        print(f"🔍 Raw results type: {type(results)}")
        print(f"🔍 Raw results: {results}")
        
        # Now test the parsing
        enemies = env.detect_enemy_cards()
        print(f"✅ Enemy detection result: {enemies}")
        return True
        
    except Exception as e:
        print(f"❌ Enemy detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Detection Fixes...")
    
    hand_ok = test_hand_detection()
    enemy_ok = test_enemy_detection()
    
    print(f"\n📊 Results:")
    print(f"Hand Detection: {'✅ FIXED' if hand_ok else '❌ BROKEN'}")
    print(f"Enemy Detection: {'✅ FIXED' if enemy_ok else '❌ BROKEN'}")
    
    if hand_ok and enemy_ok:
        print("🎉 All detection systems are working!")
    else:
        print("⚠️ Some detection systems need more work")
