#!/usr/bin/env python3
"""
BlueStacks Detection Script for macOS
This script helps detect BlueStacks and find the correct coordinates
"""

import subprocess
import re
import time

def get_running_processes():
    """Get all running processes"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"Error getting processes: {e}")
        return ""

def find_bluestacks_processes():
    """Find BlueStacks related processes"""
    processes = get_running_processes()
    bluestacks_processes = []
    
    for line in processes.split('\n'):
        if 'bluestacks' in line.lower() or 'blue' in line.lower():
            bluestacks_processes.append(line.strip())
    
    return bluestacks_processes

def get_window_info():
    """Get window information using AppleScript"""
    try:
        # Get all window information with better formatting
        script = '''
        tell application "System Events"
            set windowList to ""
            repeat with proc in (every process whose background only is false)
                try
                    repeat with win in (every window of proc)
                        set procName to name of proc
                        set winName to name of win
                        set winPos to position of win
                        set winSize to size of win
                        set windowInfo to procName & " | " & winName & " | " & (item 1 of winPos) & "," & (item 2 of winPos) & " | " & (item 1 of winSize) & "x" & (item 2 of winSize)
                        set windowList to windowList & windowInfo & "\n"
                    end repeat
                end try
            end repeat
            return windowList
        end tell
        '''

        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting window info: {e}")
        return ""

def find_bluestacks_windows():
    """Find BlueStacks windows"""
    window_info = get_window_info()
    bluestacks_windows = []

    for line in window_info.split('\n'):
        if line.strip() and ('bluestacks' in line.lower() or 'blue' in line.lower()):
            bluestacks_windows.append(line.strip())

    return bluestacks_windows

def main():
    print("🔍 Detecting BlueStacks on macOS...")
    print("=" * 50)
    
    # Check processes
    print("\n📋 BlueStacks Processes:")
    processes = find_bluestacks_processes()
    if processes:
        for proc in processes:
            print(f"  ✅ {proc}")
    else:
        print("  ❌ No BlueStacks processes found")
    
    # Check windows
    print("\n🪟 BlueStacks Windows:")
    windows = find_bluestacks_windows()
    if windows:
        for win in windows:
            print(f"  ✅ {win}")
    else:
        print("  ❌ No BlueStacks windows found")
    
    # Get all windows for debugging
    print("\n🔍 All Windows (for debugging):")
    all_windows = get_window_info()
    lines = [line.strip() for line in all_windows.split('\n') if line.strip()]
    for line in lines[:15]:  # Show first 15
        print(f"  📱 {line}")
    
    print("\n" + "=" * 50)
    print("💡 Tips:")
    print("1. Make sure BlueStacks is running")
    print("2. Make sure Clash Royale is open in BlueStacks")
    print("3. Position BlueStacks on the right side of your screen")
    print("4. The bot will use these coordinates to interact with the game")

if __name__ == "__main__":
    main()
