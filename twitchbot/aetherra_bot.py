# aetherra_bot.py
"""
Aetherra Twitch Bot
===================

Main bot class that integrates Twitch IRC client with Aetherra AI capabilities.
This bot can respond to chat messages using the Aetherra conversation system.
"""

import sys
import os
import random
import time
import threading
import logging
import json
from typing import Optional, Dict, Any

# Add parent directory to path for Aetherra imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twitch_client import TwitchIRCClient
from config import config

# Try to import Aetherra components
try:
    from Aetherra.lyrixa.conversation_manager import LyrixaEnhancedConversationManager
    from Aetherra.lyrixa.enhanced_conversation_manager import EnhancedConversationManager
    AETHERRA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Aetherra components not available: {e}")
    AETHERRA_AVAILABLE = False


class AetherraBot:
    """Main Twitch bot with Aetherra AI integration"""
    
    def __init__(self):
        self.irc_client = TwitchIRCClient()
        self.conversation_manager = None
        self.running = False
        
        # Bot state
        self.user_contexts: Dict[str, Dict] = {}  # Per-user conversation context
        self.channel_activity: Dict[str, int] = {}  # Track channel activity
        
        # Add cooldown tracking to prevent spam
        self.last_response_time: Dict[str, float] = {}  # Track last response per user
        self.response_cooldown = 3.0  # 3 seconds between responses per user
        
        # Commands file path
        self.commands_file = os.path.join(os.path.dirname(__file__), 'commands.json')
        
        # Setup logging
        self.logger = logging.getLogger("AetherraBot")
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # Initialize Aetherra AI if available
        if AETHERRA_AVAILABLE and config.ENABLE_AI_RESPONSES:
            self._initialize_ai()
        
        # Setup message and command handlers
        self._setup_handlers()
    
    def _initialize_ai(self):
        """Initialize the Aetherra conversation manager"""
        try:
            self.logger.info("Initializing Aetherra AI conversation manager...")
            
            # Get OpenAI API key from environment
            openai_api_key = os.getenv('OPENAI_API_KEY', '')
            
            # Create config for conversation manager
            ai_config = {
                "openai_api_key": openai_api_key,
                "openai_model": "gpt-3.5-turbo",
                "max_tokens": 150,  # Shorter responses for chat
                "temperature": 0.8,  # More creative for chat
                "memory_enabled": True
            }
            
            # Try the enhanced conversation manager first
            try:
                self.conversation_manager = EnhancedConversationManager(config=ai_config)
                self.logger.info("Using EnhancedConversationManager")
                self.logger.info(f"OpenAI API key configured: {'Yes' if openai_api_key else 'No'}")
            except:
                # Fallback to basic conversation manager
                self.conversation_manager = LyrixaEnhancedConversationManager()
                self.logger.info("Using LyrixaEnhancedConversationManager")
            
            self.logger.info("Aetherra AI initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Aetherra AI: {e}")
            self.conversation_manager = None
    
    def _setup_handlers(self):
        """Setup message and command handlers"""
        # Add message handler
        self.irc_client.add_message_handler(self._handle_message)
        
        # Add basic commands
        self.irc_client.add_command_handler("hello", self._cmd_hello)
        self.irc_client.add_command_handler("help", self._cmd_help)
        self.irc_client.add_command_handler("ai", self._cmd_ai)
        self.irc_client.add_command_handler("status", self._cmd_status)
        self.irc_client.add_command_handler("ping", self._cmd_ping)
        
        # Add moderator commands
        self.irc_client.add_command_handler("addcmd", self._cmd_addcmd)
        self.irc_client.add_command_handler("delcmd", self._cmd_delcmd)
        self.irc_client.add_command_handler("togglecmd", self._cmd_togglecmd)
        
        if AETHERRA_AVAILABLE:
            self.irc_client.add_command_handler("ask", self._cmd_ask)
            self.irc_client.add_command_handler("chat", self._cmd_chat)
        
        # Initialize dynamic commands storage
        self.dynamic_commands: Dict[str, str] = {
            'hello': 'Hello there! Welcome to the stream!',
            'help': 'Available commands: !hello, !help, !status, !ping',  # This will be dynamically updated
            'status': 'Bot is running and ready to chat!',
            'ping': 'Pong! Bot is responsive.'
        }
        
        # Add AI commands to dynamic_commands if available
        if AETHERRA_AVAILABLE:
            self.dynamic_commands['ask'] = 'Ask me a question! Usage: !ask [your question]'
            self.dynamic_commands['chat'] = 'Chat with me! Usage: !chat [your message]'
        
        # Track enabled/disabled state for commands
        self.command_enabled: Dict[str, bool] = {
            'hello': True,
            'help': True,
            'status': True,
            'ping': True
        }
        
        # Add AI commands to enabled tracking if available
        if AETHERRA_AVAILABLE:
            self.command_enabled['ask'] = True
            self.command_enabled['chat'] = True
        
        # Load saved commands from file
        self._load_commands()
        
        # Add dynamic command handler
        self._register_dynamic_commands()
    
    def _load_commands(self):
        """Load commands from the commands file"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                
                # Handle both old format (just commands) and new format (with enabled state)
                if isinstance(saved_data, dict) and 'commands' in saved_data:
                    # New format with enabled state
                    saved_commands = saved_data.get('commands', {})
                    saved_enabled = saved_data.get('enabled', {})
                else:
                    # Old format - just commands
                    saved_commands = saved_data
                    saved_enabled = {}
                
                # Update dynamic_commands with saved commands, but skip built-in commands that have special logic
                built_in_commands = {'help', 'ask', 'chat'}  # Commands that should not be overridden from file
                loaded_count = 0
                for cmd, response in saved_commands.items():
                    if cmd not in built_in_commands:
                        self.dynamic_commands[cmd] = response
                        # Set enabled state - default to True if not specified
                        self.command_enabled[cmd] = saved_enabled.get(cmd, True)
                        loaded_count += 1
                
                self.logger.info(f"Loaded {loaded_count} commands from {self.commands_file} (skipped {len(saved_commands) - loaded_count} built-ins)")
            else:
                self.logger.info("No saved commands file found, using defaults")
        except Exception as e:
            self.logger.error(f"Failed to load commands: {e}")
    
    def _save_commands(self):
        """Save commands to the commands file"""
        try:
            # Only save custom commands, not built-in ones with special logic
            built_in_commands = {'help', 'ask', 'chat'}  # Commands that should not be saved to file
            commands_to_save = {cmd: response for cmd, response in self.dynamic_commands.items() 
                              if cmd not in built_in_commands}
            enabled_to_save = {cmd: enabled for cmd, enabled in self.command_enabled.items() 
                             if cmd not in built_in_commands}
            
            # Save in new format with enabled state
            data_to_save = {
                'commands': commands_to_save,
                'enabled': enabled_to_save
            }
            
            with open(self.commands_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(commands_to_save)} commands to {self.commands_file}")
        except Exception as e:
            self.logger.error(f"Failed to save commands: {e}")
    
    def _register_dynamic_commands(self):
        """Register dynamic command handlers"""
        for command_name in self.dynamic_commands.keys():
            if command_name not in ['hello', 'help', 'ai', 'status', 'ping', 'ask', 'chat']:
                self.irc_client.add_command_handler(command_name, self._handle_dynamic_command)
    
    def add_dynamic_command(self, command: str, response: str, enabled: bool = True):
        """Add or update a dynamic command"""
        command = command.lower().strip()
        if enabled:
            self.dynamic_commands[command] = response
            # Register the command handler if it's not a built-in command
            if command not in ['hello', 'help', 'ai', 'status', 'ping', 'ask', 'chat']:
                self.irc_client.add_command_handler(command, self._handle_dynamic_command)
            self.logger.info(f"Added dynamic command: !{command}")
        else:
            # Add the command but don't register handler if it's disabled
            self.dynamic_commands[command] = response
            self.logger.info(f"Added dynamic command: !{command} (disabled)")
        
        # Set enabled state
        self.command_enabled[command] = enabled
        # Save to file
        self._save_commands()
        return True
    
    def set_command_enabled(self, command: str, enabled: bool):
        """Enable or disable a command"""
        command = command.lower().strip()
        if command in self.dynamic_commands:
            old_state = self.command_enabled.get(command, True)
            self.command_enabled[command] = enabled
            self.logger.info(f"Command !{command} {'enabled' if enabled else 'disabled'} (was {'enabled' if old_state else 'disabled'})")
            print(f"[DEBUG] Command toggle: !{command} -> {'enabled' if enabled else 'disabled'}")
            print(f"[DEBUG] Updated command_enabled: {self.command_enabled}")
            # Save to file
            self._save_commands()
            return True
        else:
            self.logger.warning(f"Tried to toggle unknown command: !{command}")
            print(f"[DEBUG] Unknown command toggle attempt: !{command}")
            print(f"[DEBUG] Available commands: {list(self.dynamic_commands.keys())}")
            return False
    
    def remove_dynamic_command(self, command: str):
        """Remove a dynamic command"""
        command = command.lower().strip()
        if command in self.dynamic_commands:
            del self.dynamic_commands[command]
            # Note: We can't easily remove command handlers from the IRC client
            # but we can check if the command exists in our dynamic_commands dict
            self.logger.info(f"Removed dynamic command: !{command}")
            # Save to file
            self._save_commands()
            return True
        return False
    
    def get_dynamic_commands(self) -> Dict[str, str]:
        """Get all dynamic commands"""
        return self.dynamic_commands.copy()
    
    def _handle_dynamic_command(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle dynamic commands"""
        command_part = message[len(config.COMMAND_PREFIX):].split(' ')[0].lower()
        print(f"[DEBUG] Dynamic command triggered: !{command_part} by {username}")
        print(f"[DEBUG] Available commands: {list(self.dynamic_commands.keys())}")
        print(f"[DEBUG] Command enabled states: {self.command_enabled}")
        
        if command_part in self.dynamic_commands:
            # Check if the command is enabled
            is_enabled = self.command_enabled.get(command_part, True)
            print(f"[DEBUG] Command !{command_part} enabled state: {is_enabled}")
            
            if is_enabled:
                response = self.dynamic_commands[command_part]
                print(f"[DEBUG] Sending response for !{command_part}: {response}")
                self.irc_client.send_message(response, channel)
            else:
                # Command is disabled - silently ignore or optionally send a message
                print(f"[DEBUG] Command !{command_part} is disabled, ignoring")
                self.logger.debug(f"Command !{command_part} is disabled, ignoring")
        else:
            print(f"[DEBUG] Command !{command_part} not found in dynamic_commands")
    
    def _handle_message(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle incoming chat messages"""
        # Don't respond to our own messages or system messages
        if (not username or 
            username.lower() == config.BOT_USERNAME.lower() or 
            username.lower() == 'stuntbot' or 
            username.startswith('tmi.') or
            message.startswith('@' + config.BOT_USERNAME.lower()) or  # Don't process responses to ourselves
            'stuntbot' in username.lower()):
            print(f"[DEBUG] Ignoring message from {username}: {message[:50]}...")
            return
        
        print(f"[DEBUG] Processing message from {username}: {message[:50]}...")
        
        # Update user context
        self._update_user_context(username, channel, message)
        
        # Update channel activity
        self.channel_activity[channel] = self.channel_activity.get(channel, 0) + 1
        
        # Check if we should respond with AI
        if (self.conversation_manager and 
            config.ENABLE_AI_RESPONSES and 
            self._should_respond_with_ai(username, channel, message)):
            
            self._generate_ai_response(username, channel, message)
    
    def _update_user_context(self, username: str, channel: str, message: str):
        """Update conversation context for a user"""
        if username not in self.user_contexts:
            self.user_contexts[username] = {
                'messages': [],
                'last_interaction': time.time(),
                'channel': channel
            }
        
        context = self.user_contexts[username]
        context['messages'].append({
            'message': message,
            'timestamp': time.time(),
            'channel': channel
        })
        
        # Keep only recent messages (last 10)
        if len(context['messages']) > 10:
            context['messages'] = context['messages'][-10:]
        
        context['last_interaction'] = time.time()
    
    def _should_respond_with_ai(self, username: str, channel: str, message: str) -> bool:
        """Determine if the bot should respond with AI"""
        # Don't respond to commands
        if message.startswith(config.COMMAND_PREFIX):
            return False
        
        # Check if bot is mentioned
        bot_mentioned = config.BOT_USERNAME.lower() in message.lower()
        
        # Random chance or if mentioned
        random_chance = random.random() < config.AI_RESPONSE_CHANCE
        
        return bot_mentioned or random_chance
    
    def _generate_ai_response(self, username: str, channel: str, message: str):
        """Generate an AI response using Aetherra"""
        if not self.conversation_manager:
            return
        
        # Check cooldown to prevent spam
        current_time = time.time()
        last_response = self.last_response_time.get(username, 0)
        if current_time - last_response < self.response_cooldown:
            print(f"[DEBUG] Cooldown active for {username}, skipping response")
            return
        
        # Update last response time
        self.last_response_time[username] = current_time
        
        try:
            # Get user context
            user_context = self.user_contexts.get(username, {})
            recent_messages = user_context.get('messages', [])
            
            # Build context for AI
            context_messages = []
            for msg_data in recent_messages[-3:]:  # Last 3 messages
                context_messages.append(msg_data['message'])
            
            # Create conversation context
            conversation_context = f"Twitch chat conversation with {username}. "
            if len(context_messages) > 1:
                conversation_context += f"Recent context: {' | '.join(context_messages[:-1])} | "
            conversation_context += f"Current message: {message}"
            
            # Generate response
            self.logger.info(f"Generating AI response for {username}: {message}")
            
            # Debug: check available methods
            available_methods = [method for method in dir(self.conversation_manager) if not method.startswith('_')]
            print(f"[DEBUG] Available conversation manager methods: {available_methods}")
            
            response = None
            
            # Check if we have OpenAI API key
            import os
            if not os.getenv('OPENAI_API_KEY'):
                print(f"[DEBUG] No OpenAI API key found, using local AI fallback")
                # Create a simple local AI response system for testing
                response = self._generate_local_ai_response(message, username)
            else:
                # Try different methods in order of preference
                if hasattr(self.conversation_manager, 'generate_response'):
                    print(f"[DEBUG] Using generate_response method")
                    try:
                        # Handle async method
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        response = loop.run_until_complete(self.conversation_manager.generate_response(message, context={'user': username}))
                        loop.close()
                        print(f"[DEBUG] Async generate_response completed successfully")
                    except Exception as e:
                        print(f"[DEBUG] Async call failed: {e}")
                        # Try synchronous call
                        try:
                            response = self.conversation_manager.generate_response(message)
                            if hasattr(response, '__await__'):
                                print(f"[DEBUG] Got coroutine, need to await it")
                                response = f"Hello {username}! I'm processing your question but need proper async handling."
                        except Exception as sync_e:
                            print(f"[DEBUG] Sync call also failed: {sync_e}")
                            response = None
                            
                elif hasattr(self.conversation_manager, 'process_conversation'):
                    print(f"[DEBUG] Using process_conversation method")
                    response = self.conversation_manager.process_conversation(message, username)
                elif hasattr(self.conversation_manager, 'get_response'):
                    print(f"[DEBUG] Using get_response method")
                    response = self.conversation_manager.get_response(message, context={'user': username})
                elif hasattr(self.conversation_manager, 'process_message'):
                    print(f"[DEBUG] Using process_message method")
                    response = self.conversation_manager.process_message(conversation_context)
                else:
                    print(f"[DEBUG] No suitable method found, using fallback")
                    response = f"Hello {username}! I'm an AI bot powered by Aetherra. How can I help?"
            
            print(f"[DEBUG] Raw AI response: {response}")
            
            # Handle different response formats from Aetherra
            if response and isinstance(response, dict):
                # Extract the actual response text from Aetherra's response format
                if 'response' in response:
                    response = response['response']
                    print(f"[DEBUG] Extracted response from dict: {response}")
                else:
                    print(f"[DEBUG] Dict response without 'response' key: {response}")
                    response = str(response)
            
            # Clean up response for Twitch
            if response and isinstance(response, str):
                # Remove excessive formatting
                response = response.replace('*', '').replace('_', '')
                
                # Ensure it's not too long
                if len(response) > config.MAX_MESSAGE_LENGTH:
                    response = response[:config.MAX_MESSAGE_LENGTH-3] + "..."
                
                # Add username prefix for context
                response = f"@{username} {response}"
                
                # Send the response
                self.irc_client.send_message(response, channel)
            else:
                print(f"[DEBUG] Invalid response received: {response}")
                fallback = f"@{username} Sorry, I couldn't process that question right now."
                self.irc_client.send_message(fallback, channel)
                
        except Exception as e:
            self.logger.error(f"Failed to generate AI response: {e}")
            print(f"[DEBUG] Exception in AI response generation: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_local_ai_response(self, message: str, username: str) -> str:
        """Generate a local AI-like response without requiring OpenAI API"""
        message_lower = message.lower()
        
        # Simple keyword-based responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return f"Hello {username}! Great to see you in the chat!"
        
        elif any(word in message_lower for word in ['42', 'meaning of life', 'universe']):
            return f"Ah, the meaning of 42! According to Douglas Adams' 'The Hitchhiker's Guide to the Galaxy', 42 is the Answer to the Ultimate Question of Life, the Universe, and Everything. But the real question is... what's the question? 🤔"
        
        elif any(word in message_lower for word in ['how are you', 'how do you feel']):
            return f"I'm doing great, {username}! I'm running smoothly and ready to chat. How are you doing today?"
        
        elif any(word in message_lower for word in ['what is', 'what are', 'define']):
            # Extract the topic after "what is" or similar
            for phrase in ['what is', 'what are', 'define']:
                if phrase in message_lower:
                    topic = message_lower.split(phrase, 1)[1].strip()
                    if topic:
                        return f"That's an interesting question about '{topic}', {username}! I'd love to give you a detailed answer, but I'm running in local mode. With an OpenAI API key, I could provide much more comprehensive responses!"
            return f"That's a great question, {username}! I'd need more context to give you a good answer."
        
        elif any(word in message_lower for word in ['help', 'commands']):
            return f"I can help you, {username}! Try commands like !hello, !status, !help, or ask me questions with !ask. I'm running in local mode, so responses are simple but functional!"
        
        elif any(word in message_lower for word in ['weather', 'time', 'date']):
            import datetime
            now = datetime.datetime.now()
            return f"I can't check live weather data, but I can tell you it's currently {now.strftime('%I:%M %p')} on {now.strftime('%B %d, %Y')}!"
        
        elif any(word in message_lower for word in ['game', 'play', 'fun']):
            import random
            games = [
                "How about we play 20 questions?",
                "Want to hear a joke? Why don't scientists trust atoms? Because they make up everything!",
                "Here's a riddle: What gets wetter the more it dries? (Answer: A towel!)",
                "Fun fact: Octopuses have three hearts and blue blood!"
            ]
            return f"{username}, {random.choice(games)}"
        
        elif any(word in message_lower for word in ['thank', 'thanks']):
            return f"You're very welcome, {username}! Happy to help anytime!"
        
        else:
            # Generic intelligent-sounding response
            responses = [
                f"That's a fascinating topic, {username}! I'm processing your message about '{message[:50]}...' in local mode.",
                f"Interesting perspective, {username}! I'd love to discuss this more deeply with full AI capabilities.",
                f"You've got me thinking, {username}! That's a great question about '{message[:30]}...'",
                f"I appreciate you sharing that, {username}! Let me think about your message...",
                f"Great point, {username}! I'm running in local mode, but I can still chat about '{message[:40]}...'"
            ]
            import random
            return random.choice(responses)

    def _is_moderator(self, username: str, message_data: Dict[str, Any]) -> bool:
        """Check if a user is a moderator or broadcaster"""
        # Check if user is the broadcaster (channel owner)
        if username.lower() == config.CHANNEL.lower().replace('#', ''):
            return True
        
        # Check tags for moderator badge
        tags = message_data.get('tags', {})
        if isinstance(tags, dict):
            # Check for mod badge
            badges = tags.get('badges', '')
            if 'moderator' in badges or 'broadcaster' in badges:
                return True
            
            # Check mod flag (some IRC clients use this)
            mod_flag = tags.get('mod', '0')
            if mod_flag == '1':
                return True
        
        # For testing purposes, you can add specific usernames here
        # moderator_list = ['your_mod_username', 'another_mod']
        # if username.lower() in moderator_list:
        #     return True
        
        return False

    # Command handlers
    def _cmd_hello(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !hello command"""
        print(f"[DEBUG] !hello command triggered by {username}, enabled: {self.command_enabled.get('hello', True)}")
        if not self.command_enabled.get('hello', True):
            print(f"[DEBUG] !hello command is disabled, returning")
            return  # Command is disabled
            
        if 'hello' in self.dynamic_commands:
            response = self.dynamic_commands['hello']
        else:
            responses = [
                f"Hello {username}! 👋",
                f"Hey there {username}! Welcome to the stream!",
                f"Greetings {username}! How are you doing?",
                f"Hi {username}! Nice to see you in chat!"
            ]
            response = random.choice(responses)
        print(f"[DEBUG] Sending !hello response: {response}")
        self.irc_client.send_message(response, channel)
    
    def _cmd_help(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !help command"""
        print(f"[DEBUG] !help command triggered by {username}, enabled: {self.command_enabled.get('help', True)}")
        if not self.command_enabled.get('help', True):
            print(f"[DEBUG] !help command is disabled, returning")
            return  # Command is disabled
            
        # Always build dynamic list of available commands
        commands = []
        
        # Add enabled commands from dynamic_commands
        for cmd in sorted(self.dynamic_commands.keys()):
            if self.command_enabled.get(cmd, True):  # Only show enabled commands
                commands.append(f"!{cmd}")
        
        # Add moderator commands if user is a moderator
        if self._is_moderator(username, message_data):
            commands.extend(["!addcmd", "!delcmd", "!togglecmd"])
        
        response = f"Available commands: {', '.join(commands)}"
        print(f"[DEBUG] Sending !help response: {response}")
        self.irc_client.send_message(response, channel)
    
    def _cmd_status(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !status command"""
        if not self.command_enabled.get('status', True):
            return  # Command is disabled
            
        if 'status' in self.dynamic_commands:
            response = self.dynamic_commands['status']
            self.irc_client.send_message(response, channel)
        else:
            ai_status = "✅ Enabled" if (AETHERRA_AVAILABLE and self.conversation_manager) else "❌ Disabled"
            active_users = len(self.user_contexts)
            status = f"@{username} Bot Status: Connected ✅ | AI: {ai_status} | Active Users: {active_users}"
            self.irc_client.send_message(status, channel)
    
    def _cmd_ping(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !ping command"""
        print(f"[DEBUG] !ping command triggered by {username}, enabled: {self.command_enabled.get('ping', True)}")
        if not self.command_enabled.get('ping', True):
            print(f"[DEBUG] !ping command is disabled, returning")
            return  # Command is disabled
            
        if 'ping' in self.dynamic_commands:
            response = self.dynamic_commands['ping']
        else:
            response = f"@{username} Pong! 🏓"
        print(f"[DEBUG] Sending !ping response: {response}")
        self.irc_client.send_message(response, channel)
    
    def _cmd_ai(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !ai command"""
        if not AETHERRA_AVAILABLE:
            self.irc_client.send_message(f"@{username} AI features are not available.", channel)
            return
        
        if not self.conversation_manager:
            self.irc_client.send_message(f"@{username} AI is currently unavailable.", channel)
            return
        
        self.irc_client.send_message(f"@{username} AI is powered by Aetherra! Use {config.COMMAND_PREFIX}ask or {config.COMMAND_PREFIX}chat to interact.", channel)
    
    def _cmd_ask(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !ask command"""
        print(f"[DEBUG] !ask command triggered by {username}, enabled: {self.command_enabled.get('ask', True)}")
        if not self.command_enabled.get('ask', True):
            print(f"[DEBUG] !ask command is disabled, returning")
            return  # Command is disabled
            
        if not AETHERRA_AVAILABLE or not self.conversation_manager:
            self.irc_client.send_message(f"@{username} AI is not available.", channel)
            return
        
        # Extract question from message
        parts = message.split(' ', 1)
        if len(parts) < 2:
            self.irc_client.send_message(f"@{username} Please ask a question! Example: {config.COMMAND_PREFIX}ask What is AI?", channel)
            return
        
        question = parts[1]
        print(f"[DEBUG] Sending !ask question to AI: {question}")
        self._generate_ai_response(username, channel, question)
    
    def _cmd_chat(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !chat command"""
        print(f"[DEBUG] !chat command triggered by {username}, enabled: {self.command_enabled.get('chat', True)}")
        if not self.command_enabled.get('chat', True):
            print(f"[DEBUG] !chat command is disabled, returning")
            return  # Command is disabled
            
        if not AETHERRA_AVAILABLE or not self.conversation_manager:
            self.irc_client.send_message(f"@{username} AI chat is not available.", channel)
            return
        
        # Extract chat message
        parts = message.split(' ', 1)
        if len(parts) < 2:
            self.irc_client.send_message(f"@{username} Say something! Example: {config.COMMAND_PREFIX}chat Hello there!", channel)
            return
        
        chat_message = parts[1]
        print(f"[DEBUG] Sending !chat message to AI: {chat_message}")
        self._generate_ai_response(username, channel, chat_message)
    
    # Moderator Commands
    def _cmd_addcmd(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !addcmd command (Moderator only)"""
        print(f"[DEBUG] !addcmd command triggered by {username}")
        
        # Check if user is a moderator
        if not self._is_moderator(username, message_data):
            self.irc_client.send_message(f"@{username} ⛔ This command is for moderators only.", channel)
            return
        
        # Parse command syntax: !addcmd <command_name> <response>
        parts = message.split(' ', 2)
        if len(parts) < 3:
            self.irc_client.send_message(f"@{username} Usage: !addcmd <command_name> <response>", channel)
            return
        
        command_name = parts[1].lower().strip()
        command_response = parts[2].strip()
        
        # Remove ! prefix if provided
        if command_name.startswith('!'):
            command_name = command_name[1:]
        
        # Check if it's a built-in command
        built_in_commands = {'hello', 'help', 'status', 'ping', 'ask', 'chat', 'ai', 'addcmd', 'delcmd', 'togglecmd'}
        if command_name in built_in_commands:
            self.irc_client.send_message(f"@{username} ⛔ Cannot override built-in command: !{command_name}", channel)
            return
        
        # Add the command
        success = self.add_dynamic_command(command_name, command_response, enabled=True)
        if success:
            self.irc_client.send_message(f"@{username} ✅ Command !{command_name} added successfully!", channel)
            print(f"[DEBUG] Moderator {username} added command: !{command_name}")
        else:
            self.irc_client.send_message(f"@{username} ❌ Failed to add command !{command_name}", channel)
    
    def _cmd_delcmd(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !delcmd command (Moderator only)"""
        print(f"[DEBUG] !delcmd command triggered by {username}")
        
        # Check if user is a moderator
        if not self._is_moderator(username, message_data):
            self.irc_client.send_message(f"@{username} ⛔ This command is for moderators only.", channel)
            return
        
        # Parse command syntax: !delcmd <command_name>
        parts = message.split(' ', 1)
        if len(parts) < 2:
            self.irc_client.send_message(f"@{username} Usage: !delcmd <command_name>", channel)
            return
        
        command_name = parts[1].lower().strip()
        
        # Remove ! prefix if provided
        if command_name.startswith('!'):
            command_name = command_name[1:]
        
        # Check if it's a built-in command
        built_in_commands = {'hello', 'help', 'status', 'ping', 'ask', 'chat', 'ai', 'addcmd', 'delcmd', 'togglecmd'}
        if command_name in built_in_commands:
            self.irc_client.send_message(f"@{username} ⛔ Cannot delete built-in command: !{command_name}", channel)
            return
        
        # Delete the command
        success = self.remove_dynamic_command(command_name)
        if success:
            # Also remove from enabled tracking
            if command_name in self.command_enabled:
                del self.command_enabled[command_name]
            self.irc_client.send_message(f"@{username} ✅ Command !{command_name} deleted successfully!", channel)
            print(f"[DEBUG] Moderator {username} deleted command: !{command_name}")
        else:
            self.irc_client.send_message(f"@{username} ❌ Command !{command_name} not found", channel)
    
    def _cmd_togglecmd(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Handle !togglecmd command (Moderator only)"""
        print(f"[DEBUG] !togglecmd command triggered by {username}")
        
        # Check if user is a moderator
        if not self._is_moderator(username, message_data):
            self.irc_client.send_message(f"@{username} ⛔ This command is for moderators only.", channel)
            return
        
        # Parse command syntax: !togglecmd <command_name> [on|off]
        parts = message.split(' ')
        if len(parts) < 2:
            self.irc_client.send_message(f"@{username} Usage: !togglecmd <command_name> [on|off]", channel)
            return
        
        command_name = parts[1].lower().strip()
        
        # Remove ! prefix if provided
        if command_name.startswith('!'):
            command_name = command_name[1:]
        
        # Determine toggle state
        if len(parts) >= 3:
            toggle_state = parts[2].lower().strip()
            if toggle_state in ['on', 'enable', 'enabled', '1', 'true']:
                enabled = True
            elif toggle_state in ['off', 'disable', 'disabled', '0', 'false']:
                enabled = False
            else:
                self.irc_client.send_message(f"@{username} Invalid state: {toggle_state}. Use 'on' or 'off'", channel)
                return
        else:
            # No state specified, toggle current state
            current_state = self.command_enabled.get(command_name, True)
            enabled = not current_state
        
        # Check if command exists
        if command_name not in self.dynamic_commands:
            self.irc_client.send_message(f"@{username} ❌ Command !{command_name} not found", channel)
            return
        
        # Toggle the command
        success = self.set_command_enabled(command_name, enabled)
        if success:
            state_text = "enabled" if enabled else "disabled"
            self.irc_client.send_message(f"@{username} ✅ Command !{command_name} {state_text}!", channel)
            print(f"[DEBUG] Moderator {username} {state_text} command: !{command_name}")
        else:
            self.irc_client.send_message(f"@{username} ❌ Failed to toggle command !{command_name}", channel)
    
    def start(self):
        """Start the bot"""
        self.logger.info("Starting Aetherra Twitch Bot...")
        
        # Initialize AI conversation manager if available
        if self.conversation_manager and hasattr(self.conversation_manager, 'initialize'):
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                initialization_result = loop.run_until_complete(self.conversation_manager.initialize())
                loop.close()
                self.logger.info(f"Conversation manager initialized: {initialization_result}")
            except Exception as e:
                self.logger.error(f"Failed to initialize conversation manager: {e}")
        
        # Validate configuration
        is_valid, errors = config.validate_config()
        if not is_valid:
            self.logger.error("Cannot start bot - configuration errors:")
            for error in errors:
                self.logger.error(f"  - {error}")
            return False
        
        # Start IRC client
        listener_thread = self.irc_client.start_async()
        if not listener_thread:
            self.logger.error("Failed to start IRC client")
            return False
        
        self.running = True
        self.logger.info("Bot started successfully!")
        
        # Send startup message
        startup_messages = [
            "🤖 Aetherra Bot is now online!",
            f"Type {config.COMMAND_PREFIX}help for available commands",
            "AI-powered responses are enabled!" if (AETHERRA_AVAILABLE and self.conversation_manager) else "Running in basic mode"
        ]
        
        # Wait a moment for connection to stabilize
        time.sleep(2)
        
        for msg in startup_messages:
            self.irc_client.send_message(msg)
            time.sleep(0.5)  # Small delay between messages
        
        return True
    
    def stop(self):
        """Stop the bot"""
        self.logger.info("Stopping Aetherra Twitch Bot...")
        
        # Send goodbye message
        if self.irc_client.connected:
            self.irc_client.send_message("🤖 Aetherra Bot going offline. See you later!")
            time.sleep(1)
        
        self.running = False
        self.irc_client.disconnect()
        self.logger.info("Bot stopped")
    
    def is_running(self) -> bool:
        """Check if bot is running"""
        return self.running and self.irc_client.connected
