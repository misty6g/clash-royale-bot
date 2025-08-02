import numpy as np
import time
import os
import pyautogui
import threading
from typing import List
from Actions import Actions
from inference_sdk import InferenceHTTPClient

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
        try:
            from config import BotConfig
            self.config = BotConfig()
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
            api_key="########"
        )

    def setup_card_roboflow(self):
        return InferenceHTTPClient(
            api_url="http://localhost:9001",
            api_key="########"
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

        # If all cards are "Unknown", click at (1611, 831) and return no-op
        if all(card == "Unknown" for card in self.current_cards):
            print("All cards are Unknown, clicking at (1611, 831) and skipping move.")
            pyautogui.moveTo(1611, 831, duration=0.2)
            pyautogui.click()
            # Return current state, zero reward, not done
            next_state = self._get_state()
            return next_state, 0, False

        action = self.available_actions[action_index]
        card_index, x_frac, y_frac = action
        print(f"Action selected: card_index={card_index}, x_frac={x_frac:.2f}, y_frac={y_frac:.2f}")

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
        self.actions.capture_area(self.screenshot_path)
        elixir = self.actions.count_elixir()
        results = self.rf_model.run_workflow(
            workspace_name="workspace-mck69",
            workflow_id="detect-count-and-visualize",
            images={"image": self.screenshot_path}
        )

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

    def detect_cards_in_hand(self):
        try:
            card_paths = self.actions.capture_individual_cards()
            print("\nTesting individual card predictions:")

            cards = []
            for card_path in card_paths:
                results = self.card_model.run_workflow(
                    workspace_name="clash-royale-841nt",
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

    def detect_enemy_cards(self) -> List[str]:
        """Detect enemy cards currently on the battlefield"""
        try:
            # Use existing Roboflow model to detect enemy units
            screenshot_path = self.screenshot_path
            results = self.rf_model.run_workflow(
                workspace_name="workspace-mck69",
                workflow_id="detect-count-and-visualize",
                images={"image": screenshot_path}
            )

            enemy_cards = []
            # Handle new structure: dict with "predictions" key
            predictions = []
            if isinstance(results, dict) and "predictions" in results:
                predictions = results["predictions"]
            elif isinstance(results, list) and results:
                first = results[0]
                if isinstance(first, dict) and "predictions" in first:
                    predictions = first["predictions"]

            for prediction in predictions:
                # Filter for enemy units (you'll need to distinguish enemy vs friendly)
                if prediction.get('confidence', 0) > 0.7:
                    card_name = prediction.get('class_name', '')
                    # Add logic to determine if it's an enemy card based on position
                    x = prediction.get('x', 0)
                    y = prediction.get('y', 0)
                    if self._is_enemy_position(x, y):
                        enemy_cards.append(card_name)

            return enemy_cards
        except Exception as e:
            print(f"Error detecting enemy cards: {e}")
            return []

    def _is_enemy_position(self, x: float, y: float) -> bool:
        """Determine if detected card is in enemy territory"""
        # Enemy territory is typically upper half of the screen
        # Adjust based on your game area coordinates
        return y < self.grid_height / 2

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
            print(f"Error in detect_cards_in_hand: {e}")
            return []

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
        self.actions.capture_area(self.screenshot_path)
        results = self.rf_model.run_workflow(
            workspace_name="workspace-mck69",
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