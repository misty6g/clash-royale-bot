#!/usr/bin/env python3
"""
Debug script to isolate enemy detection issues
"""

import os
import traceback
import json
from env import ClashRoyaleEnv

def test_enemy_detection():
    """Test enemy detection in isolation"""
    print("🔍 Testing Enemy Detection System")
    print("=" * 50)
    
    try:
        # Initialize environment
        print("1. Initializing environment...")
        env = ClashRoyaleEnv()
        print(f"   ✅ Environment initialized")
        print(f"   📸 Screenshot path: {env.screenshot_path}")
        print(f"   🤖 Roboflow model: {env.rf_model is not None}")
        print(f"   🎯 Enhanced vision: {hasattr(env, 'enhanced_vision') and env.enhanced_vision is not None}")
        
        # Check if screenshot exists
        print("\n2. Checking screenshot...")
        if os.path.exists(env.screenshot_path):
            print(f"   ✅ Screenshot exists: {env.screenshot_path}")
            # Get file size
            size = os.path.getsize(env.screenshot_path)
            print(f"   📏 File size: {size} bytes")
        else:
            print(f"   ❌ Screenshot missing: {env.screenshot_path}")
            print("   📸 Taking new screenshot...")
            env.actions.capture_area(env.screenshot_path)
            if os.path.exists(env.screenshot_path):
                print(f"   ✅ Screenshot captured")
            else:
                print(f"   ❌ Failed to capture screenshot")
                return
        
        # Test Roboflow workflow directly
        print("\n3. Testing Roboflow workflow...")
        try:
            results = env.rf_model.run_workflow(
                workspace_name="clash-royale-tgua7",
                workflow_id="detect-count-and-visualize",
                images={"image": env.screenshot_path}
            )
            print(f"   ✅ Workflow executed successfully")
            print(f"   📊 Results type: {type(results)}")
            print(f"   📊 Results length: {len(results) if isinstance(results, list) else 'N/A'}")
            
            # Analyze results structure
            if isinstance(results, list) and results:
                first_result = results[0]
                print(f"   📊 First result type: {type(first_result)}")
                if isinstance(first_result, dict):
                    print(f"   📊 First result keys: {list(first_result.keys())}")
                    
                    # Look for predictions
                    if 'predictions' in first_result:
                        predictions = first_result['predictions']
                        print(f"   🎯 Predictions type: {type(predictions)}")
                        if isinstance(predictions, dict) and 'predictions' in predictions:
                            actual_predictions = predictions['predictions']
                            print(f"   🎯 Actual predictions count: {len(actual_predictions) if isinstance(actual_predictions, list) else 'N/A'}")
                            
                            # Show first few predictions
                            if isinstance(actual_predictions, list):
                                for i, pred in enumerate(actual_predictions[:3]):
                                    print(f"   🎯 Prediction {i}: {type(pred)} - {pred}")
                        else:
                            print(f"   🎯 Predictions content: {predictions}")
                            
        except Exception as workflow_error:
            print(f"   ❌ Workflow failed: {workflow_error}")
            traceback.print_exc()
        
        # Test enhanced vision detection
        print("\n4. Testing enhanced vision detection...")
        if hasattr(env, 'enhanced_vision') and env.enhanced_vision:
            try:
                units = env.enhanced_vision.detect_units_on_field()
                print(f"   ✅ Enhanced vision executed")
                print(f"   🎯 Units detected: {len(units)}")
                for i, unit in enumerate(units):
                    print(f"   🎯 Unit {i}: {unit}")
            except Exception as vision_error:
                print(f"   ❌ Enhanced vision failed: {vision_error}")
                traceback.print_exc()
        else:
            print("   ⚠️  Enhanced vision not available")
        
        # Test main enemy detection function
        print("\n5. Testing main enemy detection function...")
        try:
            enemy_cards = env.detect_enemy_cards()
            print(f"   ✅ Enemy detection executed")
            print(f"   🎯 Enemy cards detected: {enemy_cards}")
            print(f"   🎯 Number of enemies: {len(enemy_cards)}")
        except Exception as detection_error:
            print(f"   ❌ Enemy detection failed: {detection_error}")
            traceback.print_exc()
        
        # Check debug files
        print("\n6. Checking debug files...")
        debug_files = [
            "screenshots/debug_field.png",
            "screenshots/debug_cards.png",
            "screenshots/current.png"
        ]
        
        for debug_file in debug_files:
            if os.path.exists(debug_file):
                size = os.path.getsize(debug_file)
                print(f"   ✅ {debug_file} exists ({size} bytes)")
            else:
                print(f"   ❌ {debug_file} missing")
        
        print("\n" + "=" * 50)
        print("🎯 Enemy Detection Test Complete")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_enemy_detection()
