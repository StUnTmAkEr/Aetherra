# config.py
"""
Twitch Bot Configuration
========================

Configuration settings for the Aetherra Twitch Bot integration.
This file contains all the necessary settings for connecting to Twitch IRC
and integrating with the Aetherra AI system.
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TwitchConfig:
    """Configuration class for Twitch bot settings"""
    
    def __init__(self):
        # Twitch IRC Connection Settings
        self.IRC_SERVER = "irc.chat.twitch.tv"
        self.IRC_PORT = 6667
        self.IRC_SSL_PORT = 6697
        self.USE_SSL = True
        
        # Twitch Application Credentials (from dev.twitch.tv)
        self.CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
        self.CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
        
        # Bot credentials (from OAuth flow)
        self.BOT_USERNAME = os.getenv("TWITCH_USERNAME", "")
        self.ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN", "")
        self.REFRESH_TOKEN = os.getenv("TWITCH_REFRESH_TOKEN", "")
        self.CHANNEL = os.getenv("TWITCH_CHANNEL", "")
        
        # Bot behavior settings
        self.COMMAND_PREFIX = "!"
        self.RATE_LIMIT_MESSAGES = 20  # Messages per 30 seconds
        self.RATE_LIMIT_WINDOW = 30    # Time window in seconds
        
        # Aetherra AI Integration
        self.ENABLE_AI_RESPONSES = True
        self.AI_RESPONSE_CHANCE = 0.3  # 30% chance to respond with AI
        self.MAX_MESSAGE_LENGTH = 500  # Twitch message limit
        
        # Logging
        self.LOG_LEVEL = "INFO"
        self.LOG_TO_FILE = True
        self.LOG_FILE = "twitchbot.log"
        
        # Token file for persistence
        self.TOKEN_FILE = "twitch_token.json"
        
        # Load from token file if available
        self._load_from_token_file()
    
    def _load_from_token_file(self):
        """Load configuration from saved token file (only if env vars not set)"""
        try:
            if os.path.exists(self.TOKEN_FILE):
                with open(self.TOKEN_FILE, 'r') as f:
                    token_data = json.load(f)
                
                # Only update config with saved data if env vars are not set
                if 'client_id' in token_data and not self.CLIENT_ID:
                    self.CLIENT_ID = token_data['client_id']
                if 'client_secret' in token_data and not self.CLIENT_SECRET:
                    self.CLIENT_SECRET = token_data['client_secret']
                if 'access_token' in token_data and not self.ACCESS_TOKEN:
                    self.ACCESS_TOKEN = token_data['access_token']
                if 'refresh_token' in token_data and not self.REFRESH_TOKEN:
                    self.REFRESH_TOKEN = token_data['refresh_token']
                if 'username' in token_data and not self.BOT_USERNAME:
                    self.BOT_USERNAME = token_data['username']
                if 'channel' in token_data and not self.CHANNEL:
                    self.CHANNEL = token_data['channel']
                    
        except Exception as e:
            print(f"Warning: Could not load token file: {e}")
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate that all required configuration is set"""
        errors = []
        
        if not self.CLIENT_ID:
            errors.append("Client ID not set (TWITCH_CLIENT_ID)")
        
        if not self.CLIENT_SECRET:
            errors.append("Client Secret not set (TWITCH_CLIENT_SECRET)")
        
        if not self.BOT_USERNAME:
            errors.append("Bot username not set (TWITCH_BOT_USERNAME)")
        
        if not self.ACCESS_TOKEN:
            errors.append("Access token not set (TWITCH_ACCESS_TOKEN)")
            
        if not self.CHANNEL:
            errors.append("Channel not set (TWITCH_CHANNEL)")
            
        return len(errors) == 0, errors
    
    def set_oauth_credentials(self, client_id: str, client_secret: str, access_token: str, 
                             username: str, refresh_token: str = None):
        """Set OAuth credentials from OAuth flow"""
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.ACCESS_TOKEN = access_token
        self.BOT_USERNAME = username
        if refresh_token:
            self.REFRESH_TOKEN = refresh_token
    
    def set_channel(self, channel: str):
        """Set the channel to join"""
        self.CHANNEL = channel.lower().replace("#", "")
    
    def get_oauth_token(self) -> str:
        """Get the OAuth token in the format expected by IRC"""
        return f"oauth:{self.ACCESS_TOKEN}"
    
    def get_irc_server(self) -> tuple[str, int]:
        """Get the appropriate IRC server and port"""
        if self.USE_SSL:
            return self.IRC_SERVER, self.IRC_SSL_PORT
        return self.IRC_SERVER, self.IRC_PORT
    
    def save_to_token_file(self):
        """Save current configuration to token file"""
        try:
            token_data = {
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET,
                'access_token': self.ACCESS_TOKEN,
                'refresh_token': self.REFRESH_TOKEN,
                'username': self.BOT_USERNAME,
                'channel': self.CHANNEL
            }
            
            with open(self.TOKEN_FILE, 'w') as f:
                json.dump(token_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save token file: {e}")

# Global config instance
config = TwitchConfig()
