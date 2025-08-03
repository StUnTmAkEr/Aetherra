# twitch_client.py
"""
Twitch IRC Client
=================

Core IRC client for connecting to Twitch chat and handling messages.
This module handles the low-level IRC protocol communication with Twitch.
"""

import socket
import ssl
import time
import threading
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime, timedelta

from config import config


class TwitchIRCClient:
    """IRC client for connecting to Twitch chat"""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        self.message_handlers: list[Callable] = []
        self.command_handlers: Dict[str, Callable] = {}
        
        # Rate limiting
        self.message_queue = []
        self.last_message_time = datetime.now()
        self.messages_sent_count = 0
        self.rate_limit_reset_time = datetime.now()
        
        # Setup logging
        self.logger = logging.getLogger("TwitchIRC")
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        if config.LOG_TO_FILE:
            handler = logging.FileHandler(config.LOG_FILE)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def connect(self) -> bool:
        """Connect to Twitch IRC server"""
        try:
            # Validate configuration
            is_valid, errors = config.validate_config()
            if not is_valid:
                self.logger.error("Configuration validation failed:")
                for error in errors:
                    self.logger.error(f"  - {error}")
                return False
            
            self.logger.info("Connecting to Twitch IRC...")
            
            # Create socket
            server, port = config.get_irc_server()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if config.USE_SSL:
                context = ssl.create_default_context()
                self.socket = context.wrap_socket(self.socket, server_hostname=server)
            
            # Connect to server
            self.socket.connect((server, port))
            self.logger.info(f"Connected to {server}:{port}")
            
            # Send authentication
            self._send_raw(f"PASS {config.get_oauth_token()}")
            self._send_raw(f"NICK {config.BOT_USERNAME}")
            
            # Request capabilities
            self._send_raw("CAP REQ :twitch.tv/membership")
            self._send_raw("CAP REQ :twitch.tv/tags")
            self._send_raw("CAP REQ :twitch.tv/commands")
            
            # Join channel
            channel = config.CHANNEL if config.CHANNEL.startswith("#") else f"#{config.CHANNEL}"
            self._send_raw(f"JOIN {channel}")
            
            self.connected = True
            self.running = True
            self.logger.info(f"Successfully joined channel: {channel}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Twitch IRC"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
                self.logger.info("Disconnected from Twitch IRC")
            except:
                pass
    
    def _send_raw(self, message: str):
        """Send raw IRC message"""
        if not self.socket:
            return False
            
        try:
            encoded_message = f"{message}\r\n".encode('utf-8')
            self.socket.send(encoded_message)
            self.logger.debug(f"Sent: {message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    def send_message(self, message: str, channel: Optional[str] = None) -> bool:
        """Send a chat message with rate limiting"""
        if not self.connected:
            self.logger.warning("Cannot send message: not connected")
            return False
        
        # Use default channel if not specified
        if not channel:
            channel = config.CHANNEL if config.CHANNEL.startswith("#") else f"#{config.CHANNEL}"
        
        # Check rate limiting
        if not self._check_rate_limit():
            self.logger.warning("Rate limit exceeded, message queued")
            self.message_queue.append((message, channel))
            return False
        
        # Truncate message if too long
        if len(message) > config.MAX_MESSAGE_LENGTH:
            message = message[:config.MAX_MESSAGE_LENGTH-3] + "..."
            self.logger.warning("Message truncated due to length limit")
        
        # Send the message
        irc_message = f"PRIVMSG {channel} :{message}"
        success = self._send_raw(irc_message)
        
        if success:
            self._update_rate_limit()
            self.logger.info(f"Sent message to {channel}: {message}")
        
        return success
    
    def _check_rate_limit(self) -> bool:
        """Check if we can send a message based on rate limits"""
        now = datetime.now()
        
        # Reset counter if window has passed
        if now >= self.rate_limit_reset_time:
            self.messages_sent_count = 0
            self.rate_limit_reset_time = now + timedelta(seconds=config.RATE_LIMIT_WINDOW)
        
        return self.messages_sent_count < config.RATE_LIMIT_MESSAGES
    
    def _update_rate_limit(self):
        """Update rate limiting counters"""
        self.messages_sent_count += 1
        self.last_message_time = datetime.now()
    
    def add_message_handler(self, handler: Callable):
        """Add a message handler function"""
        self.message_handlers.append(handler)
    
    def add_command_handler(self, command: str, handler: Callable):
        """Add a command handler for specific commands"""
        command = command.lower().lstrip(config.COMMAND_PREFIX)
        self.command_handlers[command] = handler
        self.logger.info(f"Added command handler for: {config.COMMAND_PREFIX}{command}")
    
    def listen(self):
        """Main message listening loop"""
        if not self.connected:
            self.logger.error("Cannot listen: not connected")
            return
        
        self.logger.info("Starting message listener...")
        buffer = ""
        
        while self.running:
            try:
                # Process queued messages
                self._process_message_queue()
                
                # Receive data
                data = self.socket.recv(2048).decode('utf-8', errors='ignore')
                if not data:
                    self.logger.warning("No data received, connection may be lost")
                    break
                
                buffer += data
                
                # Process complete lines
                while '\r\n' in buffer:
                    line, buffer = buffer.split('\r\n', 1)
                    if line:
                        self._handle_irc_message(line)
                        
            except ConnectionResetError:
                self.logger.error("Connection reset by server")
                break
            except Exception as e:
                self.logger.error(f"Error in listen loop: {e}")
                time.sleep(1)  # Brief pause before continuing
        
        self.logger.info("Message listener stopped")
        self.disconnect()
    
    def _process_message_queue(self):
        """Process queued messages if rate limit allows"""
        while self.message_queue and self._check_rate_limit():
            message, channel = self.message_queue.pop(0)
            self.send_message(message, channel)
    
    def _handle_irc_message(self, raw_message: str):
        """Handle incoming IRC messages"""
        # Always log incoming messages for debugging
        print(f"[DEBUG] Received: {raw_message}")
        self.logger.debug(f"Received: {raw_message}")
        
        # Handle PING
        if raw_message.startswith("PING"):
            pong_message = raw_message.replace("PING", "PONG")
            self._send_raw(pong_message)
            return
        
        # Parse message
        message_data = self._parse_irc_message(raw_message)
        if not message_data:
            return
        
        # Handle chat messages
        if message_data.get('command') == 'PRIVMSG':
            self._handle_chat_message(message_data)
    
    def _parse_irc_message(self, raw_message: str) -> Optional[Dict[str, Any]]:
        """Parse IRC message into components with Twitch IRCv3 tags support"""
        try:
            # Handle Twitch IRCv3 tags (format: @tags :prefix COMMAND params :message)
            tags = {}
            message_part = raw_message
            
            # Extract tags if present
            if raw_message.startswith('@'):
                tag_end = raw_message.find(' ')
                if tag_end != -1:
                    tag_string = raw_message[1:tag_end]
                    message_part = raw_message[tag_end + 1:]
                    
                    # Parse tags
                    for tag in tag_string.split(';'):
                        if '=' in tag:
                            key, value = tag.split('=', 1)
                            tags[key] = value
            
            # Parse the main IRC message
            parts = message_part.split(' ')
            
            if len(parts) < 3:
                return None
            
            # Extract user info
            prefix = parts[0] if parts[0].startswith(':') else None
            command_idx = 1 if prefix else 0
            command = parts[command_idx]
            
            username = None
            if prefix and '!' in prefix:
                username = prefix[1:].split('!')[0]
            
            # Extract channel and message
            channel = None
            message = None
            
            if command == 'PRIVMSG' and len(parts) >= command_idx + 3:
                channel = parts[command_idx + 1]
                message_start = message_part.find(':', 1 if prefix else 0)
                if message_start != -1:
                    message = message_part[message_start + 1:]
            
            print(f"[DEBUG] Parsed message - username: {username}, channel: {channel}, message: {message}")
            
            return {
                'raw': raw_message,
                'tags': tags,
                'username': username,
                'command': command,
                'channel': channel,
                'message': message
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse message: {e}")
            return None
    
    def _handle_chat_message(self, message_data: Dict[str, Any]):
        """Handle incoming chat messages"""
        username = message_data.get('username')
        channel = message_data.get('channel')
        message = message_data.get('message')
        
        if not all([username, channel, message]):
            return
        
        print(f"[DEBUG] Chat message: [{channel}] {username}: {message}")
        self.logger.info(f"[{channel}] {username}: {message}")
        
        # Check for commands
        if message.startswith(config.COMMAND_PREFIX):
            print(f"[DEBUG] Detected command: {message}")
            self._handle_command(username, channel, message, message_data)
        
        # Call message handlers
        for handler in self.message_handlers:
            try:
                handler(username, channel, message, message_data)
            except Exception as e:
                self.logger.error(f"Error in message handler: {e}")
    
    def _handle_command(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle bot commands"""
        command_part = message[len(config.COMMAND_PREFIX):].split(' ')[0].lower()
        print(f"[DEBUG] Command detected: '{command_part}' from {username}")
        
        if command_part in self.command_handlers:
            try:
                print(f"[DEBUG] Executing command handler for: {command_part}")
                self.command_handlers[command_part](username, channel, message, message_data)
            except Exception as e:
                self.logger.error(f"Error in command handler '{command_part}': {e}")
        else:
            print(f"[DEBUG] No handler found for command: {command_part}")
    
    def start_async(self):
        """Start the bot in a separate thread"""
        if self.connect():
            listener_thread = threading.Thread(target=self.listen, daemon=True)
            listener_thread.start()
            return listener_thread
        return None
