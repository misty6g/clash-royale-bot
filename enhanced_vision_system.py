#!/usr/bin/env python3
"""
Enhanced Computer Vision System for Clash Royale Bot
Integrates screen capture, object detection, and game state parsing
"""

import cv2
import numpy as np
import pyautogui
import time
import os
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pytesseract
from PIL import Image
import re

class GamePhase(Enum):
    LOADING = "loading"
    NORMAL = "normal"
    OVERTIME = "overtime"
    SUDDEN_DEATH = "sudden_death"
    MATCH_END = "match_end"

@dataclass
class GameState:
    """Complete game state from visual analysis"""
    # Basic game info
    phase: GamePhase
    time_remaining: float
    
    # Player state
    my_elixir: int
    my_tower_health: Dict[str, int]  # {'king': 100, 'left': 100, 'right': 100}
    my_cards: List[str]
    
    # Enemy state
    enemy_elixir: int  # Estimated
    enemy_tower_health: Dict[str, int]
    enemy_cards_played: List[str]
    
    # Field state
    units_on_field: List[Dict]  # [{'type': 'Knight', 'position': (x, y), 'team': 'ally'}]
    
    # Match info
    match_score: Tuple[int, int]  # (my_towers, enemy_towers)
    
    # Confidence scores
    detection_confidence: Dict[str, float]

class EnhancedVisionSystem:
    """Enhanced computer vision system for real-time game analysis"""
    
    def __init__(self, platform_manager=None):
        self.platform_manager = platform_manager
        
        # Initialize Roboflow clients
        self.setup_roboflow_clients()
        
        # Game area coordinates (will be updated by platform manager)
        self.game_area = (0, 0, 1920, 1080)  # Default full screen
        self.card_area = (0, 900, 1920, 1080)  # Bottom area for cards
        self.elixir_area = (1800, 850, 1900, 950)  # Elixir counter area
        self.timer_area = (900, 50, 1020, 100)  # Timer area
        
        # Detection thresholds
        self.confidence_threshold = 0.5
        self.card_confidence_threshold = 0.6
        
        # Cache for performance
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.screenshot_cache_duration = 0.1  # 100ms cache
        
        # Game state tracking
        self.current_game_state = None
        self.game_state_history = []
        
        # Initialize coordinate mapping
        self._update_coordinate_mapping()
        
        print("Enhanced Vision System initialized")
    
    def setup_roboflow_clients(self):
        """Setup Roboflow inference clients"""
        try:
            from inference_sdk import InferenceHTTPClient
            
            self.field_model = InferenceHTTPClient(
                api_url="http://localhost:9001",
                api_key="zt3zjKAX2eYuIBGrLDJu"
            )
            
            self.card_model = InferenceHTTPClient(
                api_url="http://localhost:9001", 
                api_key="zt3zjKAX2eYuIBGrLDJu"
            )
            
            print("Roboflow clients initialized successfully")
            
        except Exception as e:
            print(f"Warning: Roboflow setup failed: {e}")
            self.field_model = None
            self.card_model = None
    
    def _update_coordinate_mapping(self):
        """Update coordinate mapping based on platform manager"""
        if self.platform_manager and self.platform_manager.emulator_window:
            window = self.platform_manager.emulator_window
            x, y, w, h = window['region']
            
            # Update game areas based on emulator window
            self.game_area = (x, y, w, h)
            
            # Calculate relative positions within emulator
            self.card_area = (
                x + int(w * 0.1),  # 10% from left
                y + int(h * 0.85), # 85% from top
                x + int(w * 0.9),  # 90% from left
                y + h              # Bottom of window
            )
            
            self.elixir_area = (
                x + int(w * 0.85), # 85% from left
                y + int(h * 0.8),  # 80% from top
                x + int(w * 0.95), # 95% from left
                y + int(h * 0.9)   # 90% from top
            )
            
            self.timer_area = (
                x + int(w * 0.45), # 45% from left
                y + int(h * 0.05), # 5% from top
                x + int(w * 0.55), # 55% from left
                y + int(h * 0.15)  # 15% from top
            )
            
            print(f"Coordinate mapping updated for emulator window: {window}")
    
    def capture_screen_region(self, region: Tuple[int, int, int, int] = None) -> np.ndarray:
        """Capture screen region with caching"""
        current_time = time.time()
        
        # Use cache if recent enough
        if (self.last_screenshot is not None and 
            current_time - self.last_screenshot_time < self.screenshot_cache_duration):
            return self.last_screenshot
        
        # Capture new screenshot
        if region is None:
            region = self.game_area
        
        try:
            if self.platform_manager:
                screenshot = self.platform_manager.capture_screen(region)
            else:
                # Fallback to pyautogui
                screenshot = pyautogui.screenshot(region=region)
                screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Update cache
            self.last_screenshot = screenshot
            self.last_screenshot_time = current_time
            
            return screenshot
            
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return np.array([])
    
    def detect_cards_in_hand(self) -> List[str]:
        """Detect cards currently in hand"""
        try:
            # Capture card area
            card_screenshot = self.capture_screen_region(self.card_area)
            if card_screenshot.size == 0:
                return ["Unknown"] * 4
            
            # Save for debugging
            debug_path = os.path.join("screenshots", "debug_cards.png")
            cv2.imwrite(debug_path, card_screenshot)
            
            # Split into individual card regions
            card_regions = self._split_card_regions(card_screenshot)
            detected_cards = []
            
            for i, card_region in enumerate(card_regions):
                # Save individual card for debugging
                card_debug_path = os.path.join("screenshots", f"debug_card_{i}.png")
                cv2.imwrite(card_debug_path, card_region)
                
                # Detect card using Roboflow
                card_name = self._detect_single_card(card_region)
                detected_cards.append(card_name)
                
                print(f"Card {i}: {card_name}")
            
            return detected_cards
            
        except Exception as e:
            print(f"Error detecting cards: {e}")
            return ["Unknown"] * 4
    
    def _split_card_regions(self, card_screenshot: np.ndarray) -> List[np.ndarray]:
        """Split card area into individual card regions"""
        height, width = card_screenshot.shape[:2]
        
        # Assume 4 cards evenly distributed
        card_width = width // 4
        card_regions = []
        
        for i in range(4):
            x_start = i * card_width
            x_end = (i + 1) * card_width
            
            # Add some padding to avoid edge artifacts
            padding = int(card_width * 0.05)
            x_start = max(0, x_start + padding)
            x_end = min(width, x_end - padding)
            
            card_region = card_screenshot[:, x_start:x_end]
            card_regions.append(card_region)
        
        return card_regions
    
    def _detect_single_card(self, card_image: np.ndarray) -> str:
        """Detect a single card using Roboflow"""
        if self.card_model is None:
            return "Unknown"
        
        try:
            # Save card image temporarily
            temp_path = os.path.join("screenshots", "temp_card.png")
            cv2.imwrite(temp_path, card_image)
            
            # Run Roboflow inference
            results = self.card_model.run_workflow(
                workspace_name="clash-royale",
                workflow_id="custom-workflow",
                images={"image": temp_path}
            )
            
            # Parse results
            if isinstance(results, list) and results:
                predictions_dict = results[0].get("predictions", {})
                if isinstance(predictions_dict, dict):
                    predictions = predictions_dict.get("predictions", [])
                    if predictions and len(predictions) > 0:
                        best_prediction = max(predictions, key=lambda x: x.get("confidence", 0))
                        if best_prediction.get("confidence", 0) > self.card_confidence_threshold:
                            return best_prediction.get("class", "Unknown")
            
            return "Unknown"
            
        except Exception as e:
            print(f"Error in single card detection: {e}")
            return "Unknown"
    
    def detect_elixir_level(self) -> int:
        """Detect current elixir level using OCR"""
        try:
            # Capture elixir area
            elixir_screenshot = self.capture_screen_region(self.elixir_area)
            if elixir_screenshot.size == 0:
                return 10  # Default assumption
            
            # Convert to PIL Image for OCR
            elixir_pil = Image.fromarray(cv2.cvtColor(elixir_screenshot, cv2.COLOR_BGR2RGB))
            
            # Preprocess for better OCR
            elixir_pil = elixir_pil.convert('L')  # Grayscale
            elixir_pil = elixir_pil.resize((elixir_pil.width * 3, elixir_pil.height * 3))  # Upscale
            
            # OCR with specific config for numbers
            ocr_config = '--psm 8 -c tessedit_char_whitelist=0123456789'
            elixir_text = pytesseract.image_to_string(elixir_pil, config=ocr_config).strip()
            
            # Parse elixir value
            elixir_match = re.search(r'(\d+)', elixir_text)
            if elixir_match:
                elixir = int(elixir_match.group(1))
                return min(10, max(0, elixir))  # Clamp to valid range
            
            return 10  # Default if detection fails
            
        except Exception as e:
            print(f"Error detecting elixir: {e}")
            return 10
    
    def detect_game_phase(self) -> GamePhase:
        """Detect current game phase"""
        try:
            # Capture timer area
            timer_screenshot = self.capture_screen_region(self.timer_area)
            if timer_screenshot.size == 0:
                return GamePhase.NORMAL
            
            # Convert to PIL for OCR
            timer_pil = Image.fromarray(cv2.cvtColor(timer_screenshot, cv2.COLOR_BGR2RGB))
            timer_pil = timer_pil.convert('L')
            timer_pil = timer_pil.resize((timer_pil.width * 2, timer_pil.height * 2))
            
            # OCR to read timer
            timer_text = pytesseract.image_to_string(timer_pil).strip().lower()
            
            # Determine phase based on timer text
            if "overtime" in timer_text:
                return GamePhase.OVERTIME
            elif "sudden" in timer_text or "death" in timer_text:
                return GamePhase.SUDDEN_DEATH
            elif any(keyword in timer_text for keyword in ["victory", "defeat", "end"]):
                return GamePhase.MATCH_END
            else:
                return GamePhase.NORMAL
                
        except Exception as e:
            print(f"Error detecting game phase: {e}")
            return GamePhase.NORMAL
    
    def detect_tower_health(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Detect tower health for both players"""
        # This would require more sophisticated image analysis
        # For now, return default values
        my_towers = {"king": 100, "left": 100, "right": 100}
        enemy_towers = {"king": 100, "left": 100, "right": 100}
        
        return my_towers, enemy_towers
    
    def detect_units_on_field(self) -> List[Dict]:
        """Detect units currently on the battlefield"""
        if self.field_model is None:
            return []
        
        try:
            # Capture main game area
            field_screenshot = self.capture_screen_region(self.game_area)
            if field_screenshot.size == 0:
                return []
            
            # Save for debugging
            debug_path = os.path.join("screenshots", "debug_field.png")
            cv2.imwrite(debug_path, field_screenshot)
            
            # Run field detection
            results = self.field_model.run_workflow(
                workspace_name="clash-royale",
                workflow_id="field-detection",
                images={"image": debug_path}
            )
            
            # Parse field units (simplified)
            units = []
            # This would parse the actual detection results
            # For now, return empty list
            
            return units
            
        except Exception as e:
            print(f"Error detecting field units: {e}")
            return []
    
    def get_complete_game_state(self) -> GameState:
        """Get complete game state from visual analysis"""
        try:
            # Detect all components
            cards = self.detect_cards_in_hand()
            elixir = self.detect_elixir_level()
            phase = self.detect_game_phase()
            my_towers, enemy_towers = self.detect_tower_health()
            units = self.detect_units_on_field()
            
            # Create game state
            game_state = GameState(
                phase=phase,
                time_remaining=300.0,  # Default 5 minutes
                my_elixir=elixir,
                my_tower_health=my_towers,
                my_cards=cards,
                enemy_elixir=10,  # Estimated
                enemy_tower_health=enemy_towers,
                enemy_cards_played=[],
                units_on_field=units,
                match_score=(3, 3),  # Default full towers
                detection_confidence={
                    "cards": 0.8,
                    "elixir": 0.7,
                    "phase": 0.6,
                    "towers": 0.5
                }
            )
            
            # Update current state
            self.current_game_state = game_state
            self.game_state_history.append(game_state)
            
            # Keep only recent history
            if len(self.game_state_history) > 100:
                self.game_state_history = self.game_state_history[-100:]
            
            return game_state
            
        except Exception as e:
            print(f"Error getting complete game state: {e}")
            # Return default state
            return GameState(
                phase=GamePhase.NORMAL,
                time_remaining=300.0,
                my_elixir=10,
                my_tower_health={"king": 100, "left": 100, "right": 100},
                my_cards=["Unknown"] * 4,
                enemy_elixir=10,
                enemy_tower_health={"king": 100, "left": 100, "right": 100},
                enemy_cards_played=[],
                units_on_field=[],
                match_score=(3, 3),
                detection_confidence={"overall": 0.0}
            )
    
    def validate_detection_accuracy(self, ground_truth: Dict = None) -> Dict[str, float]:
        """Validate detection accuracy against ground truth"""
        if ground_truth is None:
            return {"validation": "no_ground_truth"}
        
        accuracy_scores = {}
        current_state = self.get_complete_game_state()
        
        # Compare cards
        if "cards" in ground_truth:
            correct_cards = sum(1 for i, card in enumerate(current_state.my_cards) 
                              if i < len(ground_truth["cards"]) and card == ground_truth["cards"][i])
            accuracy_scores["cards"] = correct_cards / len(ground_truth["cards"])
        
        # Compare elixir
        if "elixir" in ground_truth:
            elixir_diff = abs(current_state.my_elixir - ground_truth["elixir"])
            accuracy_scores["elixir"] = max(0, 1 - elixir_diff / 10)
        
        return accuracy_scores
    
    def save_debug_images(self, prefix: str = "debug"):
        """Save debug images for analysis"""
        timestamp = int(time.time())
        
        # Save full game area
        game_screenshot = self.capture_screen_region(self.game_area)
        if game_screenshot.size > 0:
            cv2.imwrite(f"screenshots/{prefix}_game_{timestamp}.png", game_screenshot)
        
        # Save card area
        card_screenshot = self.capture_screen_region(self.card_area)
        if card_screenshot.size > 0:
            cv2.imwrite(f"screenshots/{prefix}_cards_{timestamp}.png", card_screenshot)
        
        # Save elixir area
        elixir_screenshot = self.capture_screen_region(self.elixir_area)
        if elixir_screenshot.size > 0:
            cv2.imwrite(f"screenshots/{prefix}_elixir_{timestamp}.png", elixir_screenshot)
        
        print(f"Debug images saved with prefix: {prefix}_{timestamp}")

# Test function
def test_vision_system():
    """Test the enhanced vision system"""
    print("Testing Enhanced Vision System...")
    
    try:
        from platform_manager import PlatformManager
        pm = PlatformManager()
        pm.find_emulator_window()
        
        vision = EnhancedVisionSystem(pm)
        
        # Test card detection
        print("Testing card detection...")
        cards = vision.detect_cards_in_hand()
        print(f"Detected cards: {cards}")
        
        # Test elixir detection
        print("Testing elixir detection...")
        elixir = vision.detect_elixir_level()
        print(f"Detected elixir: {elixir}")
        
        # Test complete game state
        print("Testing complete game state...")
        game_state = vision.get_complete_game_state()
        print(f"Game state: {game_state}")
        
        # Save debug images
        vision.save_debug_images("test")
        
        print("Vision system test completed!")
        
    except Exception as e:
        print(f"Vision system test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vision_system()
