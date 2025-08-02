#!/usr/bin/env python3
import json
import re

def fix_json_formatting():
    # Read the cards.json file
    with open('cards.json', 'r') as f:
        data = json.load(f)

    # Write the data back with normal formatting first
    with open('cards.json', 'w') as f:
        json.dump(data, f, indent=2)

    # Now read the file as text and fix array formatting
    with open('cards.json', 'r') as f:
        content = f.read()

    # Replace multi-line arrays with single-line arrays
    # This regex finds arrays that span multiple lines and compacts them
    def compact_array(match):
        array_content = match.group(1)
        # Remove newlines and extra spaces, keep only the values
        items = re.findall(r'"([^"]*)"', array_content)
        if items:
            return '[\n      ' + ', '.join(f'"{item}"' for item in items) + '\n    ]'
        return '[]'

    # Find and replace arrays (counters, countered_by, synergies)
    content = re.sub(r'\[\s*\n\s*(".*?"(?:\s*,\s*\n\s*".*?")*)\s*\n\s*\]', compact_array, content, flags=re.DOTALL)

    # Write the fixed content back
    with open('cards.json', 'w') as f:
        f.write(content)

    print("Successfully reformatted cards.json with compact arrays!")

if __name__ == "__main__":
    fix_json_formatting()
