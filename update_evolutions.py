#!/usr/bin/env python3
import json

def update_evolution_values():
    # Read the evos.txt file to get the evolution mappings
    evolution_mappings = {}
    
    with open('evos.txt', 'r') as f:
        lines = f.readlines()
        
    # Skip the header line and process the rest
    for line in lines[1:]:
        line = line.strip()
        if line and '\t' in line:
            parts = line.split('\t')
            if len(parts) >= 2:
                card_name = parts[0].strip()
                try:
                    evolution_value = int(parts[1].strip())
                    evolution_mappings[card_name] = evolution_value
                except ValueError:
                    print(f"Warning: Could not parse evolution value for {card_name}: {parts[1]}")
    
    print(f"Found {len(evolution_mappings)} cards with evolution values to update:")
    for card, evo in evolution_mappings.items():
        print(f"  {card}: {evo}")
    
    # Read the cards.json file
    with open('cards.json', 'r') as f:
        cards_data = json.load(f)
    
    # Update evolution values
    updated_count = 0
    not_found = []
    
    for card_name, new_evolution in evolution_mappings.items():
        if card_name in cards_data:
            old_evolution = cards_data[card_name].get('evolution', 'N/A')
            cards_data[card_name]['evolution'] = new_evolution
            print(f"Updated {card_name}: {old_evolution} -> {new_evolution}")
            updated_count += 1
        else:
            not_found.append(card_name)
            print(f"Warning: Card '{card_name}' not found in cards.json")
    
    # Write the updated data back to cards.json
    with open('cards.json', 'w') as f:
        json.dump(cards_data, f, indent=2)
    
    # Apply the same formatting fix as before to keep arrays compact
    with open('cards.json', 'r') as f:
        content = f.read()
    
    # Replace multi-line arrays with single-line arrays
    import re
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
    
    print(f"\nSummary:")
    print(f"  Successfully updated: {updated_count} cards")
    if not_found:
        print(f"  Cards not found: {len(not_found)}")
        for card in not_found:
            print(f"    - {card}")
    
    print(f"\nEvolution values have been updated and JSON formatting preserved!")

if __name__ == "__main__":
    update_evolution_values()
