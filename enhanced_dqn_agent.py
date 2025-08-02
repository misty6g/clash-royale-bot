import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import random
import numpy as np
from collections import deque, namedtuple
import time
from typing import List, Tuple, Optional, Dict

# Experience tuple for prioritized experience replay
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done', 'priority'])

class DuelingDQN(nn.Module):
    """Dueling DQN architecture for better value estimation"""
    
    def __init__(self, input_dim, output_dim, hidden_dim=128):
        super(DuelingDQN, self).__init__()
        
        # Shared feature layers
        self.feature_layer = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        # Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, output_dim)
        )
    
    def forward(self, x):
        features = self.feature_layer(x)
        
        value = self.value_stream(features)
        advantage = self.advantage_stream(features)
        
        # Combine value and advantage
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        return q_values

class PrioritizedReplayBuffer:
    """Prioritized Experience Replay buffer"""
    
    def __init__(self, capacity=50000, alpha=0.6, beta=0.4, beta_increment=0.001):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_increment = beta_increment
        self.buffer = []
        self.priorities = deque(maxlen=capacity)
        self.position = 0
        
    def add(self, state, action, reward, next_state, done, priority=None):
        if priority is None:
            priority = max(self.priorities) if self.priorities else 1.0
        
        experience = Experience(state, action, reward, next_state, done, priority)
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(priority)
        else:
            self.buffer[self.position] = experience
            self.priorities[self.position] = priority
        
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size):
        if len(self.buffer) < batch_size:
            return None
        
        # Calculate sampling probabilities
        priorities = np.array(self.priorities)
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        # Sample indices
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        
        # Calculate importance sampling weights
        weights = (len(self.buffer) * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()
        
        # Get experiences
        experiences = [self.buffer[idx] for idx in indices]
        
        # Update beta
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        return experiences, indices, weights
    
    def update_priorities(self, indices, priorities):
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority
    
    def __len__(self):
        return len(self.buffer)

class EnhancedDQNAgent:
    """Enhanced DQN Agent with advanced features"""
    
    def __init__(self, state_size, action_size, config=None):
        self.state_size = state_size
        self.action_size = action_size
        
        # Load configuration
        if config:
            self.lr = config.DQN_LEARNING_RATE
            self.gamma = config.DQN_GAMMA
            self.epsilon_decay = config.DQN_EPSILON_DECAY
        else:
            self.lr = 0.001
            self.gamma = 0.95
            self.epsilon_decay = 0.997
        
        # Enhanced parameters
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.target_update_frequency = 1000
        self.steps_done = 0
        
        # Networks
        self.q_network = DuelingDQN(state_size, action_size)
        self.target_network = DuelingDQN(state_size, action_size)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.lr)
        
        # Prioritized replay buffer
        self.memory = PrioritizedReplayBuffer()
        
        # Performance tracking
        self.loss_history = deque(maxlen=1000)
        self.reward_history = deque(maxlen=1000)
        self.action_counts = np.zeros(action_size)
        
        # Strategy components
        self.card_preferences = {}
        self.opponent_patterns = {}
        self.elixir_efficiency_tracker = {}
        
        # Update target network
        self.update_target_network()
    
    def update_target_network(self):
        """Update target network with current network weights"""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in prioritized replay buffer"""
        # Calculate TD error for priority
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)
            
            current_q = self.q_network(state_tensor)[0][action]
            next_q = self.target_network(next_state_tensor).max(1)[0]
            target_q = reward + (self.gamma * next_q * (1 - done))
            
            td_error = abs(current_q - target_q).item()
        
        self.memory.add(state, action, reward, next_state, done, td_error)
        
        # Track performance
        self.reward_history.append(reward)
        self.action_counts[action] += 1
    
    def act(self, state, available_actions=None):
        """Enhanced action selection with strategy considerations"""
        self.steps_done += 1
        
        # Epsilon-greedy with decay
        if random.random() < self.epsilon:
            if available_actions:
                return random.choice(available_actions)
            return random.randrange(self.action_size)
        
        # Neural network prediction
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.q_network(state_tensor)
        
        # Apply action masking if available actions specified
        if available_actions:
            masked_q_values = q_values.clone()
            mask = torch.ones(self.action_size) * float('-inf')
            mask[available_actions] = 0
            masked_q_values += mask
            return masked_q_values.argmax().item()
        
        return q_values.argmax().item()
    
    def strategic_act(self, state, game_context=None):
        """Strategic action selection considering game context"""
        base_action = self.act(state)
        
        if game_context is None:
            return base_action
        
        # Extract context information
        my_elixir = game_context.get('my_elixir', 10)
        enemy_elixir = game_context.get('enemy_elixir', 10)
        my_cards = game_context.get('my_cards', [])
        enemy_cards = game_context.get('enemy_cards', [])
        game_phase = game_context.get('phase', 'normal')  # normal, overtime, sudden_death
        
        # Strategic modifications
        modified_action = self._apply_strategic_rules(
            base_action, my_elixir, enemy_elixir, my_cards, enemy_cards, game_phase
        )
        
        return modified_action
    
    def _apply_strategic_rules(self, action, my_elixir, enemy_elixir, my_cards, enemy_cards, phase):
        """Apply strategic rules to modify action selection"""
        
        # Rule 1: Elixir advantage/disadvantage
        elixir_diff = my_elixir - enemy_elixir
        
        if elixir_diff < -3:  # Significant disadvantage
            # Prefer defensive/cheap cards
            return self._prefer_defensive_action(action, my_cards)
        elif elixir_diff > 3:  # Significant advantage
            # Prefer aggressive/expensive cards
            return self._prefer_aggressive_action(action, my_cards)
        
        # Rule 2: Game phase considerations
        if phase == 'overtime':
            # More aggressive in overtime
            return self._prefer_aggressive_action(action, my_cards)
        elif phase == 'sudden_death':
            # All-in strategy
            return self._prefer_highest_damage_action(action, my_cards)
        
        # Rule 3: Counter-play
        if enemy_cards:
            counter_action = self._find_counter_action(action, enemy_cards, my_cards)
            if counter_action is not None:
                return counter_action
        
        return action
    
    def _prefer_defensive_action(self, action, my_cards):
        """Prefer defensive cards when at elixir disadvantage"""
        # This would need integration with card database
        # For now, return original action
        return action
    
    def _prefer_aggressive_action(self, action, my_cards):
        """Prefer aggressive cards when at elixir advantage"""
        # This would need integration with card database
        return action
    
    def _prefer_highest_damage_action(self, action, my_cards):
        """Prefer highest damage cards in sudden death"""
        return action
    
    def _find_counter_action(self, action, enemy_cards, my_cards):
        """Find counter action against enemy cards"""
        # This would integrate with the counter strategy system
        return None
    
    def replay(self, batch_size=32):
        """Enhanced training with prioritized experience replay"""
        if len(self.memory) < batch_size:
            return
        
        # Sample from prioritized replay buffer
        sample_result = self.memory.sample(batch_size)
        if sample_result is None:
            return
        
        experiences, indices, weights = sample_result
        
        # Prepare batch data
        states = torch.FloatTensor([e.state for e in experiences])
        actions = torch.LongTensor([e.action for e in experiences])
        rewards = torch.FloatTensor([e.reward for e in experiences])
        next_states = torch.FloatTensor([e.next_state for e in experiences])
        dones = torch.BoolTensor([e.done for e in experiences])
        weights = torch.FloatTensor(weights)
        
        # Current Q values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values from target network
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # Calculate loss with importance sampling weights
        td_errors = F.mse_loss(current_q_values.squeeze(), target_q_values, reduction='none')
        weighted_loss = (td_errors * weights).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        weighted_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        # Update priorities
        new_priorities = td_errors.detach().cpu().numpy() + 1e-6
        self.memory.update_priorities(indices, new_priorities)
        
        # Track loss
        self.loss_history.append(weighted_loss.item())
        
        # Update target network periodically
        if self.steps_done % self.target_update_frequency == 0:
            self.update_target_network()
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def get_performance_metrics(self):
        """Get performance metrics for monitoring"""
        return {
            'epsilon': self.epsilon,
            'steps_done': self.steps_done,
            'avg_loss': np.mean(self.loss_history) if self.loss_history else 0,
            'avg_reward': np.mean(self.reward_history) if self.reward_history else 0,
            'memory_size': len(self.memory),
            'action_distribution': self.action_counts / max(self.action_counts.sum(), 1)
        }
    
    def save(self, filename):
        """Save model with enhanced metadata"""
        if not os.path.exists("models"):
            os.makedirs("models")
        
        model_path = os.path.join("models", filename)
        
        # Save model state and metadata
        torch.save({
            'model_state_dict': self.q_network.state_dict(),
            'target_model_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps_done': self.steps_done,
            'performance_metrics': self.get_performance_metrics()
        }, model_path)
        
        print(f"Enhanced model saved to {model_path}")
    
    def load(self, filename):
        """Load model with enhanced metadata"""
        model_path = os.path.join("models", filename) if not os.path.isabs(filename) else filename
        
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path)
            
            self.q_network.load_state_dict(checkpoint['model_state_dict'])
            self.target_network.load_state_dict(checkpoint['target_model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.epsilon = checkpoint.get('epsilon', self.epsilon)
            self.steps_done = checkpoint.get('steps_done', 0)
            
            print(f"Enhanced model loaded from {model_path}")
            print(f"Loaded state: epsilon={self.epsilon}, steps={self.steps_done}")
        else:
            print(f"Model file {model_path} not found")
