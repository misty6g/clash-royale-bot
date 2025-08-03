import numpy as np
import time
import os
import pyautogui
import threading
from typing import List
from Actions import Actions
from inference_sdk import InferenceHTTPClient

# Import enhanced vision system
try:
    from enhanced_vision_system import EnhancedVisionSystem, GameState, GamePhase
    ENHANCED_VISION_AVAILABLE = True
except ImportError:
    print("Enhanced vision system not available, using legacy detection")
    ENHANCED_VISION_AVAILABLE = False

MAX_ENEMIES = 10
MAX_ALLIES = 10

SPELL_CARDS = ["Fireball", "Zap", "Arrows", "Tornado", "Rocket", "Lightning", "Freeze"]

class ClashRoyaleEnv:
    def __init__(self):
        self.actions = Actions()
        self.rf_model = self.setup_roboflow()
        self.card_model = self.setup_card_roboflow()
        self.state_size = 1 + 2 * (MAX_ALLIES + MAX_ENEMIES)

        self.num_cards = 4
        self.grid_width = 18
        self.grid_height = 28

        self.screenshot_path = os.path.join(os.path.dirname(__file__), 'screenshots', "current.png")
        self.available_actions = self.get_available_actions()
        self.action_size = len(self.available_actions)
        self.current_cards = []

        self.game_over_flag = None
        self._endgame_thread = None
        self._endgame_thread_stop = threading.Event()

        self.prev_elixir = None
        self.prev_enemy_presence = None

        self.prev_enemy_princess_towers = None

        self.match_over_detected = False

        # ADD: Enhanced mode initialization
        self.enhanced_mode = False
        self.enhanced_vision = None

        try:
            from config import BotConfig
            self.config = BotConfig()

            # Initialize enhanced vision system
            if ENHANCED_VISION_AVAILABLE:
                try:
                    from platform_manager import PlatformManager
                    self.platform_manager = PlatformManager()
                    self.platform_manager.find_emulator_window()

                    self.enhanced_vision = EnhancedVisionSystem(self.platform_manager)
                    print("Enhanced vision system initialized")
                except Exception as e:
                    print(f"Enhanced vision initialization failed: {e}")
                    self.enhanced_vision = None

            if self.config.ENABLE_REDIS:
                from redis_card_manager import RedisCardManager
                self.redis_manager = RedisCardManager(self.config)
                if self.redis_manager.redis_available:
                    self.redis_manager.load_cards_from_json('cards.json')
                    self.enhanced_mode = True
                    print("Enhanced mode enabled with Redis")
                else:
                    print("Redis unavailable, staying in legacy mode")
        except Exception as e:
            print(f"Enhanced features initialization failed: {e}")
            print("Continuing in legacy mode")
            self.enhanced_mode = False

        # Initialize other components only if Redis is working
        if self.enhanced_mode:
            try:
                if self.config.ENABLE_LEARNING:
                    from card_learning_system import CardLearningSystem
                    self.learning_system = CardLearningSystem(self.redis_manager)

                if self.config.ENABLE_OPPONENT_TRACKING:
                    from opponent_tracker import OpponentTracker
                    self.opponent_tracker = OpponentTracker(self.redis_manager)

                if self.config.ENABLE_COUNTER_STRATEGY:
                    from counter_strategy import CounterStrategy
                    self.counter_strategy = CounterStrategy(self.redis_manager,
                                                          getattr(self, 'opponent_tracker', None))

                from performance_monitor import PerformanceMonitor
                self.performance_monitor = PerformanceMonitor()

            except Exception as e:
                print(f"Enhanced components initialization failed: {e}")
                self.enhanced_mode = False

    def setup_roboflow(self):
        return InferenceHTTPClient(
            api_url="http://localhost:9001",
            api_key="zt3zjKAX2eYuIBGrLDJu"
        )

    def setup_card_roboflow(self):
        return InferenceHTTPClient(
            api_url="http://localhost:9001",
            api_key="zt3zjKAX2eYuIBGrLDJu"
        )

    def reset(self):
        # self.actions.click_battle_start()
        # Instead, just wait for the new game to load after clicking "Play Again"
        time.sleep(3)
        self.game_over_flag = None
        self._endgame_thread_stop.clear()
        self._endgame_thread = threading.Thread(target=self._endgame_watcher, daemon=True)
        self._endgame_thread.start()
        self.prev_elixir = None
        self.prev_enemy_presence = None
        self.prev_enemy_princess_towers = self._count_enemy_princess_towers()
        self.match_over_detected = False
        return self._get_state()

    def close(self):
        self._endgame_thread_stop.set()
        if self._endgame_thread:
            self._endgame_thread.join()

    def step(self, action_index):
        # Check for match over
        if not self.match_over_detected and hasattr(self.actions, "detect_match_over") and self.actions.detect_match_over():
            print("Match over detected (matchover.png), forcing no-op until next game.")
            self.match_over_detected = True

        # If match over, only allow no-op action (last action in list)
        if self.match_over_detected:
            action_index = len(self.available_actions) - 1  # No-op action

        if self.game_over_flag:
            done = True
            reward = self._compute_reward(self._get_state())
            result = self.game_over_flag
            if result == "victory":
                reward += 100
                print("Victory detected - ending episode")
            elif result == "defeat":
                reward -= 100
                print("Defeat detected - ending episode")
            self.match_over_detected = False  # Reset for next episode
            return self._get_state(), reward, done

        self.current_cards = self.detect_cards_in_hand()
        print("\nCurrent cards in hand:", self.current_cards)

        # If all cards are "Unknown", use smart strategy with assumed cards
        if all(card == "Unknown" for card in self.current_cards):
            print("All cards are Unknown, using SMART strategy with assumed cards.")
            return self._play_smart_strategy_with_unknown_cards()

        # If we can detect cards, use SMART strategy instead of DQN
        print("🎯 Cards detected! Using SMART card-aware strategy...")
        return self._play_smart_card_aware_strategy()

        # OLD DQN strategy (disabled for now)
        # action = self.available_actions[action_index]
        # card_index, x_frac, y_frac = action
        # print(f"Action selected: card_index={card_index}, x_frac={x_frac:.2f}, y_frac={y_frac:.2f}")

        spell_penalty = 0

        if card_index != -1 and card_index < len(self.current_cards):
            card_name = self.current_cards[card_index]
            print(f"Attempting to play {card_name}")
            x = int(x_frac * self.actions.WIDTH) + self.actions.TOP_LEFT_X
            y = int(y_frac * self.actions.HEIGHT) + self.actions.TOP_LEFT_Y
            self.actions.card_play(x, y, card_index)
            time.sleep(1)  # You can reduce this if needed

            # --- Spell penalty logic ---
            if card_name in SPELL_CARDS:
                state = self._get_state()
                enemy_positions = []
                for i in range(1 + 2 * MAX_ALLIES, 1 + 2 * MAX_ALLIES + 2 * MAX_ENEMIES, 2):
                    ex = state[i]
                    ey = state[i + 1]
                    if ex != 0.0 or ey != 0.0:
                        ex_px = int(ex * self.actions.WIDTH)
                        ey_px = int(ey * self.actions.HEIGHT)
                        enemy_positions.append((ex_px, ey_px))
                radius = 100
                found_enemy = any((abs(ex - x) ** 2 + abs(ey - y) ** 2) ** 0.5 < radius for ex, ey in enemy_positions)
                if not found_enemy:
                    spell_penalty = -5  # Penalize for wasting spell

        # --- Princess tower reward logic ---
        current_enemy_princess_towers = self._count_enemy_princess_towers()
        princess_tower_reward = 0
        if self.prev_enemy_princess_towers is not None:
            if current_enemy_princess_towers < self.prev_enemy_princess_towers:
                princess_tower_reward = 20
        self.prev_enemy_princess_towers = current_enemy_princess_towers

        done = False
        reward = self._compute_reward(self._get_state()) + spell_penalty + princess_tower_reward
        next_state = self._get_state()
        return next_state, reward, done

    def _get_state(self):
        """Enhanced state detection using new vision system"""
        try:
            # Use enhanced vision system if available
            if self.enhanced_vision:
                game_state = self.enhanced_vision.get_complete_game_state()
                return self._convert_game_state_to_vector(game_state)

            # Fallback to legacy state detection
            return self._legacy_get_state()

        except Exception as e:
            print(f"Error getting state: {e}")
            return self._legacy_get_state()

    def _convert_game_state_to_vector(self, game_state) -> np.ndarray:
        """Convert enhanced game state to vector format"""
        try:
            # Start with elixir (normalized)
            elixir = game_state.my_elixir / 10.0

            # Extract unit positions from enhanced game state
            allies = []
            enemies = []

            for unit in game_state.units_on_field:
                if unit.get('team') == 'ally':
                    pos = unit.get('position', (0, 0))
                    allies.append(pos)
                else:
                    pos = unit.get('position', (0, 0))
                    enemies.append(pos)

            # Normalize and pad positions (same format as legacy)
            def normalize(units):
                return [(x / self.actions.WIDTH, y / self.actions.HEIGHT) for x, y in units]

            def pad_units(units, max_units):
                units = normalize(units)
                if len(units) < max_units:
                    units += [(0.0, 0.0)] * (max_units - len(units))
                return units[:max_units]

            ally_positions = pad_units(allies, MAX_ALLIES)
            enemy_positions = pad_units(enemies, MAX_ENEMIES)

            # Flatten positions
            ally_flat = [coord for pos in ally_positions for coord in pos]
            enemy_flat = [coord for pos in enemy_positions for coord in pos]

            state = np.array([elixir] + ally_flat + enemy_flat, dtype=np.float32)
            return state

        except Exception as e:
            print(f"Error converting game state to vector: {e}")
            return self._legacy_get_state()

    def _legacy_get_state(self):
        """Legacy state detection method"""
        try:
            self.actions.capture_area(self.screenshot_path)
            elixir = self.actions.count_elixir()

            try:
                results = self.rf_model.run_workflow(
                    workspace_name="clash-royale-tgua7",
                    workflow_id="detect-count-and-visualize",
                    images={"image": self.screenshot_path}
                )
            except ConnectionError as e:
                print(f"Roboflow server not available, using fallback state: {e}")
                # Return a basic fallback state
                default_state = [elixir / 10.0]  # Normalized elixir
                default_state.extend([0, 0] * (MAX_ALLIES + MAX_ENEMIES))
                return np.array(default_state, dtype=np.float32)

            print("RAW results:", results)

            # Handle new structure: dict with "predictions" key
            predictions = []
            if isinstance(results, dict) and "predictions" in results:
                predictions = results["predictions"]
            elif isinstance(results, list) and results:
                first = results[0]
                if isinstance(first, dict) and "predictions" in first:
                    predictions = first["predictions"]
            print("Predictions:", predictions)
            if not predictions:
                print("WARNING: No predictions found in results")
                return None

            # After getting 'predictions' from results:
            if isinstance(predictions, dict) and "predictions" in predictions:
                predictions = predictions["predictions"]

            print("RAW predictions:", predictions)
            print("Detected classes:", [repr(p.get("class", "")) for p in predictions if isinstance(p, dict)])

            TOWER_CLASSES = {
                "ally king tower",
                "ally princess tower",
                "enemy king tower",
                "enemy princess tower"
            }

            def normalize_class(cls):
                return cls.strip().lower() if isinstance(cls, str) else ""

            allies = [
                (p["x"], p["y"])
                for p in predictions
                if (
                    isinstance(p, dict)
                    and normalize_class(p.get("class", "")) not in TOWER_CLASSES
                    and normalize_class(p.get("class", "")).startswith("ally")
                    and "x" in p and "y" in p
                )
            ]

            enemies = [
                (p["x"], p["y"])
                for p in predictions
                if (
                    isinstance(p, dict)
                    and normalize_class(p.get("class", "")) not in TOWER_CLASSES
                    and normalize_class(p.get("class", "")).startswith("enemy")
                    and "x" in p and "y" in p
                )
            ]

            print("Allies:", allies)
            print("Enemies:", enemies)

            # Normalize positions
            def normalize(units):
                return [(x / self.actions.WIDTH, y / self.actions.HEIGHT) for x, y in units]

            # Pad or truncate to fixed length
            def pad_units(units, max_units):
                units = normalize(units)
                if len(units) < max_units:
                    units += [(0.0, 0.0)] * (max_units - len(units))
                return units[:max_units]

            ally_positions = pad_units(allies, MAX_ALLIES)
            enemy_positions = pad_units(enemies, MAX_ENEMIES)

            # Flatten positions
            ally_flat = [coord for pos in ally_positions for coord in pos]
            enemy_flat = [coord for pos in enemy_positions for coord in pos]

            state = np.array([elixir / 10.0] + ally_flat + enemy_flat, dtype=np.float32)
            return state

        except Exception as e:
            print(f"Error in legacy state detection: {e}")
            # Return default state
            default_state = [5.0]  # Default elixir
            default_state.extend([0, 0] * (MAX_ALLIES + MAX_ENEMIES))
            return np.array(default_state, dtype=np.float32)

    def _compute_reward(self, state):
        if state is None:
            return 0

        elixir = state[0] * 10

        # Sum all enemy positions (not just the first)
        enemy_positions = state[1 + 2 * MAX_ALLIES:]  # All enemy x1, y1, x2, y2, ...
        enemy_presence = sum(enemy_positions)

        reward = -enemy_presence

        # Elixir efficiency: reward for spending elixir if it reduces enemy presence
        if self.prev_elixir is not None and self.prev_enemy_presence is not None:
            elixir_spent = self.prev_elixir - elixir
            enemy_reduced = self.prev_enemy_presence - enemy_presence
            if elixir_spent > 0 and enemy_reduced > 0:
                reward += 2 * min(elixir_spent, enemy_reduced)  # tune this factor

        self.prev_elixir = elixir
        self.prev_enemy_presence = enemy_presence

        return reward

    def _play_smart_strategy_with_unknown_cards(self):
        """Smart strategy using DQN agent even when cards are unknown"""
        try:
            # Get current game state for AI decision making
            current_state = self._get_state()

            # Use DQN agent to choose optimal action if available
            if hasattr(self, 'agent') and self.agent is not None:
                print("🧠 Using DQN Agent for smart decision making...")
                action = self.agent.act(current_state)
                print(f"🎯 DQN Agent chose action: {action}")
            else:
                # Use enhanced action selection system
                print("🎯 Using enhanced action selection system...")
                action = self.choose_optimal_action(current_state, ["Unknown"] * 4)
                print(f"🎯 Enhanced system chose action: {action}")

            # Convert action to card selection and placement
            card_index, placement_x, placement_y = self._action_to_card_and_position(action)

            # Calculate card positions based on BlueStacks coordinates
            card_area_left = 1250
            card_area_width = 450  # 1700 - 1250
            card_width = card_area_width // 4  # 4 cards
            card_y = 940  # Middle of card area

            card_x = card_area_left + (card_index * card_width) + (card_width // 2)

            print(f"🎮 SMART: Selecting card {card_index} at position ({card_x}, {card_y})")

            # Click on the card to select it
            pyautogui.moveTo(card_x, card_y, duration=0.1)
            pyautogui.click()
            time.sleep(0.2)  # Wait for card selection

            print(f"🎯 SMART: Placing card at strategic position ({placement_x}, {placement_y})")

            # Click to place the card at the strategic position
            pyautogui.moveTo(placement_x, placement_y, duration=0.2)
            pyautogui.click()

            # Get next state and return with higher reward for smart play
            next_state = self._get_state()
            reward = 5  # Higher reward for using smart strategy
            return next_state, reward, False

        except Exception as e:
            print(f"Error in smart strategy: {e}")
            # Fall back to simple strategy if smart strategy fails
            return self._play_fallback_card_strategy()

    def _action_to_card_and_position(self, action):
        """Convert DQN action to card index and battlefield position"""
        try:
            # Action space: card_index * (grid_width * grid_height) + position_offset
            total_positions = self.grid_width * self.grid_height

            card_index = action // total_positions
            position_offset = action % total_positions

            # Convert position offset to grid coordinates
            grid_x = position_offset % self.grid_width
            grid_y = position_offset // self.grid_width

            # Convert grid coordinates to screen coordinates
            # Game area: (1218, 72, 1756, 1004)
            game_left, game_top = 1218, 72
            game_width, game_height = 538, 932

            # Map grid to screen coordinates
            screen_x = game_left + int((grid_x / self.grid_width) * game_width)
            screen_y = game_top + int((grid_y / self.grid_height) * game_height)

            # Ensure we're placing on our side (bottom half)
            if screen_y < game_top + game_height // 2:
                screen_y = game_top + game_height // 2 + 50  # Force to our side

            # Clamp card index to valid range
            card_index = max(0, min(3, card_index))

            return card_index, screen_x, screen_y

        except Exception as e:
            print(f"Error converting action: {e}")
            # Return safe defaults
            import random
            return random.randint(0, 3), random.randint(1300, 1650), random.randint(600, 800)

    def _play_fallback_card_strategy(self):
        """Simple fallback strategy when smart strategy fails"""
        try:
            # Calculate card positions based on BlueStacks coordinates
            card_area_left = 1250
            card_area_width = 450  # 1700 - 1250
            card_width = card_area_width // 4  # 4 cards
            card_y = 940  # Middle of card area (900 + 40)

            # Select a random card (0-3)
            import random
            card_index = random.randint(0, 3)
            card_x = card_area_left + (card_index * card_width) + (card_width // 2)

            print(f"💡 FALLBACK: Selecting card {card_index} at position ({card_x}, {card_y})")

            # Click on the card to select it
            pyautogui.moveTo(card_x, card_y, duration=0.1)
            pyautogui.click()
            time.sleep(0.2)  # Wait for card selection

            # Now place the card on the battlefield
            battlefield_x = random.randint(1300, 1650)  # Random x in our territory
            battlefield_y = random.randint(600, 800)    # Our side of battlefield

            print(f"💡 FALLBACK: Placing card at battlefield position ({battlefield_x}, {battlefield_y})")

            # Click to place the card
            pyautogui.moveTo(battlefield_x, battlefield_y, duration=0.2)
            pyautogui.click()

            # Get next state and return
            next_state = self._get_state()
            reward = 1  # Small positive reward for actually playing a card
            return next_state, reward, False

        except Exception as e:
            print(f"Error in fallback strategy: {e}")
            # If fallback fails, just return current state
            next_state = self._get_state()
            return next_state, 0, False

    def _play_smart_card_aware_strategy(self):
        """Smart strategy that uses actual detected cards for intelligent decisions"""
        try:
            print(f"🎴 Available cards: {self.current_cards}")

            # 👁️ DETECT ENEMIES on battlefield
            enemy_units = self.detect_enemy_cards()
            if enemy_units:
                print(f"👁️ Enemy units detected: {enemy_units}")
            else:
                print("👁️ No enemy units detected on battlefield")

            # Analyze cards and choose the best one based on strategy and threats
            card_to_play, reason = self._choose_best_card(self.current_cards, enemy_units)

            if card_to_play == -1:
                print("🤔 No good card to play right now, waiting...")
                next_state = self._get_state()
                return next_state, 0, False

            # Choose strategic placement based on card type and game state
            placement_x, placement_y = self._choose_strategic_placement(self.current_cards[card_to_play])

            print(f"🎯 SMART DECISION: Playing {self.current_cards[card_to_play]} because {reason}")
            print(f"🎯 STRATEGIC PLACEMENT: Position ({placement_x}, {placement_y})")

            # Execute the move
            self.actions.card_play(placement_x, placement_y, card_to_play)

            # 🔄 UPDATE HAND after playing card
            time.sleep(0.5)  # Wait for card to be played and hand to update
            self.current_cards = self.detect_cards_in_hand()
            print(f"🔄 Hand updated after playing card: {self.current_cards}")

            # Get next state and return with reward based on card choice quality
            next_state = self._get_state()
            reward = self._calculate_card_play_reward(self.current_cards[card_to_play] if card_to_play < len(self.current_cards) else "Unknown", reason)
            return next_state, reward, False

        except Exception as e:
            print(f"Error in smart card-aware strategy: {e}")
            # Fall back to simple strategy if smart strategy fails
            return self._play_fallback_card_strategy()

    def _choose_best_card(self, cards, enemy_units=None):
        """Choose the best card to play based on dynamic game strategy and enemy threats"""
        try:
            import random

            # Card categorization
            tank_cards = ["Giant", "Golem", "Lava Hound", "P.E.K.K.A", "Mega Knight"]
            support_cards = ["Wizard", "Musketeer", "Archers", "Minions", "Electro Wizard"]
            swarm_cards = ["Skeleton Army", "Goblins", "Minion Horde", "Barbarians"]
            spell_cards = ["Fireball", "Lightning", "Arrows", "Zap", "Rocket"]
            building_cards = ["Inferno Tower", "Tesla", "Cannon", "Bomb Tower"]
            cheap_cards = ["Knight", "Archers", "Goblins", "Skeletons", "Ice Spirit"]

            # Create a weighted strategy that varies choices
            available_cards = []
            for i, card in enumerate(cards):
                if card != "Unknown":
                    available_cards.append((i, card))

            if not available_cards:
                return -1, "no playable cards"

            # 🎯 REACTIVE STRATEGY: Counter enemy units if detected
            if enemy_units:
                counter_card = self._find_counter_card(available_cards, enemy_units)
                if counter_card is not None:
                    return counter_card, f"counter to enemy {enemy_units[0]}"

            # Dynamic strategy based on randomness and card types
            strategy_roll = random.randint(1, 100)

            if strategy_roll <= 30:  # 30% - Aggressive tank push
                for i, card in available_cards:
                    if card in tank_cards:
                        return i, f"tank unit for aggressive push"

            elif strategy_roll <= 55:  # 25% - Support/ranged attack
                for i, card in available_cards:
                    if card in support_cards:
                        return i, f"support unit for ranged attack"

            elif strategy_roll <= 75:  # 20% - Swarm pressure
                for i, card in available_cards:
                    if card in swarm_cards:
                        return i, f"swarm unit for quick pressure"

            elif strategy_roll <= 85:  # 10% - Cheap cycle
                for i, card in available_cards:
                    if card in cheap_cards:
                        return i, f"cheap unit for cycle"

            elif strategy_roll <= 95:  # 10% - Defensive play
                for i, card in available_cards:
                    if card in building_cards:
                        return i, f"defensive building"

            else:  # 5% - Spell/utility
                for i, card in available_cards:
                    if card in spell_cards:
                        return i, f"spell for area damage"

            # If strategy doesn't find a card, pick randomly from available
            random_choice = random.choice(available_cards)
            return random_choice[0], f"random strategic choice"

        except Exception as e:
            print(f"Error choosing best card: {e}")
            return 0, "fallback choice"

    def _choose_strategic_placement(self, card_name):
        """Choose strategic placement based on card type"""
        try:
            # Game area: (1218, 72, 1756, 1004)
            game_left, game_top = 1218, 72
            game_width, game_height = 538, 932

            # Our side is bottom half
            our_side_top = game_top + game_height // 2
            our_side_bottom = game_top + game_height

            tank_cards = ["Giant", "Golem", "Lava Hound", "P.E.K.K.A", "Mega Knight", "giant", "golem", "lava hound", "p.e.k.k.a", "mega knight"]
            support_cards = ["Wizard", "Musketeer", "Archers", "Minions", "Electro Wizard", "wizard", "musketeer", "archers", "minions", "electro wizard", "firecracker", "bomber"]
            swarm_cards = ["Skeleton Army", "Goblins", "Minion Horde", "Barbarians", "skeleton army", "goblins", "minion horde", "barbarians", "spear goblins"]

            import random

            if card_name in tank_cards:
                # Place tanks at the back for a slow push
                x = game_left + game_width // 2  # Center
                y = our_side_bottom - 100  # Back of our territory
                return x, y

            elif card_name in support_cards:
                # Place support behind tanks, slightly to the side
                x = game_left + random.randint(game_width//4, 3*game_width//4)
                y = our_side_bottom - 150  # Behind tanks
                return x, y

            elif card_name in swarm_cards:
                # Place swarms at the bridge for quick pressure
                x = game_left + random.randint(game_width//3, 2*game_width//3)
                y = our_side_top + 50  # Near the bridge
                return x, y

            else:
                # Default placement - center of our territory
                x = game_left + game_width // 2
                y = our_side_top + game_height // 4
                return x, y

        except Exception as e:
            print(f"Error choosing strategic placement: {e}")
            # Safe fallback position
            return 1400, 700

    def _calculate_card_play_reward(self, card_name, reason):
        """Calculate reward based on the quality of the card choice"""
        base_reward = 2  # Base reward for playing any card

        # Bonus rewards for good strategic choices
        if "tank" in reason:
            return base_reward + 3  # Tanks are good for building pushes
        elif "support" in reason:
            return base_reward + 2  # Support is good for offense
        elif "defensive" in reason:
            return base_reward + 2  # Defense is important
        elif "swarm" in reason:
            return base_reward + 1  # Swarms provide pressure
        else:
            return base_reward

    def _find_counter_card(self, available_cards, enemy_units):
        """Find the best counter card for detected enemy units"""
        try:
            # Counter strategies based on Clash Royale meta
            counters = {
                "Giant": ["Skeleton Army", "Minion Horde", "Inferno Tower", "P.E.K.K.A"],
                "Wizard": ["Knight", "Fireball", "Lightning", "Rocket"],
                "Minions": ["Arrows", "Zap", "Wizard", "Archers"],
                "Barbarians": ["Fireball", "Wizard", "Valkyrie", "Bomb Tower"],
                "Hog Rider": ["Cannon", "Tesla", "Skeleton Army", "Tombstone"],
                "Balloon": ["Musketeer", "Archers", "Tesla", "Inferno Tower"]
            }

            # Find first enemy unit we can counter
            for enemy_unit in enemy_units:
                if enemy_unit in counters:
                    counter_cards = counters[enemy_unit]
                    # Find first available counter card
                    for i, (card_idx, card_name) in enumerate(available_cards):
                        if card_name in counter_cards:
                            print(f"🎯 COUNTER STRATEGY: {card_name} vs enemy {enemy_unit}")
                            return card_idx

            return None

        except Exception as e:
            print(f"Error finding counter card: {e}")
            return None



    def detect_cards_in_hand(self):
        """Enhanced card detection using Roboflow"""
        try:
            # Use legacy Roboflow detection as primary method
            cards = self._legacy_detect_cards_in_hand()
            if cards and not all(card == "Unknown" for card in cards):
                print(f"Roboflow detected cards: {cards}")
                return cards

            # Use enhanced vision system if available as backup
            if self.enhanced_vision:
                cards = self.enhanced_vision.detect_cards_in_hand()
                print(f"Enhanced vision detected cards: {cards}")
                if cards and not all(card == "Unknown" for card in cards):
                    return cards

            # Final fallback to unknown cards
            print("⚠️ No cards detected, using Unknown placeholders")
            return ["Unknown"] * 4

        except Exception as e:
            print(f"Error in detect_cards_in_hand: {e}")
            return ["Unknown"] * 4

    def _legacy_detect_cards_in_hand(self):
        """Legacy card detection method"""
        try:
            card_paths = self.actions.capture_individual_cards()
            print("\nTesting individual card predictions:")

            cards = []
            for card_path in card_paths:
                results = self.card_model.run_workflow(
                    workspace_name="clash-royale-tgua7",
                    workflow_id="custom-workflow",
                    images={"image": card_path}
                )
                # print("Card detection raw results:", results)  # Debug print

                # Fix: parse nested structure
                predictions = []
                if isinstance(results, list) and results:
                    preds_dict = results[0].get("predictions", {})
                    if isinstance(preds_dict, dict):
                        predictions = preds_dict.get("predictions", [])
                if predictions:
                    card_name = predictions[0]["class"]
                    print(f"Detected card: {card_name}")
                    cards.append(card_name)
                else:
                    print("No card detected.")
                    cards.append("Unknown")
            return cards
        except Exception as e:
            print(f"Error in legacy card detection: {e}")
            return ["Unknown"] * 4

    def detect_enemy_cards(self) -> List[str]:
        """Detect enemy cards currently on the battlefield"""
        try:
            # Use enhanced vision system if available
            if hasattr(self, 'enhanced_vision') and self.enhanced_vision:
                print("🔍 Using enhanced vision system for battlefield detection")
                units = self.enhanced_vision.detect_units_on_field()
                enemy_cards = []

                for unit in units:
                    # Filter for enemy units based on position
                    x = unit.get('x', 0)
                    y = unit.get('y', 0)
                    if self._is_enemy_position(x, y):
                        enemy_cards.append(unit.get('class', 'Unknown'))
                        print(f"🎯 Enhanced vision detected ENEMY: {unit.get('class')} at ({x}, {y})")

                if enemy_cards:
                    return enemy_cards
                print("👁️ Enhanced vision: No enemy units detected")

            # Fallback to Roboflow workflow
            screenshot_path = self.screenshot_path

            # Try the battlefield detection workflow first
            try:
                results = self.rf_model.run_workflow(
                    workspace_name="clash-royale-tgua7",
                    workflow_id="detect-count-and-visualize",
                    images={"image": screenshot_path}
                )
            except Exception as workflow_error:
                print(f"🔍 Battlefield workflow failed, trying direct inference: {workflow_error}")
                # Fallback to direct inference
                results = self.rf_model.infer(screenshot_path)

            enemy_cards = []
            print(f"🔍 Enemy detection raw results type: {type(results)}")

            # Handle different result structures
            predictions = []

            # Handle workflow response structure
            if isinstance(results, list) and len(results) > 0:
                main_result = results[0]
                if isinstance(main_result, dict):
                    count_objects = main_result.get('count_objects', 0)
                    print(f"🔍 Objects detected by workflow: {count_objects}")

                    if count_objects == 0:
                        print("👁️ No units detected on battlefield (count_objects = 0)")
                        return []

                    # Look for predictions in different keys
                    for key in ['predictions', 'detections', 'objects', 'results']:
                        if key in main_result:
                            predictions = main_result[key]
                            print(f"🔍 Found {len(predictions)} predictions in '{key}' field")
                            break

            # Handle direct inference response structure
            elif hasattr(results, 'predictions'):
                predictions = results.predictions
                print(f"🔍 Direct inference found {len(predictions)} predictions")

            # Handle dict response
            elif isinstance(results, dict) and 'predictions' in results:
                predictions = results['predictions']
                print(f"🔍 Dict response found {len(predictions)} predictions")

            # Process predictions and filter for enemy territory
            for i, prediction in enumerate(predictions):
                try:
                    # Handle different prediction formats
                    if hasattr(prediction, 'confidence'):
                        # Roboflow prediction object
                        confidence = prediction.confidence
                        card_name = prediction.class_name
                        x = prediction.x
                        y = prediction.y
                    elif isinstance(prediction, dict):
                        # Dict prediction
                        confidence = prediction.get('confidence', 0)
                        card_name = (prediction.get('class_name') or
                                   prediction.get('class') or
                                   prediction.get('label', ''))
                        x = prediction.get('x', 0)
                        y = prediction.get('y', 0)
                    else:
                        print(f"🔍 Skipping unknown prediction format: {type(prediction)}")
                        continue

                    # Filter by confidence and position
                    if confidence > 0.3:  # Even lower threshold for battlefield detection
                        # Check if unit is in enemy territory
                        if self._is_enemy_position(x, y):
                            enemy_cards.append(card_name)
                            print(f"🎯 Detected ENEMY unit: {card_name} at ({x}, {y}) confidence: {confidence:.2f}")
                        else:
                            print(f"🔵 Detected ALLY unit: {card_name} at ({x}, {y}) confidence: {confidence:.2f}")

                except Exception as pred_error:
                    print(f"Error processing prediction {i}: {pred_error}")
                    continue

            if not enemy_cards:
                print("👁️ No enemy units detected on battlefield")

            return enemy_cards

        except Exception as e:
            print(f"Error detecting enemy cards: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _is_enemy_position(self, x: float, y: float) -> bool:
        """Determine if detected card is in enemy territory"""
        try:
            # Get actual game area coordinates
            if hasattr(self, 'platform_manager') and self.platform_manager.detected_emulator:
                # Use emulator-specific coordinates
                config = self.platform_manager.detected_emulator['config']
                game_area = config.get('game_area', (0, 0, 1920, 1080))
                game_left, game_top, game_right, game_bottom = game_area

                # Calculate middle of the battlefield (bridge area)
                bridge_y = game_top + (game_bottom - game_top) * 0.5

                # Enemy territory is upper half (y < bridge_y)
                return y < bridge_y
            else:
                # Fallback: Use default screen coordinates
                # Assuming 1920x1080 screen, enemy territory is upper half
                screen_height = 1080
                bridge_y = screen_height * 0.5
                return y < bridge_y

        except Exception as e:
            print(f"Error in _is_enemy_position: {e}")
            # Safe fallback - assume upper half is enemy territory
            return y < 540  # Default for 1080p screen

    def choose_optimal_action(self, state, my_hand: List[str] = None) -> int:
        """Enhanced action selection with fallback to existing behavior"""
        # CRITICAL: Always preserve existing DQN behavior as primary
        base_action = 0  # Default action if no agent available

        # Only use enhanced features if explicitly enabled and working
        if not self.enhanced_mode or not hasattr(self, 'counter_strategy'):
            return base_action

        try:
            # Get current hand if not provided
            if my_hand is None:
                my_hand = self.detect_cards_in_hand()
                if not my_hand:
                    return base_action

            # Quick check for immediate threats (with timeout)
            start_time = time.time()
            enemy_cards = self.detect_enemy_cards()

            if (time.time() - start_time) * 1000 > self.config.MAX_DECISION_TIME_MS / 2:
                print("Enemy detection too slow, using base action")
                return base_action

            # Try counter strategy with remaining time budget
            if enemy_cards and hasattr(self, 'counter_strategy'):
                for enemy_card in enemy_cards:
                    if (time.time() - start_time) * 1000 > self.config.MAX_DECISION_TIME_MS:
                        break

                    best_counter = self.counter_strategy.get_best_counter(enemy_card, my_hand)
                    if best_counter:
                        counter_action = self.card_to_action_index(best_counter)
                        print(f"Counter strategy: {best_counter} vs {enemy_card}")
                        return counter_action

            # Always fall back to existing DQN decision
            return base_action

        except Exception as e:
            print(f"Enhanced action selection failed: {e}, using base action")
            return base_action

    def card_to_action_index(self, card_name: str) -> int:
        """Convert card name to action index using existing action space"""
        try:
            # Build on existing get_available_actions() method
            if card_name in self.current_cards:
                card_position = self.current_cards.index(card_name)
                # Use existing action space structure from env.py
                # Actions are already defined in get_available_actions()
                base_action = card_position * (self.grid_width * self.grid_height)
                # Add center placement as default (existing grid center logic)
                center_x, center_y = self.grid_width // 2, self.grid_height // 2
                placement_offset = center_y * self.grid_width + center_x
                return base_action + placement_offset
            return 0  # Default to first action in existing action space
        except Exception as e:
            print(f"Error in card_to_action_index: {e}")
            return 0

    def get_available_actions(self):
        """Generate all possible actions"""
        actions = [
            [card, x / (self.grid_width - 1), y / (self.grid_height - 1)]
            for card in range(self.num_cards)
            for x in range(self.grid_width)
            for y in range(self.grid_height)
        ]
        actions.append([-1, 0, 0])  # No-op action
        return actions

    def _endgame_watcher(self):
        while not self._endgame_thread_stop.is_set():
            result = self.actions.detect_game_end()
            if result:
                self.game_over_flag = result
                break
            # Sleep a bit to avoid hammering the CPU
            time.sleep(0.5)

    def _count_enemy_princess_towers(self):
        try:
            self.actions.capture_area(self.screenshot_path)
            results = self.rf_model.run_workflow(
                workspace_name="clash-royale-tgua7",
                workflow_id="detect-count-and-visualize",
                images={"image": self.screenshot_path}
            )
            predictions = []
            if isinstance(results, dict) and "predictions" in results:
                predictions = results["predictions"]
            elif isinstance(results, list) and results:
                first = results[0]
                if isinstance(first, dict) and "predictions" in first:
                    predictions = first["predictions"]
            return sum(1 for p in predictions if isinstance(p, dict) and p.get("class") == "enemy princess tower")
        except ConnectionError as e:
            print(f"Roboflow server not available for tower counting, using default: {e}")
            return 2  # Default assumption: 2 enemy princess towers
        except Exception as e:
            print(f"Error counting enemy princess towers: {e}")
            return 2  # Default assumption
