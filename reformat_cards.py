#!/usr/bin/env python3
"""
Script to reformat cards.json to put arrays on single lines instead of multi-line format.
"""

import json

def format_card_entry(card_name, card_data, indent=2):
    """Format a single card entry with single-line arrays."""
    spaces = ' ' * indent
    lines = []

    lines.append(f'{spaces}"{card_name}": {{')

    # Format each property
    for key, value in card_data.items():
        if isinstance(value, list):
            # Format arrays on single line
            if len(value) == 0:
                lines.append(f'{spaces}  "{key}": [],')
            else:
                formatted_items = ', '.join(f'"{item}"' for item in value)
                lines.append(f'{spaces}  "{key}": [{formatted_items}],')
        elif isinstance(value, str):
            lines.append(f'{spaces}  "{key}": "{value}",')
        else:
            lines.append(f'{spaces}  "{key}": {value},')

    # Remove trailing comma from last line
    if lines[-1].endswith(','):
        lines[-1] = lines[-1][:-1]

    lines.append(f'{spaces}}}')
    return lines

def reformat_cards_json():
    """Reformat the cards.json file to use single-line arrays."""

    # Load the current cards.json
    with open('cards.json', 'r') as f:
        cards_data = json.load(f)

    print(f"Loaded {len(cards_data)} cards from cards.json")

    # Format the entire file manually
    lines = ['{']

    card_names = list(cards_data.keys())
    for i, card_name in enumerate(card_names):
        card_lines = format_card_entry(card_name, cards_data[card_name])
        lines.extend(card_lines)

        # Add comma except for last card
        if i < len(card_names) - 1:
            lines[-1] += ','

    lines.append('}')

    # Write the formatted content
    with open('cards.json', 'w') as f:
        f.write('\n'.join(lines))

    print("Successfully reformatted cards.json with single-line arrays")

    # Show a sample of the new format
    print("\nSample of new format:")
    with open('cards.json', 'r') as f:
        lines_sample = f.readlines()
        for i, line in enumerate(lines_sample[:25]):
            print(f"{i+1:3d}: {line.rstrip()}")

if __name__ == "__main__":
    reformat_cards_json()
