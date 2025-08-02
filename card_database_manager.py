import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time

class CardType(Enum):
    TROOP = "troop"
    SPELL = "spell"
    BUILDING = "building"

class Rarity(Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    CHAMPION = "champion"

class Speed(Enum):
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"
    VERY_FAST = "very_fast"
    INSTANT = "instant"  # For spells
    STATIONARY = "stationary"  # For buildings

@dataclass
class CardStats:
    """Enhanced card statistics"""
    elixir_cost: int
    hitpoints: int
    damage: int
    hit_speed: float
    damage_per_second: int
    range: str
    count: int
    
    # Enhanced stats
    deploy_time: float = 1.0
    lifetime: Optional[float] = None  # For buildings/spells
    area_damage: bool = False
    splash_radius: Optional[float] = None
    movement_speed: float = 1.0
    sight_range: float = 5.5

@dataclass
class CardMeta:
    """Meta information about card usage"""
    usage_rate: float = 0.0
    win_rate: float = 0.0
    popularity_trend: float = 0.0  # -1 to 1, negative = declining
    meta_tier: str = "B"  # S, A, B, C, D
    last_balance_change: Optional[str] = None
    
@dataclass
class CardStrategy:
    """Strategic information for AI decision making"""
    optimal_placements: List[str]
    defensive_value: int  # 1-10
    offensive_value: int  # 1-10
    versatility: int  # 1-10
    skill_cap: int  # 1-10, how hard to use effectively
    
    # Situational effectiveness
    early_game_value: int = 5
    mid_game_value: int = 5
    late_game_value: int = 5
    overtime_value: int = 5
    
    # Synergy categories
    synergy_tags: List[str] = None
    anti_synergy_tags: List[str] = None

@dataclass
class EnhancedCard:
    """Complete enhanced card data structure"""
    name: str
    type: CardType
    subtype: str
    rarity: Rarity
    damage_type: str
    target: str
    speed: Speed
    
    # Core stats
    stats: CardStats
    
    # Strategic info
    strategy: CardStrategy
    
    # Meta info
    meta: CardMeta
    
    # Relationships
    counters: List[str]
    countered_by: List[str]
    synergies: List[str]
    
    # Dynamic learning data
    dynamic_data: Dict = None
    
    def __post_init__(self):
        if self.dynamic_data is None:
            self.dynamic_data = {
                'success_rate': 0.5,
                'avg_damage_dealt': 0,
                'avg_elixir_efficiency': 1.0,
                'placement_heatmap': {},
                'timing_effectiveness': {},
                'last_updated': time.time()
            }
        
        if self.strategy.synergy_tags is None:
            self.strategy.synergy_tags = []
        
        if self.strategy.anti_synergy_tags is None:
            self.strategy.anti_synergy_tags = []

class CardDatabaseManager:
    """Enhanced card database manager with learning capabilities"""
    
    def __init__(self, cards_json_path: str = "cards.json"):
        self.cards_json_path = cards_json_path
        self.cards: Dict[str, EnhancedCard] = {}
        self.synergy_matrix: Dict[Tuple[str, str], float] = {}
        self.counter_matrix: Dict[Tuple[str, str], float] = {}
        
        # Load existing data
        self.load_cards()
        self._build_relationship_matrices()
    
    def load_cards(self):
        """Load cards from JSON and convert to enhanced format"""
        try:
            with open(self.cards_json_path, 'r') as f:
                cards_data = json.load(f)
            
            for name, data in cards_data.items():
                enhanced_card = self._convert_to_enhanced_card(name, data)
                self.cards[name] = enhanced_card
            
            print(f"Loaded {len(self.cards)} enhanced cards")
            
        except Exception as e:
            print(f"Error loading cards: {e}")
            self.cards = {}
    
    def _convert_to_enhanced_card(self, name: str, data: Dict) -> EnhancedCard:
        """Convert legacy card data to enhanced format"""
        
        # Extract stats
        stats = CardStats(
            elixir_cost=data.get('elixir_cost', 1),
            hitpoints=data.get('hitpoints', 100),
            damage=data.get('damage', 50),
            hit_speed=data.get('hit_speed', 1.0),
            damage_per_second=data.get('damage_per_second', 50),
            range=data.get('range', '1'),
            count=data.get('count', 1),
            deploy_time=self._estimate_deploy_time(data.get('type', 'troop')),
            area_damage=self._has_area_damage(name, data),
            movement_speed=self._estimate_movement_speed(data.get('speed', 'medium'))
        )
        
        # Extract strategy info
        strategy = CardStrategy(
            optimal_placements=self._parse_optimal_placements(data.get('optimal_placement', 'center')),
            defensive_value=data.get('defensive_value', 5),
            offensive_value=data.get('offensive_value', 5),
            versatility=self._calculate_versatility(data),
            skill_cap=self._estimate_skill_cap(name, data),
            synergy_tags=self._generate_synergy_tags(name, data),
            anti_synergy_tags=self._generate_anti_synergy_tags(name, data)
        )
        
        # Meta information
        meta = CardMeta(
            usage_rate=0.1,  # Default values, would be updated from real data
            win_rate=0.5,
            meta_tier=self._estimate_meta_tier(data)
        )
        
        return EnhancedCard(
            name=name,
            type=CardType(data.get('type', 'troop')),
            subtype=data.get('subtype', 'generic'),
            rarity=Rarity(data.get('rarity', 'common')),
            damage_type=data.get('damage_type', 'physical'),
            target=data.get('target', 'ground'),
            speed=Speed(data.get('speed', 'medium')),
            stats=stats,
            strategy=strategy,
            meta=meta,
            counters=data.get('counters', []),
            countered_by=data.get('countered_by', []),
            synergies=data.get('synergies', [])
        )
    
    def _estimate_deploy_time(self, card_type: str) -> float:
        """Estimate deployment time based on card type"""
        deploy_times = {
            'spell': 0.5,
            'building': 1.0,
            'troop': 0.8
        }
        return deploy_times.get(card_type, 0.8)
    
    def _has_area_damage(self, name: str, data: Dict) -> bool:
        """Determine if card has area damage"""
        area_damage_cards = ['Wizard', 'Bomber', 'Baby Dragon', 'Valkyrie', 'Bowler', 'Executioner']
        return name in area_damage_cards or 'splash' in data.get('damage_type', '').lower()
    
    def _estimate_movement_speed(self, speed: str) -> float:
        """Convert speed category to numeric value"""
        speed_values = {
            'slow': 0.6,
            'medium': 1.0,
            'fast': 1.4,
            'very_fast': 1.8,
            'instant': 0.0,  # For spells/instant effects
            'stationary': 0.0  # For buildings
        }
        return speed_values.get(speed, 1.0)
    
    def _parse_optimal_placements(self, placement: str) -> List[str]:
        """Parse optimal placement string into list"""
        if isinstance(placement, list):
            return placement
        return [placement] if placement else ['center']
    
    def _calculate_versatility(self, data: Dict) -> int:
        """Calculate versatility score based on card properties"""
        versatility = 5  # Base score
        
        # Bonus for multiple targets
        if data.get('target') == 'air_and_ground':
            versatility += 2
        
        # Bonus for multiple roles
        defensive = data.get('defensive_value', 5)
        offensive = data.get('offensive_value', 5)
        if abs(defensive - offensive) < 3:  # Balanced card
            versatility += 1
        
        # Bonus for reasonable elixir cost
        cost = data.get('elixir_cost', 5)
        if 2 <= cost <= 5:
            versatility += 1
        
        return min(10, max(1, versatility))
    
    def _estimate_skill_cap(self, name: str, data: Dict) -> int:
        """Estimate skill requirement for effective use"""
        high_skill_cards = ['X-Bow', 'Mortar', 'Miner', 'Graveyard', 'Balloon', 'Lava Hound']
        medium_skill_cards = ['Hog Rider', 'Giant', 'Golem', 'P.E.K.K.A']
        
        if name in high_skill_cards:
            return 8
        elif name in medium_skill_cards:
            return 6
        elif data.get('type') == 'spell':
            return 7  # Spells generally require good timing
        else:
            return 5  # Default medium skill
    
    def _generate_synergy_tags(self, name: str, data: Dict) -> List[str]:
        """Generate synergy tags for better deck building"""
        tags = []
        
        # Type-based tags
        card_type = data.get('type', 'troop')
        tags.append(card_type)
        
        # Role-based tags
        if data.get('defensive_value', 5) > 7:
            tags.append('defensive')
        if data.get('offensive_value', 5) > 7:
            tags.append('offensive')
        
        # Cost-based tags
        cost = data.get('elixir_cost', 5)
        if cost <= 3:
            tags.append('cycle')
        elif cost >= 6:
            tags.append('beatdown')
        
        # Special tags
        if data.get('target') == 'air':
            tags.append('air_defense')
        if data.get('damage_type') == 'spell':
            tags.append('spell_damage')
        
        return tags
    
    def _generate_anti_synergy_tags(self, name: str, data: Dict) -> List[str]:
        """Generate anti-synergy tags"""
        anti_tags = []
        
        # High cost cards don't synergize with other high cost cards
        if data.get('elixir_cost', 5) >= 6:
            anti_tags.append('heavy_cost')
        
        # Defensive buildings don't stack well
        if data.get('type') == 'building' and data.get('defensive_value', 5) > 6:
            anti_tags.append('defensive_building')
        
        return anti_tags
    
    def _estimate_meta_tier(self, data: Dict) -> str:
        """Estimate meta tier based on stats"""
        # Simple heuristic based on versatility and power
        versatility = self._calculate_versatility(data)
        power = (data.get('defensive_value', 5) + data.get('offensive_value', 5)) / 2
        
        score = versatility + power
        if score >= 15:
            return 'S'
        elif score >= 12:
            return 'A'
        elif score >= 9:
            return 'B'
        elif score >= 6:
            return 'C'
        else:
            return 'D'
    
    def _build_relationship_matrices(self):
        """Build synergy and counter matrices for fast lookup"""
        for card_name, card in self.cards.items():
            # Build synergy matrix
            for synergy in card.synergies:
                if synergy in self.cards:
                    self.synergy_matrix[(card_name, synergy)] = 1.0
                    self.synergy_matrix[(synergy, card_name)] = 1.0
            
            # Build counter matrix
            for counter in card.counters:
                if counter in self.cards:
                    self.counter_matrix[(card_name, counter)] = 1.0
            
            for countered in card.countered_by:
                if countered in self.cards:
                    self.counter_matrix[(countered, card_name)] = 1.0
    
    def get_card(self, name: str) -> Optional[EnhancedCard]:
        """Get enhanced card by name"""
        return self.cards.get(name)
    
    def get_synergy_score(self, card1: str, card2: str) -> float:
        """Get synergy score between two cards"""
        return self.synergy_matrix.get((card1, card2), 0.0)
    
    def get_counter_score(self, attacker: str, defender: str) -> float:
        """Get counter effectiveness score"""
        return self.counter_matrix.get((attacker, defender), 0.0)
    
    def find_synergistic_cards(self, card_name: str, available_cards: List[str]) -> List[Tuple[str, float]]:
        """Find cards that synergize well with the given card"""
        synergies = []
        for available_card in available_cards:
            if available_card != card_name:
                score = self.get_synergy_score(card_name, available_card)
                if score > 0:
                    synergies.append((available_card, score))
        
        return sorted(synergies, key=lambda x: x[1], reverse=True)
    
    def find_counters(self, target_card: str, available_cards: List[str]) -> List[Tuple[str, float]]:
        """Find cards that counter the target card"""
        counters = []
        for available_card in available_cards:
            score = self.get_counter_score(available_card, target_card)
            if score > 0:
                counters.append((available_card, score))
        
        return sorted(counters, key=lambda x: x[1], reverse=True)
    
    def update_dynamic_data(self, card_name: str, performance_data: Dict):
        """Update dynamic learning data for a card"""
        if card_name in self.cards:
            card = self.cards[card_name]
            card.dynamic_data.update(performance_data)
            card.dynamic_data['last_updated'] = time.time()
    
    def export_enhanced_cards(self, output_path: str = "enhanced_cards.json"):
        """Export enhanced cards to JSON"""
        export_data = {}
        for name, card in self.cards.items():
            export_data[name] = asdict(card)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Enhanced cards exported to {output_path}")
    
    def get_deck_synergy_score(self, deck: List[str]) -> float:
        """Calculate overall synergy score for a deck"""
        if len(deck) < 2:
            return 0.0
        
        total_synergy = 0.0
        pair_count = 0
        
        for i in range(len(deck)):
            for j in range(i + 1, len(deck)):
                synergy = self.get_synergy_score(deck[i], deck[j])
                total_synergy += synergy
                pair_count += 1
        
        return total_synergy / pair_count if pair_count > 0 else 0.0
