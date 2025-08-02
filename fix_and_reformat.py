#!/usr/bin/env python3
"""
Script to fix the JSON file and reformat lists to be on one line.
"""

import re

def fix_and_reformat():
    """
    Fix the JSON file and reformat lists to be on one line.
    """
    # Read the file as text
    try:
        with open('cards.json', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: cards.json not found")
        return
    
    print("Fixing JSON syntax and reformatting lists...")
    
    # Fix Python boolean values to JSON boolean values
    content = content.replace(': True', ': true')
    content = content.replace(': False', ': false')
    content = content.replace(': None', ': null')
    
    # Now try to parse and reformat
    import json
    try:
        cards_data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON is still corrupted: {e}")
        return
    
    print(f"Successfully loaded {len(cards_data)} cards")
    
    # Now reformat with proper single-line lists
    output_lines = ["{"]
    card_items = list(cards_data.items())
    
    for i, (card_name, card_data) in enumerate(card_items):
        is_last_card = i == len(card_items) - 1
        comma = "" if is_last_card else ","
        
        output_lines.append(f'  "{card_name}": {{')
        
        # Format each property of the card
        properties = list(card_data.items())
        for j, (key, value) in enumerate(properties):
            is_last_prop = j == len(properties) - 1
            prop_comma = "" if is_last_prop else ","
            
            if isinstance(value, list) and key in ['counters', 'countered_by', 'synergies']:
                # Flatten nested lists if they exist
                if value and isinstance(value[0], list):
                    value = value[0]  # Take the first (and should be only) nested list
                elif value and isinstance(value[0], str) and value[0].startswith('['):
                    # Handle string representations of lists
                    try:
                        import ast
                        value = ast.literal_eval(value[0])
                    except:
                        pass
                
                # Format list on single line
                if value:
                    list_str = "[" + ", ".join(f'"{item}"' for item in value) + "]"
                else:
                    list_str = "[]"
                output_lines.append(f'    "{key}": {list_str}{prop_comma}')
            elif isinstance(value, str):
                output_lines.append(f'    "{key}": "{value}"{prop_comma}')
            elif isinstance(value, (int, float)):
                output_lines.append(f'    "{key}": {value}{prop_comma}')
            elif isinstance(value, bool):
                output_lines.append(f'    "{key}": {str(value).lower()}{prop_comma}')
            elif value is None:
                output_lines.append(f'    "{key}": null{prop_comma}')
            else:
                output_lines.append(f'    "{key}": {json.dumps(value)}{prop_comma}')
        
        output_lines.append(f'  }}{comma}')
    
    output_lines.append("}")
    
    # Write back to file
    with open('cards.json', 'w') as f:
        f.write("\n".join(output_lines))
    
    print("Successfully fixed and reformatted cards.json with single-line lists")

if __name__ == "__main__":
    fix_and_reformat()
