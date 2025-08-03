#!/usr/bin/env python3
"""
Test to examine the actual Roboflow workflow output structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env import ClashRoyaleEnv
import json

def test_workflow_output():
    """Test the raw workflow output to understand its structure"""
    print("🔍 Testing Roboflow Workflow Output Structure")
    
    env = ClashRoyaleEnv()
    
    try:
        # Call the workflow directly
        print("\n📞 Calling Roboflow workflow...")
        results = env.rf_model.run_workflow(
            workspace_name="clash-royale-tgua7",
            workflow_id="detect-count-and-visualize",
            images={"image": env.screenshot_path}
        )
        
        print(f"\n📊 Raw Results Analysis:")
        print(f"Type: {type(results)}")
        print(f"Content: {results}")
        
        if isinstance(results, dict):
            print(f"\n🔑 Dictionary Keys: {list(results.keys())}")
            for key, value in results.items():
                print(f"  {key}: {type(value)} = {value}")
                
        elif isinstance(results, list):
            print(f"\n📋 List Analysis:")
            print(f"Length: {len(results)}")
            for i, item in enumerate(results):
                print(f"  [{i}]: {type(item)} = {item}")
                
        # Save full results to file for analysis
        print(f"\n💾 Saving full results to file...")
        try:
            with open("workflow_output_full.json", "w") as f:
                json.dump(results, f, indent=2)
            print(f"✅ Saved full results to workflow_output_full.json")
        except Exception as e:
            print(f"❌ Error saving to file: {e}")

        # Try to access different possible result structures
        print(f"\n🔍 Trying Different Access Patterns:")

        # Pattern 1: Direct predictions
        if isinstance(results, dict) and 'predictions' in results:
            print(f"✅ Found 'predictions' key: {type(results['predictions'])}")
            if isinstance(results['predictions'], list):
                print(f"   Predictions list length: {len(results['predictions'])}")
                if results['predictions']:
                    print(f"   First prediction: {results['predictions'][0]}")

        # Pattern 2: Nested output
        if isinstance(results, dict) and 'output' in results:
            print(f"✅ Found 'output' key: {type(results['output'])}")

        # Pattern 3: Look for common detection keys
        if isinstance(results, dict):
            detection_keys = ['detections', 'results', 'data', 'inference', 'response']
            for key in detection_keys:
                if key in results:
                    print(f"✅ Found '{key}' key: {type(results[key])}")

        # Pattern 4: Check if it's a list with actual data
        if isinstance(results, list) and len(results) > 2:
            print(f"✅ List has {len(results)} items beyond ['image', 'predictions']")
            for i, item in enumerate(results[2:], 2):  # Skip first 2 items
                print(f"   [{i}]: {type(item)} = {str(item)[:100]}...")

        print(f"\n📄 Check workflow_output_full.json for complete structure")
            
    except Exception as e:
        print(f"❌ Error calling workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow_output()
