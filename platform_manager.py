import platform
import os
import subprocess
import pyautogui
import time
from typing import Tuple, Optional, List, Dict
import cv2
import numpy as np

class PlatformManager:
    """Cross-platform compatibility manager for macOS and Windows"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_macos = self.platform == 'darwin'
        self.is_windows = self.platform == 'windows'
        self.is_linux = self.platform == 'linux'
        
        # Emulator configurations
        self.emulator_configs = {
            'bluestacks': {
                'windows': {
                    'process_names': ['BlueStacks.exe', 'HD-Player.exe'],
                    'window_titles': ['BlueStacks', 'BlueStacks App Player'],
                    'default_size': (1600, 900),
                    'game_area': (0, 0, 1600, 900)
                },
                'macos': {
                    'process_names': ['BlueStacks'],
                    'window_titles': ['BlueStacks'],
                    'default_size': (1600, 900),
                    'game_area': (0, 0, 1600, 900)
                }
            },
            'android_studio': {
                'macos': {
                    'process_names': ['qemu-system-x86_64', 'emulator'],
                    'window_titles': ['Android Emulator'],
                    'default_size': (1080, 1920),
                    'game_area': (0, 0, 1080, 1920)
                },
                'windows': {
                    'process_names': ['qemu-system-x86_64.exe', 'emulator.exe'],
                    'window_titles': ['Android Emulator'],
                    'default_size': (1080, 1920),
                    'game_area': (0, 0, 1080, 1920)
                }
            },
            'nox': {
                'windows': {
                    'process_names': ['Nox.exe', 'NoxVMHandle.exe'],
                    'window_titles': ['NoxPlayer'],
                    'default_size': (1280, 720),
                    'game_area': (0, 0, 1280, 720)
                },
                'macos': {
                    'process_names': ['NoxPlayer'],
                    'window_titles': ['NoxPlayer'],
                    'default_size': (1280, 720),
                    'game_area': (0, 0, 1280, 720)
                }
            }
        }
        
        self.detected_emulator = None
        self.emulator_window = None
        self.coordinate_scale = (1.0, 1.0)
        
    def detect_emulators(self) -> List[Dict]:
        """Detect running Android emulators"""
        detected = []
        
        for emulator_name, configs in self.emulator_configs.items():
            if self.platform in configs:
                config = configs[self.platform]
                
                # Check for running processes
                for process_name in config['process_names']:
                    if self._is_process_running(process_name):
                        detected.append({
                            'name': emulator_name,
                            'process': process_name,
                            'config': config
                        })
                        break
        
        return detected
    
    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is running"""
        try:
            if self.is_macos:
                result = subprocess.run(['pgrep', '-f', process_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            elif self.is_windows:
                result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], 
                                      capture_output=True, text=True)
                return process_name.lower() in result.stdout.lower()
            else:  # Linux
                result = subprocess.run(['pgrep', '-f', process_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
        except Exception as e:
            print(f"Error checking process {process_name}: {e}")
            return False
    
    def find_emulator_window(self) -> Optional[Dict]:
        """Find and focus on emulator window"""
        detected_emulators = self.detect_emulators()
        
        if not detected_emulators:
            print("No Android emulators detected")
            return None
        
        # Use the first detected emulator
        emulator = detected_emulators[0]
        self.detected_emulator = emulator
        
        # Try to find the window
        window_info = self._find_window_by_title(emulator['config']['window_titles'])
        
        if window_info:
            self.emulator_window = window_info
            print(f"Found {emulator['name']} window: {window_info}")
            return window_info
        
        print(f"Could not find window for {emulator['name']}")
        return None
    
    def _find_window_by_title(self, titles: List[str]) -> Optional[Dict]:
        """Find window by title (cross-platform)"""
        try:
            if self.is_macos:
                return self._find_window_macos(titles)
            elif self.is_windows:
                return self._find_window_windows(titles)
            else:
                return self._find_window_linux(titles)
        except Exception as e:
            print(f"Error finding window: {e}")
            return None
    
    def _find_window_macos(self, titles: List[str]) -> Optional[Dict]:
        """Find window on macOS using AppleScript"""
        for title in titles:
            try:
                script = f'''
                tell application "System Events"
                    set windowList to every window of every process whose name contains "{title}"
                    if length of windowList > 0 then
                        set targetWindow to item 1 of windowList
                        set windowPosition to position of targetWindow
                        set windowSize to size of targetWindow
                        return (item 1 of windowPosition) & "," & (item 2 of windowPosition) & "," & (item 1 of windowSize) & "," & (item 2 of windowSize)
                    end if
                end tell
                '''
                
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    coords = result.stdout.strip().split(',')
                    if len(coords) == 4:
                        x, y, w, h = map(int, coords)
                        return {
                            'title': title,
                            'x': x, 'y': y, 'width': w, 'height': h,
                            'region': (x, y, w, h)
                        }
            except Exception as e:
                print(f"Error finding window {title} on macOS: {e}")
                continue
        
        return None
    
    def _find_window_windows(self, titles: List[str]) -> Optional[Dict]:
        """Find window on Windows using pygetwindow"""
        try:
            import pygetwindow as gw
            
            for title in titles:
                windows = gw.getWindowsWithTitle(title)
                if windows:
                    window = windows[0]
                    return {
                        'title': title,
                        'x': window.left, 'y': window.top,
                        'width': window.width, 'height': window.height,
                        'region': (window.left, window.top, window.width, window.height),
                        'window_obj': window
                    }
        except ImportError:
            print("pygetwindow not available, using fallback method")
        except Exception as e:
            print(f"Error finding window on Windows: {e}")
        
        return None
    
    def _find_window_linux(self, titles: List[str]) -> Optional[Dict]:
        """Find window on Linux using wmctrl"""
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    for title in titles:
                        if title.lower() in line.lower():
                            # Parse wmctrl output to get window info
                            parts = line.split()
                            if len(parts) >= 4:
                                window_id = parts[0]
                                # Get geometry
                                geom_result = subprocess.run(['xwininfo', '-id', window_id], 
                                                           capture_output=True, text=True)
                                # Parse geometry from xwininfo output
                                # This is a simplified implementation
                                return {'title': title, 'x': 0, 'y': 0, 'width': 1280, 'height': 720}
        except Exception as e:
            print(f"Error finding window on Linux: {e}")
        
        return None
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """Capture screen with cross-platform compatibility"""
        try:
            if region:
                # Capture specific region
                screenshot = pyautogui.screenshot(region=region)
            else:
                # Capture full screen
                screenshot = pyautogui.screenshot()
            
            # Convert PIL image to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return screenshot_cv
            
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return np.array([])
    
    def click_at_position(self, x: int, y: int, relative_to_window: bool = True):
        """Click at position with coordinate translation"""
        try:
            if relative_to_window and self.emulator_window:
                # Convert relative coordinates to absolute
                abs_x = self.emulator_window['x'] + x
                abs_y = self.emulator_window['y'] + y
            else:
                abs_x, abs_y = x, y
            
            # Apply coordinate scaling if needed
            scaled_x = int(abs_x * self.coordinate_scale[0])
            scaled_y = int(abs_y * self.coordinate_scale[1])
            
            pyautogui.click(scaled_x, scaled_y)
            
        except Exception as e:
            print(f"Error clicking at position ({x}, {y}): {e}")
    
    def get_emulator_region(self) -> Optional[Tuple[int, int, int, int]]:
        """Get the region of the emulator window for screen capture"""
        if self.emulator_window:
            return self.emulator_window['region']
        return None
    
    def focus_emulator_window(self) -> bool:
        """Focus on the emulator window"""
        try:
            if self.is_macos and self.emulator_window:
                # Use AppleScript to focus window on macOS
                title = self.emulator_window['title']
                script = f'''
                tell application "System Events"
                    set frontmost of first process whose name contains "{title}" to true
                end tell
                '''
                subprocess.run(['osascript', '-e', script])
                return True
                
            elif self.is_windows and self.emulator_window and 'window_obj' in self.emulator_window:
                # Use pygetwindow to focus on Windows
                self.emulator_window['window_obj'].activate()
                return True
                
        except Exception as e:
            print(f"Error focusing emulator window: {e}")
        
        return False
    
    def get_platform_info(self) -> Dict:
        """Get platform information"""
        return {
            'platform': self.platform,
            'is_macos': self.is_macos,
            'is_windows': self.is_windows,
            'is_linux': self.is_linux,
            'detected_emulator': self.detected_emulator,
            'emulator_window': self.emulator_window
        }
