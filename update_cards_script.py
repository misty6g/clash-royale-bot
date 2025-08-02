#!/usr/bin/env python3
"""
Script to automatically update cards.json with comprehensive data from Deck Shop Pro.
This script fetches card information from deckshop.pro and updates the cards.json file.
"""

import json
import requests
from bs4 import BeautifulSoup
import time
import re
from typing import Dict, List, Optional

def fetch_card_data(card_name: str) -> Optional[Dict]:
    """
    Fetch card data from Deck Shop Pro website.
    
    Args:
        card_name: Name of the card (URL-friendly format)
    
    Returns:
        Dictionary with card data or None if failed
    """
    # Convert card name to URL format (lowercase, replace spaces with hyphens)
    url_name = card_name.lower().replace(' ', '-').replace('.', '').replace("'", '')
    url = f"https://www.deckshop.pro/card/detail/{url_name}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic card info
        card_data = {}
        
        # Get elixir cost from the page
        elixir_sections = soup.find_all('h3', string=re.compile(r'.*\d+.*'))
        for section in elixir_sections:
            if 'elixir' in section.get_text().lower():
                cost_match = re.search(r'\d+', section.get_text())
                if cost_match:
                    card_data['elixir_cost'] = int(cost_match.group())
                    break
        
        # Extract rarity from the page
        rarity_text = soup.find('p', string=re.compile(r'(Common|Rare|Epic|Legendary|Champion)'))
        if rarity_text:
            rarity = rarity_text.get_text().split('·')[0].strip().lower()
            card_data['rarity'] = rarity
        
        # Extract counters, countered_by, and synergies
        card_data['counters'] = extract_card_list(soup, 'can counter these')
        card_data['countered_by'] = extract_card_list(soup, 'Counters to')
        card_data['synergies'] = extract_card_list(soup, 'synergies')
        
        return card_data
        
    except Exception as e:
        print(f"Error fetching data for {card_name}: {e}")
        return None

def extract_card_list(soup: BeautifulSoup, section_keyword: str) -> List[str]:
    """Extract list of card names from a specific section."""
    cards = []
    
    # Find sections containing the keyword
    sections = soup.find_all('h4', string=re.compile(section_keyword, re.IGNORECASE))
    
    for section in sections:
        # Find the next div or section containing card images
        next_div = section.find_next_sibling()
        if next_div:
            # Extract card names from img alt attributes or links
            card_links = next_div.find_all('a', href=re.compile(r'/card/detail/'))
            for link in card_links:
                img = link.find('img')
                if img and img.get('alt'):
                    card_name = img['alt'].strip()
                    if card_name and card_name not in cards:
                        cards.append(card_name)
    
    return cards

def get_card_properties(card_name: str) -> Dict:
    """
    Determine card properties based on name and common patterns.
    This is a fallback for when web scraping doesn't capture everything.
    """
    properties = {
        'type': 'troop',  # Default
        'subtype': 'ground',  # Default
        'damage_type': 'melee',  # Default
        'target': 'ground',  # Default
        'speed': 'medium',  # Default
        'danger_level': 5,  # Default
        'defensive_value': 5,  # Default
        'offensive_value': 5,  # Default
        'optimal_placement': 'anywhere'  # Default
    }
    
    name_lower = card_name.lower()
    
    # Determine type
    if any(spell in name_lower for spell in ['fireball', 'zap', 'arrows', 'lightning', 'rocket', 'freeze', 'rage', 'clone', 'mirror', 'tornado', 'poison', 'heal', 'earthquake', 'snowball', 'log', 'barbarian barrel', 'graveyard']):
        properties['type'] = 'spell'
        properties['speed'] = 'instant'
        properties['optimal_placement'] = 'targeted'
    elif any(building in name_lower for building in ['tower', 'cannon', 'tesla', 'mortar', 'x-bow', 'hut', 'furnace', 'collector', 'tombstone', 'cage', 'drill']):
        properties['type'] = 'building'
        properties['speed'] = 'stationary'
        properties['optimal_placement'] = 'defensive_center'
    
    # Determine subtype for troops
    if properties['type'] == 'troop':
        if any(air in name_lower for air in ['dragon', 'balloon', 'minion', 'bat', 'lava', 'phoenix']):
            properties['subtype'] = 'air'
            properties['target'] = 'air_and_ground'
        elif any(tank in name_lower for tank in ['giant', 'golem', 'pekka', 'mega knight', 'lava hound']):
            properties['subtype'] = 'big_tank'
            properties['speed'] = 'slow'
            properties['optimal_placement'] = 'back_push'
        elif any(mini_tank in name_lower for mini_tank in ['knight', 'valkyrie', 'mini pekka', 'dark prince']):
            properties['subtype'] = 'mini_tank'
        elif any(ranged in name_lower for ranged in ['archer', 'musketeer', 'wizard', 'witch', 'princess', 'dart goblin', 'magic archer']):
            properties['subtype'] = 'ranged'
            properties['damage_type'] = 'projectile'
            properties['target'] = 'air_and_ground'
            properties['optimal_placement'] = 'defensive_support'
    
    return properties

def update_cards_json():
    """Main function to update the cards.json file."""

    # Load existing cards.json
    try:
        with open('cards.json', 'r') as f:
            cards_data = json.load(f)
    except FileNotFoundError:
        cards_data = {}

    # List of remaining cards to process (excluding already updated ones)
    remaining_cards = [
        # Finish existing cards first
        "Musketeer", "Zap", "Cannon",

        # Common cards (not yet in file)
        "Skeletons", "Electro Spirit", "Fire Spirit", "Ice Spirit", "Goblins",
        "Spear Goblins", "Bomber", "Bats", "Giant Snowball", "Berserker",
        "Arrows", "Goblin Gang", "Skeleton Barrel", "Firecracker", "Royal Delivery",
        "Skeleton Dragons", "Mortar", "Tesla", "Barbarians", "Minion Horde",
        "Rascals", "Royal Giant", "Elite Barbarians", "Royal Recruits",

        # Rare cards
        "Heal Spirit", "Ice Golem", "Suspicious Bush", "Tombstone", "Mega Minion",
        "Dart Goblin", "Earthquake", "Elixir Golem", "Mini P.E.K.K.A",
        "Goblin Cage", "Goblin Hut", "Valkyrie", "Battle Ram",
        "Bomb Tower", "Flying Machine", "Hog Rider", "Battle Healer", "Furnace",
        "Zappies", "Goblin Demolisher", "Inferno Tower", "Wizard",
        "Royal Hogs", "Rocket", "Barbarian Hut", "Elixir Collector", "Three Musketeers",

        # Epic cards
        "Mirror", "Barbarian Barrel", "Wall Breakers", "Goblin Curse", "Rage",
        "Goblin Barrel", "Guards", "Skeleton Army", "Clone", "Tornado", "Void",
        "Baby Dragon", "Dark Prince", "Freeze", "Poison", "Rune Giant", "Hunter",
        "Goblin Drill", "Witch", "Balloon", "Prince", "Electro Dragon", "Bowler",
        "Executioner", "Cannon Cart", "Giant Skeleton", "Lightning", "Goblin Giant",
        "X-Bow", "P.E.K.K.A", "Electro Giant", "Golem",

        # Legendary cards
        "The Log", "Miner", "Princess", "Ice Wizard", "Royal Ghost", "Bandit",
        "Fisherman", "Electro Wizard", "Inferno Dragon", "Phoenix", "Magic Archer",
        "Lumberjack", "Night Witch", "Mother Witch", "Ram Rider", "Graveyard",
        "Goblin Machine", "Sparky", "Spirit Empress", "Mega Knight", "Lava Hound",

        # Champion cards
        "Little Prince", "Golden Knight", "Skeleton King", "Mighty Miner",
        "Archer Queen", "Goblinstein", "Monk", "Boss Bandit"
    ]

    print(f"Processing {len(remaining_cards)} remaining cards...")

    for i, card_name in enumerate(remaining_cards):
        print(f"Processing {i+1}/{len(remaining_cards)}: {card_name}")

        # Skip if card already exists and has comprehensive data
        if card_name in cards_data and len(cards_data[card_name].get('counters', [])) > 10:
            print(f"  Skipping {card_name} - already has comprehensive data")
            continue

        # Get base properties
        properties = get_card_properties(card_name)

        # For now, create basic entries with the properties
        # This ensures we have all cards in the file
        if card_name not in cards_data:
            cards_data[card_name] = {
                **properties,
                'counters': [],
                'countered_by': [],
                'synergies': []
            }
            print(f"  Added basic entry for {card_name}")

        # Add small delay
        time.sleep(0.1)

    # Save updated cards.json
    with open('cards.json', 'w') as f:
        json.dump(cards_data, f, indent=2)

    print(f"Successfully updated cards.json with {len(cards_data)} cards")

if __name__ == "__main__":
    update_cards_json()
