import pyautogui
import os
from datetime import datetime
import time
import platform

class Actions:
    def __init__(self):
        self.os_type = platform.system()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_folder = os.path.join(self.script_dir, 'main_images')

        # ADD: Enhanced action tracking
        self.action_history = []

        # ADD: Platform manager integration
        try:
            from platform_manager import PlatformManager
            self.platform_manager = PlatformManager()
            self.use_platform_manager = True
            print(f"Platform manager initialized for {self.platform_manager.platform}")
        except ImportError:
            self.platform_manager = None
            self.use_platform_manager = False
            print("Platform manager not available, using legacy coordinates")

        # Initialize coordinates
        self._initialize_coordinates()

    def _initialize_coordinates(self):
        """Initialize screen coordinates with emulator detection"""
        if self.use_platform_manager:
            # Try to detect emulator and get dynamic coordinates
            emulator_window = self.platform_manager.find_emulator_window()
            if emulator_window:
                self._setup_dynamic_coordinates(emulator_window)
            else:
                print("No emulator detected, using default coordinates")
                self._setup_default_coordinates()
        else:
            self._setup_default_coordinates()

    def _setup_dynamic_coordinates(self, emulator_window):
        """Setup coordinates based on detected emulator window"""
        x, y, width, height = emulator_window['region']

        # Calculate game area as percentage of emulator window
        # These percentages work for most Android emulators running Clash Royale
        game_area_percent = {
            'left': 0.05,    # 5% from left edge
            'top': 0.15,     # 15% from top edge
            'right': 0.95,   # 95% from left edge
            'bottom': 0.85   # 85% from top edge
        }

        self.TOP_LEFT_X = int(x + width * game_area_percent['left'])
        self.TOP_LEFT_Y = int(y + height * game_area_percent['top'])
        self.BOTTOM_RIGHT_X = int(x + width * game_area_percent['right'])
        self.BOTTOM_RIGHT_Y = int(y + height * game_area_percent['bottom'])

        self.FIELD_AREA = (self.TOP_LEFT_X, self.TOP_LEFT_Y,
                          self.BOTTOM_RIGHT_X - self.TOP_LEFT_X,
                          self.BOTTOM_RIGHT_Y - self.TOP_LEFT_Y)

        self.WIDTH = self.BOTTOM_RIGHT_X - self.TOP_LEFT_X
        self.HEIGHT = self.BOTTOM_RIGHT_Y - self.TOP_LEFT_Y

        # Card bar coordinates (bottom of screen)
        self.CARD_BAR_X = int(x + width * 0.2)
        self.CARD_BAR_Y = int(y + height * 0.85)
        self.CARD_BAR_WIDTH = int(width * 0.6)
        self.CARD_BAR_HEIGHT = int(height * 0.1)

        print(f"Dynamic coordinates set: Game area {self.FIELD_AREA}, Card bar ({self.CARD_BAR_X}, {self.CARD_BAR_Y})")

    def _setup_default_coordinates(self):
        """Setup default coordinates based on OS"""
        if self.os_type == "Darwin":  # macOS
            # Updated coordinates for BlueStacks Air on macOS
            # BlueStacks window: position (1218, 72), size 538x932
            self.TOP_LEFT_X = 1218
            self.TOP_LEFT_Y = 72
            self.BOTTOM_RIGHT_X = 1756  # 1218 + 538
            self.BOTTOM_RIGHT_Y = 1004  # 72 + 932
            self.FIELD_AREA = (self.TOP_LEFT_X, self.TOP_LEFT_Y, self.BOTTOM_RIGHT_X, self.BOTTOM_RIGHT_Y)

            self.WIDTH = self.BOTTOM_RIGHT_X - self.TOP_LEFT_X
            self.HEIGHT = self.BOTTOM_RIGHT_Y - self.TOP_LEFT_Y

            # Card bar coordinates for BlueStacks Air (bottom of game area)
            # Updated with exact coordinates from user feedback
            self.CARD_BAR_X = 1315  # Exact top-left X coordinate
            self.CARD_BAR_Y = 832   # Exact top-left Y coordinate
            self.CARD_BAR_WIDTH = 309  # Exact width measurement
            self.CARD_BAR_HEIGHT = 153  # Exact height measurement

        elif self.os_type == "Windows": # windows
            self.TOP_LEFT_X = 1376
            self.TOP_LEFT_Y = 120
            self.BOTTOM_RIGHT_X = 1838
            self.BOTTOM_RIGHT_Y = 769
            self.FIELD_AREA = (self.TOP_LEFT_X, self.TOP_LEFT_Y, self.BOTTOM_RIGHT_X, self.BOTTOM_RIGHT_Y)

            self.WIDTH = self.BOTTOM_RIGHT_X - self.TOP_LEFT_X
            self.HEIGHT = self.BOTTOM_RIGHT_Y - self.TOP_LEFT_Y

            # Add card bar coordinates for Windows
            self.CARD_BAR_X = 1450
            self.CARD_BAR_Y = 847
            self.CARD_BAR_WIDTH = 1862 - 1450
            self.CARD_BAR_HEIGHT = 971 - 847

        # Card position to key mapping
        self.card_keys = {
            0: '1',  # Changed from 1 to 0
            1: '2',  # Changed from 2 to 1
            2: '3',  # Changed from 3 to 2
            3: '4'   # Changed from 4 to 3
        }
        
        # Card name to position mapping (will be updated during detection)
        self.current_card_positions = {}

    def capture_area(self, save_path):
        screenshot = pyautogui.screenshot(region=(self.TOP_LEFT_X, self.TOP_LEFT_Y, self.WIDTH, self.HEIGHT))
        screenshot.save(save_path)

    def capture_card_area(self, save_path):
        """Capture screenshot of card area"""
        screenshot = pyautogui.screenshot(region=(
            self.CARD_BAR_X, 
            self.CARD_BAR_Y, 
            self.CARD_BAR_WIDTH, 
            self.CARD_BAR_HEIGHT
        ))
        screenshot.save(save_path)

    def capture_individual_cards(self):
        """Capture and split card bar into individual card images with improved precision"""
        screenshot = pyautogui.screenshot(region=(
            self.CARD_BAR_X,
            self.CARD_BAR_Y,
            self.CARD_BAR_WIDTH,
            self.CARD_BAR_HEIGHT
        ))

        # The captured area includes both cards and elixir bar
        # Cards are in the bottom portion, elixir is in the top
        # Adjust to focus on just the card area (bottom ~70% of the captured region)
        card_area_top = int(self.CARD_BAR_HEIGHT * 0.3)  # Skip top 30% (elixir area)
        card_area_height = self.CARD_BAR_HEIGHT - card_area_top  # Use bottom 70% for cards

        # Improved card cropping with padding and better spacing
        card_width = self.CARD_BAR_WIDTH / 4  # Use float division for precision
        padding = 5  # Small padding to avoid edge artifacts
        cards = []

        # Split into 4 individual card images focusing on card area only
        for i in range(4):
            # Calculate more precise card boundaries
            left = int(i * card_width) + padding
            right = int((i + 1) * card_width) - padding
            top = card_area_top + padding  # Start from card area, not elixir area
            bottom = self.CARD_BAR_HEIGHT - padding

            # Ensure we don't go out of bounds
            left = max(0, left)
            right = min(self.CARD_BAR_WIDTH, right)
            top = max(card_area_top, top)
            bottom = min(self.CARD_BAR_HEIGHT, bottom)

            card_img = screenshot.crop((left, top, right, bottom))
            save_path = os.path.join(self.script_dir, 'screenshots', f"card_{i+1}.png")
            card_img.save(save_path)
            cards.append(save_path)

            print(f"🎴 Card {i+1}: cropped from ({left}, {top}) to ({right}, {bottom}) [card area only]")

        return cards

    def count_elixir(self):
        if self.os_type == "Darwin":
            for i in range(10, 0, -1):
                image_file = os.path.join(self.images_folder, f"{i}elixir.png")
                try:
                    location = pyautogui.locateOnScreen(image_file, confidence=0.5, grayscale=True)
                    if location:
                        return i
                except Exception as e:
                    print(f"Error locating {image_file}: {e}")
            return 0
        elif self.os_type == "Windows":
            target = (225, 128, 229)
            tolerance = 80
            count = 0
            for x in range(1512, 1892, 38):
                r, g, b = pyautogui.pixel(x, 989)
                if (abs(r - target[0]) <= tolerance) and (abs(g - target[1]) <= tolerance) and (abs(b - target[2]) <= tolerance):
                    count += 1
            return count
        else:
            return 0

    def update_card_positions(self, detections):
        """
        Update card positions based on detection results
        detections: list of dictionaries with 'class' and 'x' position
        """
        # Sort detections by x position (left to right)
        sorted_cards = sorted(detections, key=lambda x: x['x'])
        
        # Map cards to positions 0-3 instead of 1-4
        self.current_card_positions = {
            card['class']: idx  # Removed +1 
            for idx, card in enumerate(sorted_cards)
        }

    def card_play(self, x, y, card_index):
        print(f"Playing card {card_index} at position ({x}, {y})")
        if card_index in self.card_keys:
            key = self.card_keys[card_index]
            print(f"Pressing key: {key}")

            # Focus emulator window if using platform manager
            if self.use_platform_manager and self.platform_manager.emulator_window:
                self.platform_manager.focus_emulator_window()
                time.sleep(0.1)

            pyautogui.press(key)
            time.sleep(0.2)
            print(f"Moving mouse to: ({x}, {y})")

            # Use enhanced click method
            if self.use_platform_manager and self.platform_manager.emulator_window:
                self.platform_manager.click_at_position(x, y, relative_to_window=True)
            else:
                pyautogui.moveTo(x, y, duration=0.2)
                print("Clicking")
                pyautogui.click()

            # ADD: Track action for learning
            self.action_history.append({
                'card_index': card_index,
                'position': (x, y),
                'timestamp': time.time()
            })
        else:
            print(f"Invalid card index: {card_index}")

    def enhanced_click(self, x, y, relative_to_window=True):
        """Enhanced click method with platform manager support"""
        if self.use_platform_manager and self.platform_manager.emulator_window:
            self.platform_manager.click_at_position(x, y, relative_to_window)
        else:
            pyautogui.click(x, y)

    def click_battle_start(self):
        button_image = os.path.join(self.images_folder, "battlestartbutton.png")
        confidences = [0.8, 0.7, 0.6, 0.5]  # Try multiple confidence levels

        # Define the region (left, top, width, height) for the correct battle button
        battle_button_region = (1486, 755, 1730-1486, 900-755)

        while True:
            for confidence in confidences:
                print(f"Looking for battle start button (confidence: {confidence})")
                try:
                    location = pyautogui.locateOnScreen(
                        button_image,
                        confidence=confidence,
                        region=battle_button_region  # Only search in this region
                    )
                    if location:
                        x, y = pyautogui.center(location)
                        print(f"Found battle start button at ({x}, {y})")
                        pyautogui.moveTo(x, y, duration=0.2)
                        pyautogui.click()
                        return True
                except:
                    pass

            # If button not found, click to clear screens
            print("Button not found, clicking to clear screens...")
            pyautogui.moveTo(1705, 331, duration=0.2)
            pyautogui.click()
            time.sleep(1)

    def detect_game_end(self):
        try:
            winner_img = os.path.join(self.images_folder, "Winner.png")
            confidences = [0.8, 0.7, 0.6]

            winner_region = (1510, 121, 1678-1510, 574-121)

            for confidence in confidences:
                print(f"\nTrying detection with confidence: {confidence}")
                winner_location = None

                # Try to find Winner in region
                try:
                    winner_location = pyautogui.locateOnScreen(
                        winner_img, confidence=confidence, grayscale=True, region=winner_region
                    )
                except Exception as e:
                    print(f"Error locating Winner: {str(e)}")

                if winner_location:
                    _, y = pyautogui.center(winner_location)
                    print(f"Found 'Winner' at y={y} with confidence {confidence}")
                    result = "victory" if y > 402 else "defeat"
                    time.sleep(3)
                    # Click the "Play Again" button at a fixed coordinate (adjust as needed)
                    play_again_x, play_again_y = 1522, 913  # Example coordinates
                    print(f"Clicking Play Again at ({play_again_x}, {play_again_y})")
                    pyautogui.moveTo(play_again_x, play_again_y, duration=0.2)
                    pyautogui.click()
                    return result
        except Exception as e:
            print(f"Error in game end detection: {str(e)}")
        return None

    def detect_match_over(self):
        matchover_img = os.path.join(self.images_folder, "matchover.png")
        confidences = [0.8, 0.6, 0.4]
        # Define the region where the matchover image appears (adjust as needed)
        region = (1378, 335, 1808-1378, 411-335)
        for confidence in confidences:
            try:
                location = pyautogui.locateOnScreen(
                    matchover_img, confidence=confidence, grayscale=True, region=region
                )
                if location:
                    print("Match over detected!")
                    return True
            except Exception as e:
                print(f"Error locating matchover.png: {e}")
        return False