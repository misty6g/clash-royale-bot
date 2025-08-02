#!/usr/bin/env python3
"""
Script to enhance the existing cards.json with additional strategic data
"""

import json
import os
from card_database_manager import CardDatabaseManager

def add_strategic_enhancements():
    """Add strategic enhancements to specific cards"""
    
    strategic_data = {
        "Knight": {
            "synergy_tags": ["tank", "defensive", "cycle", "versatile"],
            "anti_synergy_tags": [],
            "early_game_value": 8,
            "mid_game_value": 7,
            "late_game_value": 6,
            "overtime_value": 7,
            "deploy_time": 0.8,
            "area_damage": False,
            "movement_speed": 1.0,
            "skill_cap": 3,
            "versatility": 9,
            "meta_tier": "A"
        },
        "Archers": {
            "synergy_tags": ["ranged", "defensive", "cycle", "air_defense"],
            "anti_synergy_tags": ["spell_vulnerable"],
            "early_game_value": 7,
            "mid_game_value": 6,
            "late_game_value": 5,
            "overtime_value": 6,
            "deploy_time": 0.8,
            "area_damage": False,
            "movement_speed": 1.0,
            "skill_cap": 4,
            "versatility": 7,
            "meta_tier": "B"
        },
        "Giant": {
            "synergy_tags": ["tank", "beatdown", "offensive", "heavy_cost"],
            "anti_synergy_tags": ["heavy_cost", "cycle"],
            "early_game_value": 4,
            "mid_game_value": 8,
            "late_game_value": 9,
            "overtime_value": 8,
            "deploy_time": 1.0,
            "area_damage": False,
            "movement_speed": 0.6,
            "skill_cap": 5,
            "versatility": 6,
            "meta_tier": "A"
        },
        "Fireball": {
            "synergy_tags": ["spell", "spell_damage", "area_damage", "versatile"],
            "anti_synergy_tags": [],
            "early_game_value": 6,
            "mid_game_value": 8,
            "late_game_value": 9,
            "overtime_value": 9,
            "deploy_time": 0.5,
            "area_damage": True,
            "splash_radius": 2.5,
            "skill_cap": 6,
            "versatility": 8,
            "meta_tier": "S"
        },
        "Hog Rider": {
            "synergy_tags": ["offensive", "cycle", "building_targeting", "fast"],
            "anti_synergy_tags": ["heavy_cost"],
            "early_game_value": 8,
            "mid_game_value": 8,
            "late_game_value": 7,
            "overtime_value": 9,
            "deploy_time": 0.8,
            "area_damage": False,
            "movement_speed": 1.4,
            "skill_cap": 6,
            "versatility": 7,
            "meta_tier": "A"
        },
        "Wizard": {
            "synergy_tags": ["ranged", "area_damage", "air_defense", "support"],
            "anti_synergy_tags": ["spell_vulnerable", "heavy_cost"],
            "early_game_value": 6,
            "mid_game_value": 7,
            "late_game_value": 8,
            "overtime_value": 7,
            "deploy_time": 0.8,
            "area_damage": True,
            "splash_radius": 1.5,
            "skill_cap": 5,
            "versatility": 8,
            "meta_tier": "B"
        },
        "P.E.K.K.A": {
            "synergy_tags": ["tank", "beatdown", "heavy_damage", "heavy_cost"],
            "anti_synergy_tags": ["heavy_cost", "cycle", "swarm_vulnerable"],
            "early_game_value": 3,
            "mid_game_value": 7,
            "late_game_value": 9,
            "overtime_value": 8,
            "deploy_time": 1.0,
            "area_damage": False,
            "movement_speed": 0.6,
            "skill_cap": 7,
            "versatility": 5,
            "meta_tier": "A"
        },
        "Minions": {
            "synergy_tags": ["air", "swarm", "cycle", "versatile"],
            "anti_synergy_tags": ["spell_vulnerable"],
            "early_game_value": 7,
            "mid_game_value": 6,
            "late_game_value": 5,
            "overtime_value": 6,
            "deploy_time": 0.8,
            "area_damage": False,
            "movement_speed": 1.4,
            "skill_cap": 4,
            "versatility": 8,
            "meta_tier": "B"
        },
        "Balloon": {
            "synergy_tags": ["air", "building_targeting", "heavy_damage", "offensive"],
            "anti_synergy_tags": ["air_defense_vulnerable"],
            "early_game_value": 5,
            "mid_game_value": 8,
            "late_game_value": 9,
            "overtime_value": 10,
            "deploy_time": 0.8,
            "area_damage": True,
            "splash_radius": 1.5,
            "skill_cap": 8,
            "versatility": 6,
            "meta_tier": "A"
        },
        "Skeleton Army": {
            "synergy_tags": ["swarm", "defensive", "cycle", "distraction"],
            "anti_synergy_tags": ["spell_vulnerable", "area_damage_vulnerable"],
            "early_game_value": 8,
            "mid_game_value": 6,
            "late_game_value": 5,
            "overtime_value": 7,
            "deploy_time": 0.8,
            "area_damage": False,
            "movement_speed": 1.4,
            "skill_cap": 5,
            "versatility": 6,
            "meta_tier": "B"
        }
    }
    
    return strategic_data

def enhance_cards_json():
    """Enhance the existing cards.json file"""
    
    # Load existing cards
    with open('cards.json', 'r') as f:
        cards_data = json.load(f)
    
    # Get strategic enhancements
    strategic_data = add_strategic_enhancements()
    
    # Apply enhancements
    enhanced_count = 0
    for card_name, enhancements in strategic_data.items():
        if card_name in cards_data:
            # Add new fields
            for key, value in enhancements.items():
                cards_data[card_name][key] = value
            enhanced_count += 1
            print(f"Enhanced {card_name}")
    
    # Add meta information to all cards
    for card_name, card_data in cards_data.items():
        # Add default values if not present
        if 'meta_tier' not in card_data:
            card_data['meta_tier'] = estimate_meta_tier(card_data)
        
        if 'versatility' not in card_data:
            card_data['versatility'] = estimate_versatility(card_data)
        
        if 'skill_cap' not in card_data:
            card_data['skill_cap'] = estimate_skill_cap(card_name, card_data)
        
        # Add synergy tags if not present
        if 'synergy_tags' not in card_data:
            card_data['synergy_tags'] = generate_basic_synergy_tags(card_data)
        
        if 'anti_synergy_tags' not in card_data:
            card_data['anti_synergy_tags'] = generate_basic_anti_synergy_tags(card_data)
        
        # Add game phase values if not present
        for phase in ['early_game_value', 'mid_game_value', 'late_game_value', 'overtime_value']:
            if phase not in card_data:
                card_data[phase] = 5  # Default neutral value
        
        # Add technical stats if not present
        if 'deploy_time' not in card_data:
            card_data['deploy_time'] = estimate_deploy_time(card_data.get('type', 'troop'))
        
        if 'area_damage' not in card_data:
            card_data['area_damage'] = has_area_damage(card_name)
        
        if 'movement_speed' not in card_data:
            card_data['movement_speed'] = estimate_movement_speed(card_data.get('speed', 'medium'))
    
    # Save enhanced cards
    with open('cards_enhanced.json', 'w') as f:
        json.dump(cards_data, f, indent=2)
    
    print(f"\nEnhanced {enhanced_count} cards with detailed strategic data")
    print(f"Enhanced database saved to cards_enhanced.json")
    print(f"Total cards in database: {len(cards_data)}")

def estimate_meta_tier(card_data):
    """Estimate meta tier based on card stats"""
    defensive = card_data.get('defensive_value', 5)
    offensive = card_data.get('offensive_value', 5)
    cost = card_data.get('elixir_cost', 5)
    
    # Simple scoring system
    score = (defensive + offensive) / 2
    
    # Adjust for cost efficiency
    if cost <= 3 and score >= 6:
        score += 1
    elif cost >= 6 and score < 7:
        score -= 1
    
    if score >= 8:
        return 'S'
    elif score >= 7:
        return 'A'
    elif score >= 5:
        return 'B'
    elif score >= 3:
        return 'C'
    else:
        return 'D'

def estimate_versatility(card_data):
    """Estimate versatility score"""
    defensive = card_data.get('defensive_value', 5)
    offensive = card_data.get('offensive_value', 5)
    
    # More versatile if balanced between offense and defense
    balance = 10 - abs(defensive - offensive)
    
    # Bonus for reasonable cost
    cost = card_data.get('elixir_cost', 5)
    cost_bonus = 2 if 2 <= cost <= 5 else 0
    
    return min(10, max(1, balance + cost_bonus))

def estimate_skill_cap(card_name, card_data):
    """Estimate skill requirement"""
    high_skill = ['X-Bow', 'Mortar', 'Miner', 'Graveyard', 'Balloon', 'Lava Hound', 'Sparky']
    medium_skill = ['Hog Rider', 'Giant', 'Golem', 'P.E.K.K.A', 'Royal Giant']
    
    if card_name in high_skill:
        return 8
    elif card_name in medium_skill:
        return 6
    elif card_data.get('type') == 'spell':
        return 7
    else:
        return 5

def generate_basic_synergy_tags(card_data):
    """Generate basic synergy tags"""
    tags = []
    
    # Type-based
    card_type = card_data.get('type', 'troop')
    tags.append(card_type)
    
    # Cost-based
    cost = card_data.get('elixir_cost', 5)
    if cost <= 3:
        tags.append('cycle')
    elif cost >= 6:
        tags.append('beatdown')
    
    # Role-based
    if card_data.get('defensive_value', 5) > 7:
        tags.append('defensive')
    if card_data.get('offensive_value', 5) > 7:
        tags.append('offensive')
    
    # Target-based
    target = card_data.get('target', 'ground')
    if 'air' in target:
        tags.append('air_defense')
    
    return tags

def generate_basic_anti_synergy_tags(card_data):
    """Generate basic anti-synergy tags"""
    tags = []
    
    # High cost cards don't synergize well together
    if card_data.get('elixir_cost', 5) >= 6:
        tags.append('heavy_cost')
    
    # Defensive buildings don't stack
    if (card_data.get('type') == 'building' and 
        card_data.get('defensive_value', 5) > 6):
        tags.append('defensive_building')
    
    return tags

def estimate_deploy_time(card_type):
    """Estimate deployment time"""
    times = {'spell': 0.5, 'building': 1.0, 'troop': 0.8}
    return times.get(card_type, 0.8)

def has_area_damage(card_name):
    """Check if card has area damage"""
    area_cards = ['Wizard', 'Bomber', 'Baby Dragon', 'Valkyrie', 'Bowler', 
                  'Executioner', 'Fireball', 'Arrows', 'Rocket', 'Lightning']
    return card_name in area_cards

def estimate_movement_speed(speed):
    """Convert speed to numeric value"""
    speeds = {'slow': 0.6, 'medium': 1.0, 'fast': 1.4, 'very_fast': 1.8}
    return speeds.get(speed, 1.0)

if __name__ == "__main__":
    print("Enhancing Clash Royale card database...")
    enhance_cards_json()
    
    # Test the enhanced database
    print("\nTesting enhanced database...")
    db_manager = CardDatabaseManager("cards_enhanced.json")
    
    # Test some functionality
    knight = db_manager.get_card("Knight")
    if knight:
        print(f"Knight meta tier: {knight.meta.meta_tier}")
        print(f"Knight synergy tags: {knight.strategy.synergy_tags}")
    
    # Test synergy finding
    synergies = db_manager.find_synergistic_cards("Giant", ["Knight", "Wizard", "Archers"])
    print(f"Cards that synergize with Giant: {synergies}")
    
    print("\nCard database enhancement complete!")
