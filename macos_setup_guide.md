# macOS Setup Guide for Clash Royale Bot

## Overview
This guide helps you set up the Clash Royale bot on macOS using Android emulators.

## Supported Android Emulators on macOS

### 1. Android Studio Emulator (Recommended)
**Installation:**
```bash
# Install Android Studio
brew install --cask android-studio

# Or download from: https://developer.android.com/studio
```

**Setup:**
1. Open Android Studio
2. Go to Tools > AVD Manager
3. Create a new Virtual Device
4. Choose a phone (e.g., Pixel 6)
5. Download Android 11+ system image
6. Configure with:
   - RAM: 4GB+
   - Internal Storage: 8GB+
   - Graphics: Hardware - GLES 2.0

**Launch:**
```bash
# Start emulator from command line
~/Library/Android/sdk/emulator/emulator -avd YOUR_AVD_NAME
```

### 2. BlueStacks (If Available)
**Installation:**
```bash
# Download from official website
# https://www.bluestacks.com/download.html
```

### 3. Nox Player
**Installation:**
```bash
# Download from official website
# https://www.bignox.com/
```

## Bot Configuration for macOS

### 1. Install Dependencies
```bash
# Install Redis (already done)
brew install redis
brew services start redis

# Install Python dependencies
pip3 install -r requirements.txt
```

### 2. Configure Clash Royale in Emulator
1. Install Clash Royale from Google Play Store
2. Log into your account
3. Position emulator window for optimal capture
4. Ensure game runs in landscape mode

### 3. Test Bot Detection
```python
from platform_manager import PlatformManager
from Actions import Actions

# Test emulator detection
pm = PlatformManager()
emulators = pm.detect_emulators()
print(f"Detected emulators: {emulators}")

# Test coordinate mapping
actions = Actions()
print(f"Game area: {actions.FIELD_AREA}")
```

### 4. Run the Bot
```bash
# Start training
python3 train.py

# Or test environment
python3 -c "from env import ClashRoyaleEnv; env = ClashRoyaleEnv()"
```

## Coordinate Calibration

The bot automatically detects emulator windows and calculates game coordinates. If you need manual calibration:

1. **Find your emulator window coordinates:**
```python
from platform_manager import PlatformManager
pm = PlatformManager()
window = pm.find_emulator_window()
print(f"Window info: {window}")
```

2. **Adjust game area percentages in Actions.py:**
```python
game_area_percent = {
    'left': 0.05,    # Adjust if game area is off
    'top': 0.15,     # Adjust for title bars
    'right': 0.95,   # Adjust for side margins
    'bottom': 0.85   # Adjust for bottom UI
}
```

## Troubleshooting

### Emulator Not Detected
1. Ensure emulator is running
2. Check process names in platform_manager.py
3. Try manual window detection

### Coordinates Off
1. Check emulator resolution
2. Ensure Clash Royale is in landscape mode
3. Adjust game_area_percent values

### Performance Issues
1. Increase emulator RAM allocation
2. Enable hardware acceleration
3. Close other applications

### Permission Issues
1. Grant accessibility permissions to Terminal/Python
2. Allow screen recording permissions
3. Disable macOS mouse acceleration

## Performance Optimization

### Emulator Settings
- **RAM:** 4GB minimum, 8GB recommended
- **CPU Cores:** 4 cores recommended
- **Graphics:** Hardware acceleration enabled
- **Resolution:** 1920x1080 or 1280x720

### macOS Settings
```bash
# Disable mouse acceleration
defaults write .GlobalPreferences com.apple.mouse.scaling -1

# Grant accessibility permissions
# System Preferences > Security & Privacy > Accessibility
# Add Terminal and Python to allowed apps
```

### Bot Settings
```python
# In config.py, optimize for macOS
MAX_DECISION_TIME_MS = 300  # Increase for slower Macs
REDIS_TIMEOUT = 3           # Increase if Redis is slow
```

## Testing Checklist

- [ ] Redis server running
- [ ] Android emulator running
- [ ] Clash Royale installed and logged in
- [ ] Bot detects emulator window
- [ ] Coordinates properly mapped
- [ ] Screen capture working
- [ ] Click actions working
- [ ] Card detection functional

## Advanced Configuration

### Multiple Emulators
The bot can detect multiple emulators and will use the first one found. To specify a particular emulator:

```python
# In your script
from platform_manager import PlatformManager
pm = PlatformManager()
emulators = pm.detect_emulators()
# Select specific emulator by name
target_emulator = next((e for e in emulators if e['name'] == 'android_studio'), None)
```

### Custom Coordinate Mapping
For non-standard emulator setups:

```python
# In Actions.py _setup_dynamic_coordinates method
# Customize these percentages for your setup
game_area_percent = {
    'left': 0.1,     # 10% from left
    'top': 0.2,      # 20% from top
    'right': 0.9,    # 90% from left
    'bottom': 0.8    # 80% from top
}
```

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify emulator is properly detected
3. Test coordinate mapping manually
4. Ensure all permissions are granted

The bot now supports cross-platform operation and should work on macOS with proper emulator setup!
