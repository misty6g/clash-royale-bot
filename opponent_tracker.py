import time
from typing import List, Set, Dict
from redis_card_manager import RedisCardManager

class OpponentTracker:
    def __init__(self, redis_manager: RedisCardManager):
        self.redis = redis_manager
        self.opponent_deck = set()
        self.opponent_elixir = 10  # Starting elixir
        self.opponent_card_cycle = []
        self.last_opponent_play_time = 0
        self.elixir_generation_rate = 1/2.8  # 1 elixir per 2.8 seconds
        
    def track_opponent_card(self, card_name: str, elixir_cost: int):
        """Track opponent card play and update elixir"""
        self.opponent_deck.add(card_name)
        self.opponent_card_cycle.append(card_name)
        self.opponent_elixir = max(0, self.opponent_elixir - elixir_cost)
        self.last_opponent_play_time = time.time()
        
        # Store in Redis for persistence if available
        if self.redis.redis_available:
            try:
                self.redis.redis_client.sadd("opponent:deck", card_name)
                self.redis.redis_client.set("opponent:elixir", self.opponent_elixir)
                self.redis.redis_client.lpush("opponent:cycle", card_name)
                # Keep only last 16 cards in cycle (2 full rotations)
                self.redis.redis_client.ltrim("opponent:cycle", 0, 15)
            except Exception as e:
                print(f"Failed to store opponent data in Redis: {e}")
        
    def estimate_opponent_elixir(self) -> float:
        """Estimate current opponent elixir based on time"""
        time_since_last_play = time.time() - self.last_opponent_play_time
        elixir_gained = time_since_last_play * self.elixir_generation_rate
        return min(10, self.opponent_elixir + elixir_gained)
        
    def get_likely_opponent_cards(self) -> List[str]:
        """Predict what cards opponent might play next"""
        if len(self.opponent_card_cycle) >= 8:
            # Full cycle known, predict rotation
            cycle_position = len(self.opponent_card_cycle) % 8
            if cycle_position < len(self.opponent_card_cycle):
                return [self.opponent_card_cycle[cycle_position]]
        
        # Return known cards from deck
        return list(self.opponent_deck)
    
    def get_opponent_deck_composition(self) -> Dict[str, int]:
        """Get composition analysis of opponent deck"""
        composition = {
            'total_cards': len(self.opponent_deck),
            'avg_elixir_cost': 0,
            'spell_count': 0,
            'building_count': 0,
            'troop_count': 0
        }
        
        if not self.opponent_deck:
            return composition
            
        total_cost = 0
        for card_name in self.opponent_deck:
            card_data = self.redis.get_card_data(card_name)
            if card_data:
                cost = int(card_data.get('elixir_cost', 0))
                total_cost += cost
                
                card_type = card_data.get('type', 'unknown')
                if card_type == 'spell':
                    composition['spell_count'] += 1
                elif card_type == 'building':
                    composition['building_count'] += 1
                elif card_type == 'troop':
                    composition['troop_count'] += 1
        
        if len(self.opponent_deck) > 0:
            composition['avg_elixir_cost'] = total_cost / len(self.opponent_deck)
            
        return composition
    
    def predict_opponent_strategy(self) -> str:
        """Predict opponent's likely strategy based on observed cards"""
        composition = self.get_opponent_deck_composition()
        
        if composition['avg_elixir_cost'] > 4.5:
            return "beatdown"  # Heavy, expensive cards
        elif composition['spell_count'] >= 3:
            return "spell_cycle"  # Lots of spells
        elif composition['building_count'] >= 2:
            return "defensive"  # Multiple buildings
        elif composition['avg_elixir_cost'] < 3.5:
            return "cycle"  # Fast, cheap cards
        else:
            return "balanced"  # Mixed strategy
    
    def reset_opponent_data(self):
        """Reset opponent tracking for new match"""
        self.opponent_deck.clear()
        self.opponent_card_cycle.clear()
        self.opponent_elixir = 10
        self.last_opponent_play_time = time.time()
        
        # Clear Redis data if available
        if self.redis.redis_available:
            try:
                self.redis.redis_client.delete("opponent:deck")
                self.redis.redis_client.delete("opponent:cycle")
                self.redis.redis_client.set("opponent:elixir", 10)
            except Exception as e:
                print(f"Failed to clear opponent data from Redis: {e}")
    
    def get_tracking_stats(self) -> Dict:
        """Get current tracking statistics"""
        return {
            'cards_seen': len(self.opponent_deck),
            'estimated_elixir': self.estimate_opponent_elixir(),
            'predicted_strategy': self.predict_opponent_strategy(),
            'cycle_length': len(self.opponent_card_cycle),
            'last_play_time': self.last_opponent_play_time
        }
