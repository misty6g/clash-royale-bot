#!/usr/bin/env python3
"""
Test battlefield detection to understand what's happening
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env import ClashRoyaleEnv
import json

def test_battlefield_detection():
    """Test what's actually happening with battlefield detection"""
    print("🔍 Testing Battlefield Detection")
    
    env = ClashRoyaleEnv()
    
    # Take a screenshot first
    print("\n📸 Taking screenshot...")
    env.actions.capture_area(env.screenshot_path)
    print(f"Screenshot saved to: {env.screenshot_path}")
    
    # Test the current workflow
    print("\n🔍 Testing current workflow...")
    try:
        results = env.rf_model.run_workflow(
            workspace_name="clash-royale-tgua7",
            workflow_id="detect-count-and-visualize",
            images={"image": env.screenshot_path}
        )
        
        print(f"Workflow results type: {type(results)}")
        print(f"Workflow results: {results}")
        
        # Save full results for analysis
        with open("battlefield_detection_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("✅ Results saved to battlefield_detection_results.json")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
    
    # Test direct inference with specific model
    print("\n🔍 Testing direct inference with specific model...")
    try:
        # Try with a specific model ID for battlefield detection
        results = env.rf_model.infer(
            env.screenshot_path,
            model_id="clash-royale-tgua7/1"  # Try with version 1
        )
        print(f"Direct inference type: {type(results)}")

        if hasattr(results, 'predictions'):
            print(f"Predictions found: {len(results.predictions)}")
            for i, pred in enumerate(results.predictions):
                if hasattr(pred, 'class_name'):
                    print(f"  Prediction {i}: {pred.class_name} (confidence: {pred.confidence:.2f}) at ({pred.x}, {pred.y})")
                else:
                    print(f"  Prediction {i}: {pred}")
        else:
            print(f"No predictions attribute found")
            print(f"Results: {results}")

    except Exception as e:
        print(f"❌ Direct inference failed: {e}")

    # Test with different model versions
    print("\n🔍 Testing different model versions...")
    for version in [1, 2, 3, 4, 5]:
        try:
            results = env.rf_model.infer(
                env.screenshot_path,
                model_id=f"clash-royale-tgua7/{version}"
            )
            if hasattr(results, 'predictions') and len(results.predictions) > 0:
                print(f"✅ Model version {version} found {len(results.predictions)} predictions")
                for pred in results.predictions[:3]:  # Show first 3
                    if hasattr(pred, 'class_name'):
                        print(f"    {pred.class_name} (confidence: {pred.confidence:.2f})")
            else:
                print(f"❌ Model version {version}: no predictions")
        except Exception as e:
            print(f"❌ Model version {version} failed: {e}")
    
    # Test with different workspace/model
    print("\n🔍 Testing different approaches...")
    
    # Try to list available models
    try:
        # Check if there are any local models we can use
        models_dir = "models"
        if os.path.exists(models_dir):
            model_files = [f for f in os.listdir(models_dir) if f.endswith('.pth')]
            print(f"Found {len(model_files)} local model files")
            if model_files:
                print(f"Latest model: {sorted(model_files)[-1]}")
    except Exception as e:
        print(f"Error checking local models: {e}")
    
    # Test enhanced vision system
    print("\n🔍 Testing enhanced vision system...")
    if hasattr(env, 'enhanced_vision') and env.enhanced_vision:
        try:
            units = env.enhanced_vision.detect_units_on_field()
            print(f"Enhanced vision detected {len(units)} units")
            for unit in units:
                print(f"  Unit: {unit}")
        except Exception as e:
            print(f"Enhanced vision failed: {e}")
    else:
        print("Enhanced vision not available")

    # Test enemy detection method
    print("\n🔍 Testing improved enemy detection method...")
    enemies = env.detect_enemy_cards()
    print(f"Enemy detection result: {enemies}")

    # Test with different confidence thresholds
    print("\n🔍 Testing with different confidence thresholds...")
    for threshold in [0.1, 0.2, 0.3, 0.4, 0.5]:
        print(f"\n--- Testing with confidence threshold: {threshold} ---")
        try:
            results = env.rf_model.run_workflow(
                workspace_name="clash-royale-tgua7",
                workflow_id="detect-count-and-visualize",
                images={"image": env.screenshot_path}
            )

            if isinstance(results, list) and results:
                main_result = results[0]
                count_objects = main_result.get('count_objects', 0)
                print(f"Objects detected: {count_objects}")

                # Look for any predictions with lower thresholds
                predictions = []
                for key in ['predictions', 'detections', 'objects', 'results']:
                    if key in main_result:
                        predictions = main_result[key]
                        break

                filtered_predictions = []
                for pred in predictions:
                    if isinstance(pred, dict):
                        confidence = pred.get('confidence', 0)
                        if confidence > threshold:
                            filtered_predictions.append(pred)
                            print(f"  Found: {pred.get('class', 'Unknown')} (confidence: {confidence:.2f})")

                print(f"Total predictions above {threshold}: {len(filtered_predictions)}")

        except Exception as e:
            print(f"Error testing threshold {threshold}: {e}")

if __name__ == "__main__":
    test_battlefield_detection()
