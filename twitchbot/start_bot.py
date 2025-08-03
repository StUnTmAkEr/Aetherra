#!/usr/bin/env python3
"""
Direct Bot Starter
==================

Starts the Aetherra Twitch Bot directly without interactive menus.
This script assumes the bot is already configured.
"""

import sys
import os
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in the twitchbot directory first, then parent
    env_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),  # twitchbot/.env
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')  # parent/.env
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"✅ Loaded environment variables from {env_path}")
            env_loaded = True
            break
    
    if not env_loaded:
        print(f"⚠️ No .env file found. Searched: {env_paths}")
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables only.")

# Add parent directory to path for Aetherra imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aetherra_bot import AetherraBot
from config import TwitchConfig

# Initialize config
config = TwitchConfig()

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8') if config.LOG_TO_FILE else logging.NullHandler()
        ]
    )

def main():
    print("🤖 Starting Aetherra Twitch Bot...")
    
    # Check configuration before starting
    print("🔧 Checking bot configuration...")
    is_valid, errors = config.validate_config()
    
    if not is_valid:
        print("❌ Bot configuration is incomplete!")
        print("🔧 Please complete setup first:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("💡 To fix this:")
        print("1. Run 'python main.py' for interactive setup")
        print("2. Or update your .env file with the missing credentials")
        print("3. Get Twitch credentials from: https://dev.twitch.tv/console/apps")
        return
    
    print("✅ Configuration validated successfully")
    
    # Setup logging
    setup_logging()
    
    # Create and start bot
    bot = AetherraBot()
    
    try:
        print("🔗 Connecting to Twitch...")
        bot.start()
        print("✅ Bot started successfully!")
        print(f"🎯 Monitoring channel: #{config.CHANNEL}")
        print("💬 Send commands like: !hello, !help, !status")
        print("⚡ Press Ctrl+C to stop the bot")
        
        # Keep the bot running - use a simple loop
        import time
        while bot.running:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
        bot.stop()
        print("✅ Bot stopped successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.error(f"Bot error: {e}")

if __name__ == "__main__":
    main()
