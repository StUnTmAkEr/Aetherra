# main.py
"""
Aetherra Twitch Bot Launcher
============================

Main entry point for running the Aetherra Twitch Bot.
This script handles bot initialization, configuration, and provides
an interactive interface for managing the bot.
"""

import os
import sys
import time
import signal
import logging
from typing import Optional

from aetherra_bot import AetherraBot
from config import config


class BotLauncher:
    """Main launcher for the Twitch bot"""
    
    def __init__(self):
        self.bot: Optional[AetherraBot] = None
        self.setup_logging()
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(config.LOG_FILE) if config.LOG_TO_FILE else logging.NullHandler()
            ]
        )
        
        self.logger = logging.getLogger("BotLauncher")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal, stopping bot...")
            if self.bot:
                self.bot.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def check_configuration(self) -> bool:
        """Check and prompt for missing configuration"""
        self.logger.info("Checking bot configuration...")
        
        is_valid, errors = config.validate_config()
        
        if not is_valid:
            self.logger.warning("Configuration incomplete. Setting up credentials...")
            self.interactive_setup()
            
            # Re-validate after setup
            is_valid, errors = config.validate_config()
            
            if not is_valid:
                self.logger.error("Configuration still invalid after setup:")
                for error in errors:
                    self.logger.error(f"  - {error}")
                return False
        
        self.logger.info("Configuration validated successfully")
        return True
    
    def interactive_setup(self):
        """Interactive setup for missing configuration"""
        print("\n" + "="*60)
        print("🤖 AETHERRA TWITCH BOT SETUP")
        print("="*60)
        print()
        print("Welcome to the Aetherra Twitch Bot! Let's get you set up.")
        print()
        print("You have two options:")
        print("1. Complete OAuth setup (recommended)")
        print("2. Manual configuration")
        print()
        
        choice = input("Choose setup method (1-2): ").strip()
        
        if choice == "1":
            self._oauth_setup()
        else:
            self._manual_setup()
    
    def _oauth_setup(self):
        """Complete OAuth setup using the new flow"""
        from oauth_helper import interactive_oauth_setup
        
        print("\n🔑 Starting OAuth setup...")
        result = interactive_oauth_setup()
        
        if result:
            # Update configuration
            config.set_oauth_credentials(
                result['client_id'],
                result['client_secret'], 
                result['access_token'],
                result['username'],
                result.get('refresh_token')
            )
            
            # Get channel if not set
            if not config.CHANNEL:
                channel = input("\nEnter the channel name to join (without #): ").strip()
                if channel:
                    config.set_channel(channel)
            
            # Save configuration
            config.save_to_token_file()
            print("✅ Configuration saved!")
        else:
            print("❌ OAuth setup failed")
    
    def _manual_setup(self):
        """Manual setup (legacy method)"""
        print("\n⚠️  Manual Setup (Not Recommended)")
        print("For best results, use OAuth setup instead.")
        print()
        
        # Get application credentials
        if not config.CLIENT_ID:
            client_id = input("Enter your Client ID: ").strip()
            if client_id:
                config.CLIENT_ID = client_id
        
        if not config.CLIENT_SECRET:
            client_secret = input("Enter your Client Secret: ").strip()
            if client_secret:
                config.CLIENT_SECRET = client_secret
        
        # Get bot username
        if not config.BOT_USERNAME:
            username = input("Enter your bot's Twitch username: ").strip()
            if username:
                config.BOT_USERNAME = username
        
        # Get access token
        if not config.ACCESS_TOKEN:
            print()
            print("⚠️  You need an access token. Options:")
            print("1. Use OAuth setup instead (recommended)")
            print("2. Get token manually from Twitch API")
            print()
            
            access_token = input("Enter your access token (or leave blank to use OAuth): ").strip()
            if access_token:
                config.ACCESS_TOKEN = access_token
            else:
                print("Switching to OAuth setup...")
                self._oauth_setup()
                return
        
        # Get channel name
        if not config.CHANNEL:
            channel = input("Enter the channel name to join (without #): ").strip()
            if channel:
                config.set_channel(channel)
        
        # Save configuration
        config.save_to_token_file()
        print("✅ Configuration complete!")
    
    def display_status(self):
        """Display current bot status"""
        print("\n" + "="*60)
        print("🤖 AETHERRA TWITCH BOT STATUS")
        print("="*60)
        print(f"Client ID: {config.CLIENT_ID[:8]}..." if config.CLIENT_ID else "Client ID: ❌ Missing")
        print(f"Client Secret: {'✅ Set' if config.CLIENT_SECRET else '❌ Missing'}")
        print(f"Bot Username: {config.BOT_USERNAME}")
        print(f"Channel: #{config.CHANNEL}")
        print(f"Access Token: {'✅ Set' if config.ACCESS_TOKEN else '❌ Missing'}")
        print(f"Refresh Token: {'✅ Set' if config.REFRESH_TOKEN else '❌ Missing'}")
        print(f"AI Features: {'✅ Available' if config.ENABLE_AI_RESPONSES else '❌ Disabled'}")
        print(f"Command Prefix: {config.COMMAND_PREFIX}")
        print(f"Rate Limit: {config.RATE_LIMIT_MESSAGES} messages per {config.RATE_LIMIT_WINDOW}s")
        print("="*60)
        print()
    
    def run_interactive(self):
        """Run the bot with an interactive menu"""
        while True:
            print("\n" + "="*40)
            print("🤖 AETHERRA TWITCH BOT")
            print("="*40)
            print("1. Start Bot")
            print("2. Configure Settings")
            print("3. View Status")
            print("4. Test Connection")
            print("5. Exit")
            print("="*40)
            
            choice = input("Select an option (1-5): ").strip()
            
            if choice == "1":
                self.start_bot()
            elif choice == "2":
                self.interactive_setup()
            elif choice == "3":
                self.display_status()
            elif choice == "4":
                self.test_connection()
            elif choice == "5":
                print("Goodbye! 👋")
                break
            else:
                print("Invalid option. Please try again.")
    
    def test_connection(self):
        """Test the bot connection without starting full bot"""
        print("\n🔧 Testing connection...")
        
        if not self.check_configuration():
            print("❌ Cannot test connection - configuration invalid")
            return
        
        # Create a temporary bot instance for testing
        test_bot = AetherraBot()
        
        print("Attempting to connect to Twitch IRC...")
        if test_bot.irc_client.connect():
            print("✅ Connection successful!")
            print(f"✅ Joined channel: #{config.CHANNEL}")
            
            # Send a test message
            test_message = "🤖 Connection test successful!"
            if test_bot.irc_client.send_message(test_message):
                print(f"✅ Test message sent: {test_message}")
            
            time.sleep(2)
            test_bot.stop()
            print("✅ Test completed successfully!")
        else:
            print("❌ Connection failed! Check your configuration.")
    
    def start_bot(self):
        """Start the main bot"""
        if not self.check_configuration():
            print("❌ Cannot start bot - configuration invalid")
            return
        
        print("\n🚀 Starting Aetherra Twitch Bot...")
        
        try:
            self.bot = AetherraBot()
            
            if self.bot.start():
                print("✅ Bot started successfully!")
                print(f"🎯 Monitoring channel: #{config.CHANNEL}")
                print("Press Ctrl+C to stop the bot")
                
                # Keep the bot running
                try:
                    while self.bot.is_running():
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping bot...")
                    self.bot.stop()
                    print("✅ Bot stopped successfully!")
            else:
                print("❌ Failed to start bot")
                
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            print(f"❌ Error starting bot: {e}")
    
    def run_headless(self):
        """Run the bot in headless mode (no interactive menu)"""
        if not self.check_configuration():
            self.logger.error("Cannot start bot - configuration invalid")
            return False
        
        self.logger.info("Starting bot in headless mode...")
        
        try:
            self.bot = AetherraBot()
            
            if self.bot.start():
                self.logger.info("Bot started successfully in headless mode")
                
                # Keep running until interrupted
                try:
                    while self.bot.is_running():
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
                
                self.bot.stop()
                return True
            else:
                self.logger.error("Failed to start bot")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in headless mode: {e}")
            return False


def main():
    """Main entry point"""
    launcher = BotLauncher()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--headless":
            # Run in headless mode
            launcher.run_headless()
        elif sys.argv[1] == "--test":
            # Run connection test
            launcher.test_connection()
        elif sys.argv[1] == "--help":
            print("Aetherra Twitch Bot")
            print("Usage:")
            print("  python main.py           - Run with interactive menu")
            print("  python main.py --headless - Run in headless mode")
            print("  python main.py --test     - Test connection only")
            print("  python main.py --help     - Show this help")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        # Run with interactive menu
        launcher.run_interactive()


if __name__ == "__main__":
    main()
