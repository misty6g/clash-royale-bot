#!/usr/bin/env python3
"""
Script to add stats from stats.txt to cards.json
"""

import json
import re
from typing import Dict, Optional, Union

def parse_stats_file(filename: str) -> Dict[str, Dict]:
    """
    Parse the stats.txt file and return a dictionary of card stats.
    
    Args:
        filename: Path to the stats.txt file
    
    Returns:
        Dictionary with card names as keys and stats as values
    """
    stats_data = {}
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Skip header line and process each card line
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith('Defensive Buildings') or line.startswith('Card') or line.startswith('Rarity'):
            continue
            
        # Split by tabs, but handle cases where there might be spaces
        parts = re.split(r'\t+', line)
        if len(parts) < 8:
            continue
            
        try:
            card_name = parts[0].strip()
            
            # Skip section headers
            if card_name in ['Defensive Buildings', 'Passive Buildings', 'Damaging Spells', 'Spawners']:
                continue
                
            # Parse elixir cost (handle ability costs like "5 (1)")
            elixir_cost_str = parts[1].strip()
            elixir_match = re.match(r'(\d+)', elixir_cost_str)
            elixir_cost = int(elixir_match.group(1)) if elixir_match else None
            
            # Parse hitpoints (handle shield notation like "1440 (1,200+240)")
            hitpoints_str = parts[2].strip()
            if hitpoints_str == 'N/A':
                hitpoints = None
            else:
                # Extract the main number, ignoring parenthetical additions
                hp_match = re.match(r'([\d,]+)', hitpoints_str.replace(',', ''))
                hitpoints = int(hp_match.group(1)) if hp_match else None
            
            # Parse damage (handle multiple damage values like "115 (x2)")
            damage_str = parts[3].strip()
            if damage_str == 'N/A':
                damage = None
            else:
                # Extract the main damage number
                damage_match = re.match(r'(\d+)', damage_str)
                damage = int(damage_match.group(1)) if damage_match else None
            
            # Parse hit speed
            hit_speed_str = parts[4].strip()
            if hit_speed_str == 'N/A':
                hit_speed = None
            else:
                hit_speed_match = re.match(r'([\d.]+)', hit_speed_str)
                hit_speed = float(hit_speed_match.group(1)) if hit_speed_match else None
            
            # Parse damage per second
            dps_str = parts[5].strip()
            if dps_str == 'N/A':
                damage_per_second = None
            else:
                dps_match = re.match(r'(\d+)', dps_str)
                damage_per_second = int(dps_match.group(1)) if dps_match else None
            
            # Parse special damage (optional)
            special_damage = parts[6].strip() if len(parts) > 6 and parts[6].strip() != 'N/A' else None
            
            # Parse range
            range_str = parts[7].strip() if len(parts) > 7 else None
            
            # Parse count
            count_str = parts[8].strip() if len(parts) > 8 else "1"
            count_match = re.match(r'(\d+)', count_str)
            count = int(count_match.group(1)) if count_match else 1
            
            # Store the stats
            stats_data[card_name] = {
                'hitpoints': hitpoints,
                'damage': damage,
                'hit_speed': hit_speed,
                'damage_per_second': damage_per_second,
                'range': range_str,
                'count': count
            }
            
            # Add special damage if it exists
            if special_damage:
                stats_data[card_name]['special_damage'] = special_damage
                
        except (ValueError, IndexError) as e:
            print(f"Error parsing line: {line}")
            print(f"Error: {e}")
            continue
    
    return stats_data

def add_stats_to_cards():
    """
    Main function to add stats from stats.txt to cards.json
    """
    # Parse the stats file
    print("Parsing stats.txt...")
    stats_data = parse_stats_file('stats.txt')
    print(f"Found stats for {len(stats_data)} cards")
    
    # Load existing cards.json
    try:
        with open('cards.json', 'r') as f:
            cards_data = json.load(f)
    except FileNotFoundError:
        print("Error: cards.json not found")
        return
    
    # Add stats to each card
    updated_count = 0
    for card_name, card_info in cards_data.items():
        if card_name in stats_data:
            # Add the stats to the card
            stats = stats_data[card_name]
            for stat_key, stat_value in stats.items():
                if stat_value is not None:  # Only add non-null values
                    card_info[stat_key] = stat_value
            updated_count += 1
            print(f"Updated {card_name} with stats")
        else:
            print(f"No stats found for {card_name}")
    
    # Save the updated cards.json
    with open('cards.json', 'w') as f:
        json.dump(cards_data, f, indent=2)
    
    print(f"Successfully updated {updated_count} cards with stats")
    print("Updated cards.json saved")

if __name__ == "__main__":
    add_stats_to_cards()
