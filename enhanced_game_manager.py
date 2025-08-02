#!/usr/bin/env python3
"""
Enhanced Game State Manager for Clash Royale Bot
Manages real-time game state, action validation, and match tracking
"""

import time
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from datetime import datetime

from enhanced_vision_system import GameState, GamePhase, EnhancedVisionSystem

class MatchResult(Enum):
    ONGOING = "ongoing"
    VICTORY = "victory"
    DEFEAT = "defeat"
    DRAW = "draw"

@dataclass
class MatchStats:
    """Statistics for a single match"""
    match_id: str
    start_time: datetime
    end_time: Optional[datetime]
    result: MatchResult
    
    # Game metrics
    total_elixir_spent: int
    cards_played: List[str]
    damage_dealt: int
    damage_taken: int
    towers_destroyed: int
    towers_lost: int
    
    # AI metrics
    decisions_made: int
    average_decision_time: float
    vision_accuracy: Dict[str, float]
    
    # Performance metrics
    win_condition_progress: float
    defensive_efficiency: float
    elixir_efficiency: float

class EnhancedGameManager:
    """Enhanced game state manager with real-time tracking"""
    
    def __init__(self, vision_system: EnhancedVisionSystem, platform_manager=None):
        self.vision_system = vision_system
        self.platform_manager = platform_manager
        
        # Game state tracking
        self.current_match_stats = None
        self.match_history = []
        self.game_state_buffer = []  # Recent game states for analysis
        
        # Action validation
        self.last_action_time = 0
        self.action_cooldown = 0.5  # Minimum time between actions
        self.pending_actions = []
        
        # Performance tracking
        self.decision_times = []
        self.vision_accuracy_history = []
        
        # Match detection
        self.match_start_detected = False
        self.match_end_detected = False
        self.last_game_phase = GamePhase.NORMAL
        
        # Coordinate validation
        self.valid_play_area = self._calculate_valid_play_area()
        
        print("Enhanced Game Manager initialized")
    
    def _calculate_valid_play_area(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Calculate valid areas for card placement"""
        if self.platform_manager and self.platform_manager.emulator_window:
            window = self.platform_manager.emulator_window
            x, y, w, h = window['region']
            
            # Define play areas relative to emulator window
            return {
                'ally_side': (
                    x + int(w * 0.1),   # Left boundary
                    y + int(h * 0.5),   # Top boundary (middle of screen)
                    x + int(w * 0.9),   # Right boundary
                    y + int(h * 0.85)   # Bottom boundary (before cards)
                ),
                'enemy_side': (
                    x + int(w * 0.1),   # Left boundary
                    y + int(h * 0.15),  # Top boundary (after timer)
                    x + int(w * 0.9),   # Right boundary
                    y + int(h * 0.5)    # Bottom boundary (middle)
                ),
                'bridge': (
                    x + int(w * 0.1),   # Left boundary
                    y + int(h * 0.45),  # Top boundary
                    x + int(w * 0.9),   # Right boundary
                    y + int(h * 0.55)   # Bottom boundary
                )
            }
        else:
            # Default coordinates for full screen
            return {
                'ally_side': (100, 540, 1820, 900),
                'enemy_side': (100, 150, 1820, 540),
                'bridge': (100, 450, 1820, 590)
            }
    
    def start_new_match(self) -> str:
        """Start tracking a new match"""
        match_id = f"match_{int(time.time())}"
        
        self.current_match_stats = MatchStats(
            match_id=match_id,
            start_time=datetime.now(),
            end_time=None,
            result=MatchResult.ONGOING,
            total_elixir_spent=0,
            cards_played=[],
            damage_dealt=0,
            damage_taken=0,
            towers_destroyed=0,
            towers_lost=0,
            decisions_made=0,
            average_decision_time=0.0,
            vision_accuracy={},
            win_condition_progress=0.0,
            defensive_efficiency=0.0,
            elixir_efficiency=0.0
        )
        
        self.match_start_detected = True
        self.match_end_detected = False
        self.game_state_buffer = []
        
        print(f"Started tracking new match: {match_id}")
        return match_id
    
    def update_game_state(self) -> GameState:
        """Update and validate current game state"""
        try:
            # Get current game state from vision system
            game_state = self.vision_system.get_complete_game_state()
            
            # Add to buffer for analysis
            self.game_state_buffer.append(game_state)
            if len(self.game_state_buffer) > 50:  # Keep last 50 states
                self.game_state_buffer = self.game_state_buffer[-50:]
            
            # Detect match start/end
            self._detect_match_transitions(game_state)
            
            # Update match statistics
            if self.current_match_stats:
                self._update_match_stats(game_state)
            
            return game_state
            
        except Exception as e:
            print(f"Error updating game state: {e}")
            return None
    
    def _detect_match_transitions(self, game_state: GameState):
        """Detect match start and end transitions"""
        # Detect match start
        if not self.match_start_detected and game_state.phase == GamePhase.NORMAL:
            if game_state.my_elixir > 0 and len(game_state.my_cards) == 4:
                self.start_new_match()
        
        # Detect match end
        if not self.match_end_detected and game_state.phase == GamePhase.MATCH_END:
            self._end_current_match(game_state)
        
        # Track phase changes
        if game_state.phase != self.last_game_phase:
            print(f"Game phase changed: {self.last_game_phase} -> {game_state.phase}")
            self.last_game_phase = game_state.phase
    
    def _update_match_stats(self, game_state: GameState):
        """Update current match statistics"""
        if not self.current_match_stats:
            return
        
        # Update basic metrics
        self.current_match_stats.decisions_made += 1
        
        # Track tower status
        my_towers_remaining = sum(1 for health in game_state.my_tower_health.values() if health > 0)
        enemy_towers_remaining = sum(1 for health in game_state.enemy_tower_health.values() if health > 0)
        
        self.current_match_stats.towers_destroyed = 3 - enemy_towers_remaining
        self.current_match_stats.towers_lost = 3 - my_towers_remaining
        
        # Calculate win condition progress
        if enemy_towers_remaining > 0:
            self.current_match_stats.win_condition_progress = (3 - enemy_towers_remaining) / 3.0
        
        # Update vision accuracy if available
        if hasattr(game_state, 'detection_confidence'):
            self.current_match_stats.vision_accuracy = game_state.detection_confidence
    
    def _end_current_match(self, game_state: GameState):
        """End current match and save statistics"""
        if not self.current_match_stats:
            return
        
        self.current_match_stats.end_time = datetime.now()
        self.match_end_detected = True
        
        # Determine match result based on tower status
        my_towers = sum(1 for health in game_state.my_tower_health.values() if health > 0)
        enemy_towers = sum(1 for health in game_state.enemy_tower_health.values() if health > 0)
        
        if my_towers > enemy_towers:
            self.current_match_stats.result = MatchResult.VICTORY
        elif enemy_towers > my_towers:
            self.current_match_stats.result = MatchResult.DEFEAT
        else:
            self.current_match_stats.result = MatchResult.DRAW
        
        # Calculate final metrics
        if self.decision_times:
            self.current_match_stats.average_decision_time = sum(self.decision_times) / len(self.decision_times)
        
        # Save match to history
        self.match_history.append(self.current_match_stats)
        
        # Save to file
        self._save_match_stats()
        
        print(f"Match ended: {self.current_match_stats.result.value}")
        print(f"Towers destroyed: {self.current_match_stats.towers_destroyed}")
        print(f"Towers lost: {self.current_match_stats.towers_lost}")
        
        # Reset for next match
        self.current_match_stats = None
        self.match_start_detected = False
        self.decision_times = []
    
    def validate_action(self, action_index: int, card_name: str, position: Tuple[int, int]) -> bool:
        """Validate if an action can be executed"""
        current_time = time.time()
        
        # Check action cooldown
        if current_time - self.last_action_time < self.action_cooldown:
            print(f"Action blocked: cooldown not met ({current_time - self.last_action_time:.2f}s)")
            return False
        
        # Check if position is valid
        if not self._is_valid_position(position):
            print(f"Action blocked: invalid position {position}")
            return False
        
        # Check if we have enough elixir (simplified)
        game_state = self.vision_system.current_game_state
        if game_state and hasattr(game_state, 'my_elixir'):
            # This would need card cost data
            estimated_cost = 4  # Default cost
            if game_state.my_elixir < estimated_cost:
                print(f"Action blocked: insufficient elixir ({game_state.my_elixir} < {estimated_cost})")
                return False
        
        return True
    
    def _is_valid_position(self, position: Tuple[int, int]) -> bool:
        """Check if position is within valid play area"""
        x, y = position
        
        for area_name, (x1, y1, x2, y2) in self.valid_play_area.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        
        return False
    
    def execute_action(self, action_index: int, card_name: str, position: Tuple[int, int]) -> bool:
        """Execute validated action"""
        if not self.validate_action(action_index, card_name, position):
            return False
        
        try:
            start_time = time.time()
            
            # Execute action through platform manager
            if self.platform_manager:
                success = self.platform_manager.click_position(position)
            else:
                # Fallback to pyautogui
                import pyautogui
                pyautogui.click(position[0], position[1])
                success = True
            
            # Record timing
            execution_time = time.time() - start_time
            self.decision_times.append(execution_time)
            self.last_action_time = time.time()
            
            # Update match stats
            if self.current_match_stats and success:
                self.current_match_stats.cards_played.append(card_name)
                # Estimate elixir cost (would need card database)
                self.current_match_stats.total_elixir_spent += 4  # Default cost
            
            print(f"Action executed: {card_name} at {position} (took {execution_time:.3f}s)")
            return success
            
        except Exception as e:
            print(f"Error executing action: {e}")
            return False
    
    def get_match_statistics(self) -> Dict[str, Any]:
        """Get current match and historical statistics"""
        stats = {
            'current_match': asdict(self.current_match_stats) if self.current_match_stats else None,
            'match_history': [asdict(match) for match in self.match_history[-10:]],  # Last 10 matches
            'overall_stats': self._calculate_overall_stats()
        }
        
        return stats
    
    def _calculate_overall_stats(self) -> Dict[str, float]:
        """Calculate overall performance statistics"""
        if not self.match_history:
            return {}
        
        completed_matches = [m for m in self.match_history if m.result != MatchResult.ONGOING]
        
        if not completed_matches:
            return {}
        
        wins = sum(1 for m in completed_matches if m.result == MatchResult.VICTORY)
        total_matches = len(completed_matches)
        
        return {
            'win_rate': wins / total_matches if total_matches > 0 else 0,
            'total_matches': total_matches,
            'average_towers_destroyed': sum(m.towers_destroyed for m in completed_matches) / total_matches,
            'average_decision_time': sum(m.average_decision_time for m in completed_matches) / total_matches,
            'average_match_duration': sum((m.end_time - m.start_time).total_seconds() 
                                        for m in completed_matches if m.end_time) / total_matches
        }
    
    def _save_match_stats(self):
        """Save match statistics to file"""
        try:
            stats_file = "match_statistics.json"
            
            # Load existing stats
            existing_stats = []
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    existing_stats = json.load(f)
            
            # Add current match
            if self.current_match_stats:
                match_dict = asdict(self.current_match_stats)
                # Convert datetime objects to strings
                match_dict['start_time'] = self.current_match_stats.start_time.isoformat()
                if self.current_match_stats.end_time:
                    match_dict['end_time'] = self.current_match_stats.end_time.isoformat()
                
                existing_stats.append(match_dict)
            
            # Save updated stats
            with open(stats_file, 'w') as f:
                json.dump(existing_stats, f, indent=2)
            
            print(f"Match statistics saved to {stats_file}")
            
        except Exception as e:
            print(f"Error saving match statistics: {e}")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        current_state = self.vision_system.current_game_state
        
        if not current_state:
            return {}
        
        metrics = {
            'game_phase': current_state.phase.value,
            'my_elixir': current_state.my_elixir,
            'my_cards': current_state.my_cards,
            'towers_remaining': {
                'mine': sum(1 for h in current_state.my_tower_health.values() if h > 0),
                'enemy': sum(1 for h in current_state.enemy_tower_health.values() if h > 0)
            },
            'units_on_field': len(current_state.units_on_field),
            'detection_confidence': current_state.detection_confidence,
            'match_duration': (datetime.now() - self.current_match_stats.start_time).total_seconds() 
                            if self.current_match_stats else 0
        }
        
        return metrics

# Test function
def test_game_manager():
    """Test the enhanced game manager"""
    print("Testing Enhanced Game Manager...")
    
    try:
        from platform_manager import PlatformManager
        
        # Initialize components
        pm = PlatformManager()
        pm.find_emulator_window()
        
        vision = EnhancedVisionSystem(pm)
        game_manager = EnhancedGameManager(vision, pm)
        
        # Test game state update
        print("Testing game state update...")
        game_state = game_manager.update_game_state()
        print(f"Game state: {game_state}")
        
        # Test real-time metrics
        print("Testing real-time metrics...")
        metrics = game_manager.get_real_time_metrics()
        print(f"Metrics: {metrics}")
        
        # Test action validation
        print("Testing action validation...")
        valid = game_manager.validate_action(0, "Knight", (500, 600))
        print(f"Action validation: {valid}")
        
        print("Game manager test completed!")
        
    except Exception as e:
        print(f"Game manager test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_game_manager()
