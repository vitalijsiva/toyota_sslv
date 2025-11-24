#!/usr/bin/env python3
"""
Simple bot starter that handles conflicts gracefully
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def kill_existing_bots():
    """Kill any existing Python processes that might be running the bot"""
    try:
        if sys.platform == 'win32':
            # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                         capture_output=True, check=False)
            subprocess.run(['taskkill', '/F', '/IM', 'python3.exe'], 
                         capture_output=True, check=False)
        else:
            # Linux/Mac
            subprocess.run(['pkill', '-f', 'toyota_bot'], check=False)
        
        time.sleep(2)  # Wait for processes to terminate
        print("🧹 Cleaned up any existing bot processes")
    except Exception as e:
        print(f"⚠️ Warning: Could not clean up processes: {e}")

def main():
    """Start the bot with conflict prevention"""
    print("🤖 Starting Toyota Bot...")
    
    # Kill any existing instances first
    kill_existing_bots()
    
    # Remove any lock files
    lock_file = Path("toyota_bot.lock")
    if lock_file.exists():
        lock_file.unlink()
        print("🔓 Removed old lock file")
    
    # Start the bot
    print("🚀 Launching toyota_bot_fixed.py...")
    try:
        subprocess.run([sys.executable, 'toyota_bot_fixed.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == '__main__':
    main()