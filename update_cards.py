#!/usr/bin/env python3
import json

def update_cards():
    # Read the cards.json file
    with open('cards.json', 'r') as f:
        data = json.load(f)
    
    # Add missing fields to all cards
    for card_name, card_data in data.items():
        # Add elixir_cost if missing
        if 'elixir_cost' not in card_data:
            # Set default elixir costs based on card type and subtype
            if card_data.get('type') == 'spell':
                if 'Rocket' in card_name or 'Lightning' in card_name:
                    card_data['elixir_cost'] = 6
                elif 'Fireball' in card_name or 'Poison' in card_name:
                    card_data['elixir_cost'] = 4
                elif 'Freeze' in card_name or 'Tornado' in card_name:
                    card_data['elixir_cost'] = 4
                elif 'Mirror' in card_name:
                    card_data['elixir_cost'] = 1
                elif 'Clone' in card_name or 'Rage' in card_name:
                    card_data['elixir_cost'] = 3
                else:
                    card_data['elixir_cost'] = 2  # Default for most spells
            elif card_data.get('type') == 'building':
                if 'X-Bow' in card_name:
                    card_data['elixir_cost'] = 6
                elif 'Mortar' in card_name:
                    card_data['elixir_cost'] = 4
                elif 'Inferno Tower' in card_name or 'Bomb Tower' in card_name:
                    card_data['elixir_cost'] = 5
                elif 'Tesla' in card_name or 'Cannon' in card_name:
                    card_data['elixir_cost'] = 4
                elif 'Tombstone' in card_name:
                    card_data['elixir_cost'] = 3
                elif 'Furnace' in card_name or 'Goblin Hut' in card_name or 'Barbarian Hut' in card_name:
                    card_data['elixir_cost'] = 5
                else:
                    card_data['elixir_cost'] = 4  # Default for buildings
            elif card_data.get('type') == 'troop':
                if card_data.get('subtype') == 'big_tank':
                    card_data['elixir_cost'] = 8
                elif card_data.get('subtype') == 'tank':
                    card_data['elixir_cost'] = 5
                elif card_data.get('subtype') == 'mini_tank':
                    card_data['elixir_cost'] = 3
                elif card_data.get('subtype') == 'swarm':
                    card_data['elixir_cost'] = 2
                elif card_data.get('subtype') == 'spirit':
                    card_data['elixir_cost'] = 1
                elif card_data.get('subtype') == 'champion':
                    if 'Little Prince' in card_name:
                        card_data['elixir_cost'] = 3
                    else:
                        card_data['elixir_cost'] = 4
                else:
                    card_data['elixir_cost'] = 4  # Default for troops
        
        # Add evolution field if missing
        if 'evolution' not in card_data:
            card_data['evolution'] = 99
        
        # Add champion field if missing
        if 'champion' not in card_data:
            if card_data.get('subtype') == 'champion':
                card_data['champion'] = True
            else:
                card_data['champion'] = False
        
        # Add rarity if missing
        if 'rarity' not in card_data:
            if card_data.get('subtype') == 'champion':
                card_data['rarity'] = 'champion'
            elif card_name in ['Princess', 'Ice Wizard', 'Lumberjack', 'Sparky', 'Lava Hound', 'Miner', 'Inferno Dragon', 'Graveyard', 'The Log', 'Bandit', 'Night Witch', 'Electro Wizard', 'Mega Knight', 'Royal Ghost', 'Magic Archer', 'Fisherman', 'Ram Rider', 'Phoenix', 'Mother Witch', 'Goblin Machine', 'Spirit Empress']:
                card_data['rarity'] = 'legendary'
            elif card_name in ['Giant', 'Balloon', 'Witch', 'Skeleton Army', 'Baby Dragon', 'Prince', 'Dark Prince', 'P.E.K.K.A', 'Golem', 'X-Bow', 'Lightning', 'Poison', 'Freeze', 'Mirror', 'Tornado', 'Clone', 'Bowler', 'Executioner', 'Cannon Cart', 'Goblin Giant', 'Electro Dragon', 'Earthquake', 'Goblin Cage', 'Battle Healer', 'Elixir Golem', 'Firecracker', 'Royal Delivery', 'Skeleton Dragons', 'Electro Giant', 'Goblin Drill', 'Goblin Curse', 'Void', 'Rune Giant']:
                card_data['rarity'] = 'epic'
            elif card_name in ['Musketeer', 'Mini P.E.K.K.A', 'Valkyrie', 'Hog Rider', 'Wizard', 'Fireball', 'Rocket', 'Tombstone', 'Inferno Tower', 'Bomb Tower', 'Barbarian Hut', 'Goblin Hut', 'Furnace', 'Three Musketeers', 'Giant Skeleton', 'Rage', 'Dart Goblin', 'Flying Machine', 'Zappies', 'Hunter', 'Barbarian Barrel', 'Royal Recruits', 'Goblin Demolisher', 'Suspicious Bush', 'Elixir Collector']:
                card_data['rarity'] = 'rare'
            else:
                card_data['rarity'] = 'common'
    
    # Write the updated data back to the file
    with open('cards.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Successfully updated all cards with missing fields!")

if __name__ == "__main__":
    update_cards()
