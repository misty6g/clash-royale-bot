from typing import List, Optional, Dict, Tuple
import time
import numpy as np
from redis_card_manager import RedisCardManager
from opponent_tracker import OpponentTracker

class CounterStrategy:
    def __init__(self, redis_manager: RedisCardManager, opponent_tracker: OpponentTracker = None):
        self.redis = redis_manager
        self.opponent = opponent_tracker

        # Enhanced strategy tracking
        self.counter_success_history = {}
        self.timing_patterns = {}
        self.placement_effectiveness = {}
        self.meta_adaptations = {}
        
    def get_best_counter(self, enemy_card: str, my_hand: List[str], context: Dict = None) -> Optional[str]:
        """Find best counter card from current hand with enhanced context"""
        if not my_hand:
            return None

        context = context or {}
        best_card = None
        best_score = 0

        for my_card in my_hand:
            score = self._calculate_enhanced_counter_score(my_card, enemy_card, context)
            if score > best_score:
                best_score = score
                best_card = my_card

        # Dynamic threshold based on game state
        threshold = self._get_dynamic_threshold(context)
        return best_card if best_score > threshold else None

    def get_multi_counter_strategy(self, enemy_cards: List[str], my_hand: List[str], context: Dict = None) -> List[Tuple[str, str, float]]:
        """Get counter strategies for multiple enemy cards"""
        strategies = []
        context = context or {}

        for enemy_card in enemy_cards:
            counter = self.get_best_counter(enemy_card, my_hand, context)
            if counter:
                score = self._calculate_enhanced_counter_score(counter, enemy_card, context)
                strategies.append((counter, enemy_card, score))

        # Sort by effectiveness
        strategies.sort(key=lambda x: x[2], reverse=True)
        return strategies

    def predict_optimal_timing(self, my_card: str, enemy_card: str, context: Dict = None) -> float:
        """Predict optimal timing for counter play"""
        context = context or {}

        # Base timing from card properties
        my_deploy_time = self._get_card_deploy_time(my_card)
        enemy_deploy_time = self._get_card_deploy_time(enemy_card)

        # Adjust for distance and positioning
        enemy_position = context.get('enemy_position', (0.5, 0.5))
        optimal_counter_position = self._get_optimal_counter_position(my_card, enemy_card, enemy_position)

        # Calculate timing based on movement speeds and ranges
        timing_adjustment = self._calculate_timing_adjustment(my_card, enemy_card, enemy_position, optimal_counter_position)

        return my_deploy_time + timing_adjustment
        
    def _calculate_enhanced_counter_score(self, my_card: str, enemy_card: str, context: Dict) -> float:
        """Enhanced counter score calculation with context"""
        base_score = self._calculate_counter_score(my_card, enemy_card)

        # Context-based adjustments
        elixir_context = context.get('elixir_advantage', 0)
        game_phase = context.get('game_phase', 'normal')
        enemy_position = context.get('enemy_position', (0.5, 0.5))
        my_tower_health = context.get('my_tower_health', 100)

        # Elixir advantage adjustment
        if elixir_context > 2:
            base_score *= 1.2  # More aggressive when ahead
        elif elixir_context < -2:
            base_score *= 0.8  # More conservative when behind

        # Game phase adjustment
        if game_phase == 'overtime':
            base_score *= 1.3  # More aggressive in overtime
        elif game_phase == 'sudden_death':
            base_score *= 1.5  # Very aggressive in sudden death

        # Positional adjustment
        position_bonus = self._calculate_position_bonus(my_card, enemy_card, enemy_position)
        base_score *= position_bonus

        # Defensive urgency
        if my_tower_health < 50:
            defensive_value = self._get_card_defensive_value(my_card)
            base_score *= (1 + defensive_value * 0.3)

        # Historical success rate
        historical_bonus = self._get_historical_success_rate(my_card, enemy_card)
        base_score *= (0.8 + historical_bonus * 0.4)

        return min(2.0, base_score)  # Cap at 2.0

    def _calculate_counter_score(self, my_card: str, enemy_card: str) -> float:
        """Calculate how effective my_card is against enemy_card"""
        # Get counter confidence from Redis or JSON fallback
        if self.redis.redis_available:
            counter_key = f"{self.redis.card_prefix}{my_card}:counters"
            confidence = self.redis.redis_client.zscore(counter_key, enemy_card)
            if confidence is not None:
                base_confidence = float(confidence)
            else:
                # Fallback to JSON data
                base_confidence = self._get_json_counter_confidence(my_card, enemy_card)
        else:
            base_confidence = self._get_json_counter_confidence(my_card, enemy_card)
        
        # Factor in elixir efficiency
        my_cost = self._get_card_cost(my_card)
        enemy_cost = self._get_card_cost(enemy_card)
        
        if my_cost > 0:
            elixir_efficiency = enemy_cost / my_cost
            # Bonus for positive elixir trades, penalty for negative
            elixir_bonus = min(1.5, max(0.5, elixir_efficiency))
        else:
            elixir_bonus = 1.0
            
        return base_confidence * elixir_bonus
    
    def _get_json_counter_confidence(self, my_card: str, enemy_card: str) -> float:
        """Get counter confidence from JSON data"""
        my_card_data = self.redis.json_cards.get(my_card, {})
        counters = my_card_data.get('counters', [])
        
        if enemy_card in counters:
            # Simple heuristic: position in counter list indicates effectiveness
            try:
                position = counters.index(enemy_card)
                # Earlier in list = more effective (higher confidence)
                return max(0.1, 1.0 - (position / len(counters)) * 0.8)
            except ValueError:
                return 0.5
        return 0.1  # Very low confidence if not in counter list
    
    def _get_card_cost(self, card_name: str) -> int:
        """Get elixir cost of a card"""
        card_data = self.redis.get_card_data(card_name)
        return int(card_data.get('elixir_cost', 0))
        
    def predict_opponent_response(self, my_card: str) -> List[str]:
        """Predict how opponent might counter my card"""
        if self.redis.redis_available:
            countered_key = f"{self.redis.card_prefix}{my_card}:countered_by"
            potential_counters = self.redis.redis_client.zrange(countered_key, 0, -1, withscores=True)
        else:
            # Use JSON fallback
            my_card_data = self.redis.json_cards.get(my_card, {})
            countered_by = my_card_data.get('countered_by', [])
            potential_counters = [(card, 0.5) for card in countered_by]
        
        # Filter by cards opponent has in deck if tracker available
        if self.opponent:
            available_counters = []
            for counter, confidence in potential_counters:
                if counter in self.opponent.opponent_deck:
                    available_counters.append((counter, confidence))
            return [card for card, _ in sorted(available_counters, key=lambda x: x[1], reverse=True)]

    def _get_dynamic_threshold(self, context: Dict) -> float:
        """Calculate dynamic threshold based on game context"""
        base_threshold = 0.3

        # Adjust based on elixir advantage
        elixir_advantage = context.get('elixir_advantage', 0)
        if elixir_advantage > 3:
            base_threshold -= 0.1  # Lower threshold when ahead
        elif elixir_advantage < -3:
            base_threshold += 0.1  # Higher threshold when behind

        # Adjust based on tower health
        my_tower_health = context.get('my_tower_health', 100)
        if my_tower_health < 30:
            base_threshold -= 0.15  # More desperate when low health

        return max(0.1, min(0.6, base_threshold))

    def _calculate_position_bonus(self, my_card: str, enemy_card: str, enemy_position: Tuple[float, float]) -> float:
        """Calculate positional effectiveness bonus"""
        # Get card properties
        my_range = self._get_card_range(my_card)
        my_speed = self._get_card_speed(my_card)
        enemy_speed = self._get_card_speed(enemy_card)

        # Calculate distance from optimal position
        optimal_pos = self._get_optimal_counter_position(my_card, enemy_card, enemy_position)
        distance = np.sqrt((optimal_pos[0] - enemy_position[0])**2 + (optimal_pos[1] - enemy_position[1])**2)

        # Bonus based on range and positioning
        if my_range > 3:  # Long range units
            return 1.2 if distance > 0.3 else 1.0
        else:  # Short range units
            return 1.2 if distance < 0.2 else 0.9

    def _get_optimal_counter_position(self, my_card: str, enemy_card: str, enemy_position: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate optimal position to counter enemy card"""
        # Simple heuristic - adjust based on card types
        my_range = self._get_card_range(my_card)

        if my_range > 5:  # Long range
            # Stay back and to the side
            return (enemy_position[0] + 0.2, enemy_position[1] - 0.3)
        elif my_range > 3:  # Medium range
            # Moderate distance
            return (enemy_position[0] + 0.1, enemy_position[1] - 0.2)
        else:  # Short range
            # Get close
            return (enemy_position[0], enemy_position[1] - 0.1)

    def _get_historical_success_rate(self, my_card: str, enemy_card: str) -> float:
        """Get historical success rate for this counter"""
        key = f"{my_card}_vs_{enemy_card}"
        if key in self.counter_success_history:
            history = self.counter_success_history[key]
            if len(history) > 0:
                return sum(history) / len(history)
        return 0.5  # Default neutral rate

    def _get_card_defensive_value(self, card: str) -> float:
        """Get defensive value of a card"""
        card_data = self.redis.get_card_data(card)
        return card_data.get('defensive_value', 5) / 10.0

    def _get_card_range(self, card: str) -> float:
        """Get range of a card"""
        card_data = self.redis.get_card_data(card)
        range_str = card_data.get('range', '1')
        # Extract numeric value from range string
        try:
            return float(range_str.split()[0])
        except:
            return 1.0

    def _get_card_speed(self, card: str) -> str:
        """Get speed of a card"""
        card_data = self.redis.get_card_data(card)
        return card_data.get('speed', 'medium')

    def _get_card_deploy_time(self, card: str) -> float:
        """Get deployment time of a card"""
        card_data = self.redis.get_card_data(card)
        # Estimate based on card type
        card_type = card_data.get('type', 'troop')
        if card_type == 'spell':
            return 0.5
        elif card_type == 'building':
            return 1.0
        else:
            return 0.8

    def _calculate_timing_adjustment(self, my_card: str, enemy_card: str, enemy_pos: Tuple[float, float], counter_pos: Tuple[float, float]) -> float:
        """Calculate timing adjustment for optimal counter"""
        # Distance-based timing
        distance = np.sqrt((counter_pos[0] - enemy_pos[0])**2 + (counter_pos[1] - enemy_pos[1])**2)

        # Speed-based adjustment
        my_speed = self._get_card_speed(my_card)
        speed_multiplier = {'slow': 1.5, 'medium': 1.0, 'fast': 0.7, 'very_fast': 0.5}.get(my_speed, 1.0)

        return distance * speed_multiplier * 2.0  # Base timing factor

    def update_counter_success(self, my_card: str, enemy_card: str, success: bool):
        """Update historical success rate"""
        key = f"{my_card}_vs_{enemy_card}"
        if key not in self.counter_success_history:
            self.counter_success_history[key] = []

        self.counter_success_history[key].append(1.0 if success else 0.0)

        # Keep only recent history
        if len(self.counter_success_history[key]) > 50:
            self.counter_success_history[key] = self.counter_success_history[key][-50:]
        else:
            return [card for card, _ in sorted(potential_counters, key=lambda x: x[1], reverse=True)[:5]]
    
    def get_synergy_recommendations(self, my_card: str, my_hand: List[str]) -> List[str]:
        """Get cards that synergize well with the given card"""
        if self.redis.redis_available:
            synergy_key = f"{self.redis.card_prefix}{my_card}:synergies"
            synergies = self.redis.redis_client.zrange(synergy_key, 0, -1, withscores=True)
        else:
            # Use JSON fallback
            my_card_data = self.redis.json_cards.get(my_card, {})
            synergy_list = my_card_data.get('synergies', [])
            synergies = [(card, 0.5) for card in synergy_list]
        
        # Filter by cards available in hand
        available_synergies = []
        for synergy_card, confidence in synergies:
            if synergy_card in my_hand:
                available_synergies.append((synergy_card, confidence))
        
        return [card for card, _ in sorted(available_synergies, key=lambda x: x[1], reverse=True)]
    
    def evaluate_play_timing(self, my_card: str, enemy_card: str) -> Dict[str, float]:
        """Evaluate the timing of playing a card against an enemy"""
        evaluation = {
            'immediate_threat': 0.0,
            'elixir_efficiency': 0.0,
            'positioning_advantage': 0.0,
            'overall_score': 0.0
        }
        
        # Calculate immediate threat level
        enemy_data = self.redis.get_card_data(enemy_card)
        enemy_danger = float(enemy_data.get('danger_level', 5))
        evaluation['immediate_threat'] = min(1.0, enemy_danger / 10.0)
        
        # Calculate elixir efficiency
        my_cost = self._get_card_cost(my_card)
        enemy_cost = self._get_card_cost(enemy_card)
        if my_cost > 0:
            evaluation['elixir_efficiency'] = min(1.0, enemy_cost / my_cost / 2.0)
        
        # Simple positioning advantage (could be enhanced with actual positioning)
        evaluation['positioning_advantage'] = 0.5  # Neutral for now
        
        # Overall score
        evaluation['overall_score'] = (
            evaluation['immediate_threat'] * 0.4 +
            evaluation['elixir_efficiency'] * 0.4 +
            evaluation['positioning_advantage'] * 0.2
        )
        
        return evaluation
