#!/usr/bin/env python3
"""
Setup script for enhanced Clash Royale bot features
Helps users configure and test the new Redis-based enhancements
"""

import os
import sys
import subprocess
import time
from config import BotConfig
from feature_manager import FeatureManager

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n=== Installing Dependencies ===")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def check_redis_installation():
    """Check if Redis is installed and running"""
    print("\n=== Checking Redis Installation ===")
    
    # Try to import redis
    try:
        import redis
        print("✓ Redis Python library installed")
    except ImportError:
        print("✗ Redis Python library not found")
        return False
    
    # Try to connect to Redis
    try:
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        print("✓ Redis server is running")
        return True
    except Exception as e:
        print(f"✗ Redis server not accessible: {e}")
        print("\nTo install Redis:")
        print("  macOS: brew install redis && brew services start redis")
        print("  Ubuntu: sudo apt install redis-server")
        print("  Windows: Use Redis for Windows or Docker")
        return False

def setup_directories():
    """Create necessary directories"""
    print("\n=== Setting up Directories ===")
    directories = ["backups", "logs"]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Created directory: {directory}")
        except Exception as e:
            print(f"✗ Failed to create directory {directory}: {e}")
            return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of enhanced features"""
    print("\n=== Testing Basic Functionality ===")
    
    try:
        # Test configuration
        config = BotConfig()
        print("✓ Configuration loaded")
        
        # Test Redis card manager
        from redis_card_manager import RedisCardManager
        manager = RedisCardManager(config)
        print(f"✓ Redis Card Manager initialized (Redis available: {manager.redis_available})")
        
        # Test performance monitor
        from performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        monitor.track_decision_time(100.0)
        print("✓ Performance Monitor working")
        
        # Test feature manager
        feature_manager = FeatureManager(config)
        print("✓ Feature Manager initialized")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def configure_features():
    """Configure features based on system capabilities"""
    print("\n=== Configuring Features ===")
    
    config = BotConfig()
    feature_manager = FeatureManager(config)
    
    # Test and enable features gradually
    print("Testing Redis connection...")
    if feature_manager._test_redis_connection():
        feature_manager.enable_feature('REDIS', force=True)
        print("✓ Redis enabled")
        
        # Enable other features if Redis works
        print("Enabling opponent tracking...")
        feature_manager.enable_feature('OPPONENT_TRACKING', force=True)
        
        print("Enabling counter strategy...")
        feature_manager.enable_feature('COUNTER_STRATEGY', force=True)
        
        # Learning is more experimental, ask user
        response = input("Enable learning system? (experimental) [y/N]: ").lower()
        if response in ['y', 'yes']:
            feature_manager.enable_feature('LEARNING', force=True)
            print("✓ Learning system enabled")
    else:
        print("Redis not available, using JSON fallback mode")
        feature_manager.emergency_disable_all()
    
    feature_manager.print_feature_status()
    return True

def create_sample_config():
    """Create a sample configuration file"""
    print("\n=== Creating Sample Configuration ===")
    
    sample_env = """# Enhanced Clash Royale Bot Configuration
# Copy this to .env and modify as needed

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_TIMEOUT=2

# Feature Flags
ENABLE_REDIS=true
ENABLE_LEARNING=false
ENABLE_COUNTER_STRATEGY=false
ENABLE_OPPONENT_TRACKING=false

# Performance Settings
MAX_REDIS_LATENCY_MS=50
MAX_DECISION_TIME_MS=200

# Learning Parameters
LEARNING_RATE=0.02
CONFIDENCE_THRESHOLD=0.8
"""
    
    try:
        with open('.env.sample', 'w') as f:
            f.write(sample_env)
        print("✓ Sample configuration created (.env.sample)")
        print("  Copy to .env and modify as needed")
        return True
    except Exception as e:
        print(f"✗ Failed to create sample config: {e}")
        return False

def run_tests():
    """Run the test suite"""
    print("\n=== Running Tests ===")
    try:
        result = subprocess.run([sys.executable, "test_enhanced_features.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ All tests passed")
            return True
        else:
            print("✗ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Failed to run tests: {e}")
        return False

def main():
    """Main setup function"""
    print("=== Enhanced Clash Royale Bot Setup ===")
    print("This script will help you set up the enhanced features")
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("Please install dependencies manually and try again")
        return False
    
    # Check Redis
    redis_available = check_redis_installation()
    
    # Setup directories
    if not setup_directories():
        return False
    
    # Test basic functionality
    if not test_basic_functionality():
        return False
    
    # Configure features
    if not configure_features():
        return False
    
    # Create sample config
    create_sample_config()
    
    # Run tests
    print("\nWould you like to run the test suite? [Y/n]: ", end="")
    response = input().lower()
    if response not in ['n', 'no']:
        run_tests()
    
    print("\n=== Setup Complete ===")
    print("Enhanced features are now configured!")
    print("\nNext steps:")
    print("1. Review feature_flags.json to adjust enabled features")
    print("2. Copy .env.sample to .env and customize settings")
    print("3. Run 'python train.py' to start training with enhanced features")
    
    if not redis_available:
        print("\nNote: Redis is not available, so the bot will run in JSON fallback mode.")
        print("Enhanced features will be limited but the bot will still work normally.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
