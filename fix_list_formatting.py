#!/usr/bin/env python3
"""
Script to fix the formatting of lists in cards.json to be on one line instead of multiple lines.
"""

import json

def fix_list_formatting():
    """
    Load cards.json, reformat lists to be on one line, and save it back.
    """
    # Load the cards.json file
    try:
        with open('cards.json', 'r') as f:
            cards_data = json.load(f)
    except FileNotFoundError:
        print("Error: cards.json not found")
        return

    print(f"Loaded {len(cards_data)} cards from cards.json")

    # Custom JSON encoder to format lists on single lines
    def format_card_json(card_data, indent=2):
        lines = []
        lines.append("{")

        items = list(card_data.items())
        for i, (key, value) in enumerate(items):
            is_last = i == len(items) - 1
            comma = "" if is_last else ","

            if isinstance(value, list) and key in ['counters', 'countered_by', 'synergies']:
                # Format list on single line
                list_str = "[" + ", ".join(f'"{item}"' for item in value) + "]"
                lines.append(f'  "{key}": {list_str}{comma}')
            elif isinstance(value, str):
                lines.append(f'  "{key}": "{value}"{comma}')
            elif isinstance(value, (int, float)):
                lines.append(f'  "{key}": {value}{comma}')
            elif isinstance(value, bool):
                lines.append(f'  "{key}": {str(value).lower()}{comma}')
            elif isinstance(value, list):
                # Other lists (not the main three) - keep normal formatting
                list_items = ", ".join(f'"{item}"' if isinstance(item, str) else str(item) for item in value)
                lines.append(f'  "{key}": [{list_items}]{comma}')
            else:
                lines.append(f'  "{key}": {json.dumps(value)}{comma}')

        lines.append("}")
        return "\n".join(lines)

    # Format the entire JSON
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
                # Format list on single line
                list_str = "[" + ", ".join(f'"{item}"' for item in value) + "]"
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

    print("Successfully reformatted cards.json with single-line lists")

if __name__ == "__main__":
    fix_list_formatting()
