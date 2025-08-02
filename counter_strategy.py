from typing import List, Optional, Dict, Tuple
from redis_card_manager import RedisCardManager
from opponent_tracker import OpponentTracker

class CounterStrategy:
    def __init__(self, redis_manager: RedisCardManager, opponent_tracker: OpponentTracker = None):
        self.redis = redis_manager
        self.opponent = opponent_tracker
        
    def get_best_counter(self, enemy_card: str, my_hand: List[str]) -> Optional[str]:
        """Find best counter card from current hand"""
        if not my_hand:
            return None
            
        best_card = None
        best_score = 0
        
        for my_card in my_hand:
            score = self._calculate_counter_score(my_card, enemy_card)
            if score > best_score:
                best_score = score
                best_card = my_card
                
        return best_card if best_score > 0.3 else None  # Minimum confidence threshold
        
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
