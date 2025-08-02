#!/usr/bin/env python3
"""
Enhanced training system for Clash Royale bot with advanced features
"""

import os
import time
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import torch

# Import our enhanced components
from env import ClashRoyaleEnv
from enhanced_dqn_agent import EnhancedDQNAgent
from config import BotConfig
from redis_card_manager import RedisCardManager
from card_database_manager import CardDatabaseManager
from counter_strategy import CounterStrategy
from opponent_tracker import OpponentTracker
from performance_monitor import PerformanceMonitor
from pynput import keyboard

class EnhancedTrainingSystem:
    """Advanced training system with all enhanced features"""
    
    def __init__(self):
        print("Initializing Enhanced Training System...")
        
        # Load configuration
        self.config = BotConfig()
        
        # Initialize environment
        self.env = ClashRoyaleEnv()
        
        # Initialize enhanced DQN agent
        self.agent = EnhancedDQNAgent(
            state_size=self.env.state_size,
            action_size=self.env.action_size,
            config=self.config
        )
        
        # Initialize enhanced components
        self.redis_manager = RedisCardManager(self.config)
        self.card_db = CardDatabaseManager()
        self.performance_monitor = PerformanceMonitor(self.redis_manager)
        
        # Initialize strategy components if enabled
        self.opponent_tracker = None
        self.counter_strategy = None
        
        if self.config.ENABLE_OPPONENT_TRACKING:
            self.opponent_tracker = OpponentTracker(self.redis_manager)
        
        if self.config.ENABLE_COUNTER_STRATEGY:
            self.counter_strategy = CounterStrategy(self.redis_manager, self.opponent_tracker)
        
        # Training metrics
        self.training_metrics = {
            'episodes': 0,
            'total_reward': 0,
            'best_reward': float('-inf'),
            'win_rate': 0.0,
            'avg_decision_time': 0.0,
            'strategy_usage': {},
            'card_effectiveness': {},
            'learning_progress': []
        }
        
        # Keyboard controller for graceful shutdown
        self.keyboard_controller = KeyboardController()
        
        print("Enhanced Training System initialized successfully!")
        self._print_system_status()
    
    def _print_system_status(self):
        """Print current system status"""
        print("\n=== System Status ===")
        print(f"Environment: {type(self.env).__name__}")
        print(f"Agent: {type(self.agent).__name__}")
        print(f"Redis available: {self.redis_manager.redis_available}")
        print(f"Enhanced mode: {getattr(self.env, 'enhanced_mode', False)}")
        print(f"Opponent tracking: {self.opponent_tracker is not None}")
        print(f"Counter strategy: {self.counter_strategy is not None}")
        print(f"Card database: {len(self.card_db.cards)} cards loaded")
        print("=====================\n")
    
    def train(self, episodes: int = 1000, save_interval: int = 50):
        """Enhanced training loop with all features"""
        print(f"Starting enhanced training for {episodes} episodes...")
        
        for episode in range(episodes):
            if self.keyboard_controller.is_exit_requested():
                print("\nGraceful shutdown requested...")
                break
            
            episode_start_time = time.time()
            episode_reward = self._run_episode(episode)
            episode_duration = time.time() - episode_start_time
            
            # Update metrics
            self._update_training_metrics(episode, episode_reward, episode_duration)
            
            # Save model periodically
            if episode % save_interval == 0 and episode > 0:
                self._save_checkpoint(episode)
            
            # Print progress
            if episode % 10 == 0:
                self._print_progress(episode)
        
        # Final save and summary
        self._save_final_model()
        self._print_training_summary()
    
    def _run_episode(self, episode: int) -> float:
        """Run a single enhanced episode"""
        state = self.env.reset()
        total_reward = 0
        done = False
        step_count = 0
        
        # Episode-specific tracking
        episode_actions = []
        episode_strategies = []
        
        while not done and step_count < 1000:  # Max steps per episode
            step_start_time = time.time()
            
            # Get enhanced action with strategy
            action = self._get_enhanced_action(state, episode_actions)
            
            # Execute action
            next_state, reward, done = self.env.step(action)
            
            # Enhanced reward shaping
            shaped_reward = self._shape_reward(reward, state, action, next_state)
            
            # Store experience
            self.agent.remember(state, action, shaped_reward, next_state, done)
            
            # Track performance
            decision_time = (time.time() - step_start_time) * 1000
            self.performance_monitor.track_decision_time(decision_time)
            
            # Update state and tracking
            state = next_state
            total_reward += shaped_reward
            step_count += 1
            
            episode_actions.append(action)
            
            # Train agent periodically
            if len(self.agent.memory) > 32:
                self.agent.replay(batch_size=32)
        
        # Post-episode learning
        self._post_episode_learning(episode_actions, total_reward)
        
        return total_reward
    
    def _get_enhanced_action(self, state, episode_actions) -> int:
        """Get action using enhanced strategy system"""
        
        # Get base action from DQN
        if self.counter_strategy and len(episode_actions) > 5:
            # Use strategic action selection
            game_context = self._build_game_context(state)
            action = self.agent.strategic_act(state, game_context)
        else:
            # Use standard action selection
            action = self.agent.act(state)
        
        return action
    
    def _build_game_context(self, state) -> Dict:
        """Build game context for strategic decisions"""
        context = {
            'my_elixir': 10,  # Would extract from state
            'enemy_elixir': 10,  # Would extract from state
            'my_cards': [],  # Would get from card detection
            'enemy_cards': [],  # Would get from enemy detection
            'phase': 'normal',  # Would determine from game state
            'elixir_advantage': 0,
            'my_tower_health': 100,
            'enemy_position': (0.5, 0.5)
        }
        
        # Extract actual values from state if available
        # This would be implemented based on state representation
        
        return context
    
    def _shape_reward(self, base_reward: float, state, action: int, next_state) -> float:
        """Enhanced reward shaping for better learning"""
        shaped_reward = base_reward
        
        # Reward shaping based on strategic decisions
        if self.counter_strategy:
            # Bonus for using counter strategies
            # This would require integration with actual game state
            pass
        
        # Elixir efficiency bonus
        # Would calculate based on elixir trades
        
        # Timing bonus
        # Would reward good timing of card plays
        
        # Defensive bonus
        # Would reward successful defenses
        
        return shaped_reward
    
    def _post_episode_learning(self, episode_actions: List[int], total_reward: float):
        """Post-episode learning and adaptation"""
        
        # Update card effectiveness tracking
        if len(episode_actions) > 0:
            avg_reward_per_action = total_reward / len(episode_actions)
            
            for action in episode_actions:
                if action not in self.training_metrics['card_effectiveness']:
                    self.training_metrics['card_effectiveness'][action] = []
                
                self.training_metrics['card_effectiveness'][action].append(avg_reward_per_action)
        
        # Update counter strategy success rates
        if self.counter_strategy:
            # This would track which counter strategies worked
            pass
        
        # Update opponent patterns
        if self.opponent_tracker:
            # This would update opponent behavior patterns
            pass
    
    def _update_training_metrics(self, episode: int, reward: float, duration: float):
        """Update training metrics"""
        self.training_metrics['episodes'] = episode + 1
        self.training_metrics['total_reward'] += reward
        
        if reward > self.training_metrics['best_reward']:
            self.training_metrics['best_reward'] = reward
        
        # Update moving averages
        alpha = 0.1  # Learning rate for moving averages
        
        if episode == 0:
            self.training_metrics['avg_decision_time'] = duration
        else:
            self.training_metrics['avg_decision_time'] = (
                (1 - alpha) * self.training_metrics['avg_decision_time'] + 
                alpha * duration
            )
        
        # Track learning progress
        if episode % 10 == 0:
            progress_point = {
                'episode': episode,
                'avg_reward': self.training_metrics['total_reward'] / (episode + 1),
                'epsilon': self.agent.epsilon,
                'timestamp': time.time()
            }
            self.training_metrics['learning_progress'].append(progress_point)
    
    def _save_checkpoint(self, episode: int):
        """Save training checkpoint"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save enhanced model
        model_filename = f"enhanced_model_{timestamp}.pth"
        self.agent.save(model_filename)
        
        # Save training metrics
        metrics_filename = f"training_metrics_{timestamp}.json"
        with open(os.path.join("models", metrics_filename), 'w') as f:
            json.dump(self.training_metrics, f, indent=2, default=str)
        
        # Save performance data
        if self.redis_manager.redis_available:
            self.performance_monitor.save_performance_data(f"performance_{timestamp}.json")
        
        print(f"Checkpoint saved at episode {episode}")
    
    def _print_progress(self, episode: int):
        """Print training progress"""
        avg_reward = self.training_metrics['total_reward'] / (episode + 1)
        agent_metrics = self.agent.get_performance_metrics()
        
        print(f"\nEpisode {episode}:")
        print(f"  Average Reward: {avg_reward:.2f}")
        print(f"  Best Reward: {self.training_metrics['best_reward']:.2f}")
        print(f"  Epsilon: {agent_metrics['epsilon']:.3f}")
        print(f"  Memory Size: {agent_metrics['memory_size']}")
        print(f"  Avg Loss: {agent_metrics['avg_loss']:.4f}")
        print(f"  Decision Time: {self.training_metrics['avg_decision_time']:.2f}s")
        
        if self.redis_manager.redis_available:
            print(f"  Redis Status: Connected")
        else:
            print(f"  Redis Status: Fallback mode")
    
    def _save_final_model(self):
        """Save final trained model"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_model = f"final_enhanced_model_{timestamp}.pth"
        self.agent.save(final_model)
        
        # Export enhanced card database
        self.card_db.export_enhanced_cards(f"final_cards_{timestamp}.json")
        
        print(f"Final model saved as {final_model}")
    
    def _print_training_summary(self):
        """Print comprehensive training summary"""
        print("\n" + "="*50)
        print("ENHANCED TRAINING SUMMARY")
        print("="*50)
        
        total_episodes = self.training_metrics['episodes']
        avg_reward = self.training_metrics['total_reward'] / max(total_episodes, 1)
        
        print(f"Total Episodes: {total_episodes}")
        print(f"Average Reward: {avg_reward:.2f}")
        print(f"Best Reward: {self.training_metrics['best_reward']:.2f}")
        print(f"Final Epsilon: {self.agent.epsilon:.3f}")
        
        # Agent performance
        agent_metrics = self.agent.get_performance_metrics()
        print(f"\nAgent Performance:")
        print(f"  Steps Taken: {agent_metrics['steps_done']}")
        print(f"  Memory Usage: {agent_metrics['memory_size']}")
        print(f"  Average Loss: {agent_metrics['avg_loss']:.4f}")
        
        # System performance
        print(f"\nSystem Performance:")
        print(f"  Redis Available: {self.redis_manager.redis_available}")
        print(f"  Enhanced Mode: {getattr(self.env, 'enhanced_mode', False)}")
        print(f"  Cards in Database: {len(self.card_db.cards)}")
        
        # Learning progress
        if self.training_metrics['learning_progress']:
            print(f"\nLearning Progress:")
            recent_progress = self.training_metrics['learning_progress'][-5:]
            for point in recent_progress:
                print(f"  Episode {point['episode']}: {point['avg_reward']:.2f} reward")
        
        print("="*50)

class KeyboardController:
    """Keyboard controller for graceful shutdown"""
    
    def __init__(self):
        self.should_exit = False
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
    
    def on_press(self, key):
        try:
            if key.char == 'q':
                print("\nShutdown requested - will finish current episode...")
                self.should_exit = True
        except AttributeError:
            pass  # Special key pressed
    
    def is_exit_requested(self):
        return self.should_exit

def main():
    """Main training function"""
    print("Starting Enhanced Clash Royale Bot Training")
    print("Press 'q' to gracefully stop training")
    
    # Initialize training system
    training_system = EnhancedTrainingSystem()
    
    # Start training
    try:
        training_system.train(episodes=1000, save_interval=50)
    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
    except Exception as e:
        print(f"\nTraining error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Training session ended")

if __name__ == "__main__":
    main()
