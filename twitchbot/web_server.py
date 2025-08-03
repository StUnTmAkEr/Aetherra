#!/usr/bin/env python3
"""
Aetherra Twitch Bot Web Interface Server
========================================

Flask server with Socket.IO for real-time bot control and chat monitoring.
"""

import os
import sys
import time
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template_string, send_from_directory, request
from flask_socketio import SocketIO, emit
import logging

# Add parent directory to path for bot imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aetherra_bot import AetherraBot
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'aetherra-neural-interface-key'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Global bot instance and state
bot_instance: Optional[AetherraBot] = None
bot_thread: Optional[threading.Thread] = None
bot_running = False
chat_messages = []
bot_stats = {
    'running': False,
    'channel': None,
    'messageCount': 0,
    'aiEnabled': False,
    'activeUsers': 0,
    'startTime': None,
    'lastActivity': None
}

class WebBotInterface:
    """Interface between web UI and bot instance"""
    
    def __init__(self):
        self.message_callbacks = []
        self.status_callbacks = []
        self.connected_clients = set()  # Track connected clients
        
    def register_message_callback(self, callback):
        """Register callback for new chat messages"""
        self.message_callbacks.append(callback)
        
    def register_status_callback(self, callback):
        """Register callback for status updates"""
        self.status_callbacks.append(callback)
        
    def clear_callbacks(self):
        """Clear all callbacks (useful for cleanup)"""
        self.message_callbacks.clear()
        self.status_callbacks.clear()
        
    def broadcast_message(self, username: str, message: str, msg_type: str = 'user'):
        """Broadcast chat message to all connected clients"""
        # Use socketio.emit directly instead of callbacks to avoid duplicates
        socketio.emit('chat_message', {
            'username': username,
            'message': message,
            'type': msg_type,
            'timestamp': datetime.now().isoformat()
        })
                
    def broadcast_status(self, status_data: Dict[str, Any]):
        """Broadcast status update to all connected clients"""
        # Use socketio.emit directly instead of callbacks to avoid duplicates
        socketio.emit('bot_status', status_data)

# Global interface instance
web_interface = WebBotInterface()

# Track messages sent from web interface to avoid duplicates
web_sent_messages = set()

class WebAwareBot(AetherraBot):
    """Enhanced bot with web interface integration"""
    
    def __init__(self):
        super().__init__()
        self.web_interface = web_interface
        
    def _handle_message(self, username: str, channel: str, message: str, message_data: Dict[str, Any]):
        """Override to broadcast messages to web interface"""
        # Call parent method
        super()._handle_message(username, channel, message, message_data)
        
        # Only broadcast to web interface if:
        # 1. It's not a bot message AND
        # 2. It's not a message we sent from the web interface
        if (username and 
            not self._is_bot_message(username) and 
            not self._is_web_sent_message(message)):
            
            self.web_interface.broadcast_message(username, message, 'user')
            
            # Update stats
            bot_stats['lastActivity'] = datetime.now().isoformat()
            bot_stats['activeUsers'] = len(self.user_contexts)
            self.web_interface.broadcast_status(bot_stats)
    
    def _is_bot_message(self, username: str) -> bool:
        """Check if message is from the bot itself"""
        return (username.lower() == config.BOT_USERNAME.lower() or 
                username.lower() == 'stuntbot' or 
                'stuntbot' in username.lower())
    
    def _is_web_sent_message(self, message: str) -> bool:
        """Check if this message was sent from the web interface"""
        # Check if any web-sent message matches (within timing window)
        for web_msg in list(web_sent_messages):
            if message in web_msg:
                return True
        return False
    
    def send_web_message(self, message: str, channel: str = None):
        """Send message through bot and broadcast to web interface"""
        global web_sent_messages
        
        if self.irc_client and self.irc_client.connected:
            target_channel = channel or f"#{config.CHANNEL}"
            
            # Add message to web-sent tracking to avoid showing it again from Twitch
            message_id = f"{message}_{int(time.time() * 1000)}"
            web_sent_messages.add(message_id)
            
            # Clean old messages (keep only last 10 seconds)
            current_time = int(time.time() * 1000)
            web_sent_messages = {msg for msg in web_sent_messages 
                               if current_time - int(msg.split('_')[-1]) < 10000}
            
            self.irc_client.send_message(message, target_channel)
            
            # DON'T broadcast to web interface - let the frontend handle showing "YOU" message
            # The message will appear in Twitch chat, but won't duplicate in web interface
            
            # Update stats only
            bot_stats['messageCount'] += 1
            self.web_interface.broadcast_status(bot_stats)
            
            return True
        return False

@app.route('/')
def index():
    """Serve the main web interface"""
    try:
        with open('web_interface.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: web_interface.html not found</h1>", 404

@app.route('/test')
def test_socket():
    """Serve Socket.IO test page"""
    try:
        with open('test_socket.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: test_socket.html not found</h1>", 404

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

# Socket.IO Event Handlers
@socketio.on('connect')
def handle_connect(auth=None):
    """Handle new client connection"""
    logger.info(f"Client connected")
    emit('terminal_response', {'message': '🔗 Connected to Aetherra Neural Interface'})
    
    # Send current bot status
    emit('bot_status', bot_stats)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected")

def _validate_and_refresh_tokens():
    """Validate OAuth tokens and refresh if needed"""
    try:
        if not config.ACCESS_TOKEN or not config.CLIENT_ID:
            emit('terminal_response', {'message': '⚠️ OAuth credentials not configured'})
            return False
            
        # Test current token
        import requests
        headers = {
            'Authorization': f'Bearer {config.ACCESS_TOKEN}',
            'Client-Id': config.CLIENT_ID
        }
        
        emit('terminal_response', {'message': '🔍 Validating OAuth tokens...'})
        response = requests.get('https://api.twitch.tv/helix/users', headers=headers)
        
        if response.status_code == 200:
            emit('terminal_response', {'message': '✅ OAuth tokens are valid'})
            return True
        
        # Token invalid, try to refresh
        if not config.REFRESH_TOKEN:
            emit('terminal_response', {'message': '❌ No refresh token available'})
            return False
            
        emit('terminal_response', {'message': '🔄 Refreshing OAuth tokens...'})
        
        from oauth_helper import TwitchOAuth
        oauth = TwitchOAuth(config.CLIENT_ID, config.CLIENT_SECRET)
        new_tokens = oauth.refresh_token(config.REFRESH_TOKEN)
        
        if new_tokens and 'access_token' in new_tokens:
            # Update config with new tokens
            config.ACCESS_TOKEN = new_tokens['access_token']
            if 'refresh_token' in new_tokens:
                config.REFRESH_TOKEN = new_tokens['refresh_token']
                
            # Update .env file
            _update_env_file('TWITCH_ACCESS_TOKEN', config.ACCESS_TOKEN)
            if 'refresh_token' in new_tokens:
                _update_env_file('TWITCH_REFRESH_TOKEN', config.REFRESH_TOKEN)
                
            emit('terminal_response', {'message': '✅ OAuth tokens refreshed successfully'})
            return True
        else:
            emit('terminal_response', {'message': '❌ Token refresh failed'})
            return False
            
    except Exception as e:
        emit('terminal_response', {'message': f'❌ Token validation error: {str(e)}'})
        return False

def _update_env_file(key, value):
    """Update a specific key in the .env file"""
    try:
        env_path = '.env'
        lines = []
        
        # Read existing file
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass
            
        # Update or add the key
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f'{key}='):
                lines[i] = f'{key}={value}\n'
                updated = True
                break
                
        if not updated:
            lines.append(f'{key}={value}\n')
            
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(lines)
            
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")

@socketio.on('start_bot')
def handle_start_bot():
    """Start the Twitch bot"""
    global bot_instance, bot_thread, bot_running
    
    try:
        if bot_running:
            emit('terminal_response', {'message': '⚠️ Bot is already running'})
            return
        
        logger.info("Starting Twitch bot from web interface")
        emit('terminal_response', {'message': '🚀 Initializing Aetherra Twitch Bot...'})
        
        # Validate and refresh OAuth tokens if needed
        if not _validate_and_refresh_tokens():
            emit('terminal_response', {'message': '❌ OAuth tokens invalid and refresh failed'})
            emit('terminal_response', {'message': '💡 Please use the Settings tab to reconfigure OAuth'})
            return
        
        # Create new bot instance
        bot_instance = WebAwareBot()
        
        # Start bot in separate thread
        def run_bot():
            global bot_running
            try:
                success = bot_instance.start()
                if success:
                    bot_running = True
                    bot_stats.update({
                        'running': True,
                        'channel': f"#{config.CHANNEL}",
                        'aiEnabled': bot_instance.conversation_manager is not None,
                        'startTime': datetime.now().isoformat()
                    })
                    socketio.emit('terminal_response', {'message': '✅ Bot started successfully!'})
                    socketio.emit('bot_status', bot_stats)
                    
                    # Keep bot running
                    while bot_running and bot_instance.is_running():
                        time.sleep(1)
                        
                else:
                    socketio.emit('terminal_response', {'message': '❌ Failed to start bot'})
                    
            except Exception as e:
                logger.error(f"Error running bot: {e}")
                socketio.emit('terminal_response', {'message': f'❌ Bot error: {str(e)}'})
            finally:
                bot_running = False
                bot_stats['running'] = False
                socketio.emit('bot_status', bot_stats)
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        emit('terminal_response', {'message': '⏳ Bot starting...'})
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('stop_bot')
def handle_stop_bot():
    """Stop the Twitch bot"""
    global bot_instance, bot_running
    
    try:
        if not bot_running:
            emit('terminal_response', {'message': '⚠️ Bot is not running'})
            return
        
        emit('terminal_response', {'message': '⏹️ Stopping bot...'})
        
        bot_running = False
        if bot_instance:
            bot_instance.stop()
        
        bot_stats.update({
            'running': False,
            'channel': None,
            'aiEnabled': False
        })
        
        emit('terminal_response', {'message': '✅ Bot stopped'})
        emit('bot_status', bot_stats)
        
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('restart_bot')
def handle_restart_bot():
    """Restart the Twitch bot"""
    emit('terminal_response', {'message': '🔄 Restarting bot...'})
    handle_stop_bot()
    time.sleep(2)
    handle_start_bot()

@socketio.on('get_bot_status')
def handle_get_status():
    """Get current bot status"""
    emit('bot_status', bot_stats)
    emit('terminal_response', {'message': f'📊 Status: {"ONLINE" if bot_running else "OFFLINE"}'})

@socketio.on('send_message')
def handle_send_message(data):
    """Send message through the bot to Twitch"""
    try:
        message = data.get('message', '').strip()
        if not message:
            emit('terminal_response', {'message': '❌ Empty message'})
            return
        
        if not bot_running or not bot_instance:
            emit('terminal_response', {'message': '❌ Bot is not running'})
            return
        
        success = bot_instance.send_web_message(message)
        if success:
            emit('terminal_response', {'message': f'📤 Sent: {message}'})
        else:
            emit('terminal_response', {'message': '❌ Failed to send message'})
            
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('test_ai')
def handle_test_ai(data):
    """Test AI response"""
    try:
        if not bot_running or not bot_instance:
            emit('terminal_response', {'message': '❌ Bot is not running'})
            return
        
        test_message = data.get('message', 'Hello AI, can you respond?')
        
        if bot_instance.conversation_manager:
            emit('terminal_response', {'message': f'🧠 Testing AI with: {test_message}'})
            # Generate AI response through bot
            bot_instance._generate_ai_response('WebInterface', f"#{config.CHANNEL}", test_message)
        else:
            emit('terminal_response', {'message': '❌ AI not available'})
            
    except Exception as e:
        logger.error(f"Error testing AI: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('update_setting')
def handle_update_setting(data):
    """Update bot settings"""
    try:
        key = data.get('key')
        value = data.get('value')
        
        if not bot_instance:
            emit('terminal_response', {'message': '❌ Bot not initialized'})
            return
        
        # Apply setting based on key
        if key == 'channel':
            config.CHANNEL = value.strip()
            emit('terminal_response', {'message': f'⚙️ Channel updated: {value}'})
        elif key == 'username':
            config.BOT_USERNAME = value.strip()
            emit('terminal_response', {'message': f'⚙️ Bot username updated: {value}'})
        elif key == 'command_prefix':
            config.COMMAND_PREFIX = value.strip()
            emit('terminal_response', {'message': f'⚙️ Command prefix updated: {value}'})
        elif key == 'response_chance':
            config.AI_RESPONSE_CHANCE = float(value)
            emit('terminal_response', {'message': f'⚙️ Response chance: {value}'})
        elif key == 'temperature' and bot_instance.conversation_manager:
            bot_instance.conversation_manager.temperature = float(value)
            emit('terminal_response', {'message': f'⚙️ Temperature: {value}'})
        elif key == 'max_tokens' and bot_instance.conversation_manager:
            bot_instance.conversation_manager.max_tokens = int(value)
            emit('terminal_response', {'message': f'⚙️ Max tokens: {value}'})
        elif key == 'ai_responses':
            config.ENABLE_AI_RESPONSES = bool(value)
            emit('terminal_response', {'message': f'⚙️ AI responses: {"ON" if value else "OFF"}'})
        else:
            emit('terminal_response', {'message': f'⚙️ Updated {key}: {value}'})
            
    except Exception as e:
        logger.error(f"Error updating setting: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('toggle_memory')
def handle_toggle_memory():
    """Toggle AI memory system"""
    try:
        if not bot_instance or not bot_instance.conversation_manager:
            emit('terminal_response', {'message': '❌ AI not available'})
            return
        
        # Toggle memory (if supported)
        if hasattr(bot_instance.conversation_manager, 'memory_enabled'):
            current = bot_instance.conversation_manager.memory_enabled
            bot_instance.conversation_manager.memory_enabled = not current
            status = "ON" if not current else "OFF"
            emit('terminal_response', {'message': f'🧠 Memory: {status}'})
        else:
            emit('terminal_response', {'message': '⚠️ Memory toggle not supported'})
            
    except Exception as e:
        logger.error(f"Error toggling memory: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('clear_memory')
def handle_clear_memory():
    """Clear AI memory"""
    try:
        if not bot_instance:
            emit('terminal_response', {'message': '❌ Bot not available'})
            return
        
        # Clear user contexts
        bot_instance.user_contexts.clear()
        emit('terminal_response', {'message': '🗑️ Memory cleared'})
        
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('save_command')
def handle_save_command(data):
    """Handle command save/update requests from web interface"""
    try:
        command = data.get('name', '').strip().lower()  # Changed from 'command' to 'name'
        response = data.get('response', '').strip()
        enabled = data.get('enabled', True)
        
        if not command or not response:
            emit('error_message', {'message': 'Command name and response are required'})
            return
        
        # Remove ! prefix if present
        if command.startswith('!'):
            command = command[1:]
        
        if bot_instance:
            success = bot_instance.add_dynamic_command(command, response, enabled)
            if success:
                status = "enabled" if enabled else "disabled"
                emit('terminal_response', {'message': f'✅ Command !{command} saved successfully ({status})'})
                emit('command_saved', {'command': command, 'response': response, 'enabled': enabled})
                # Send updated commands list with enabled states
                commands = bot_instance.get_dynamic_commands()
                enabled_states = {cmd: bot_instance.command_enabled.get(cmd, True) for cmd in commands.keys()}
                emit('commands_updated', {'commands': commands, 'enabled': enabled_states}, broadcast=True)
            else:
                emit('error_message', {'message': f'Failed to save command !{command}'})
        else:
            emit('error_message', {'message': 'Bot not running'})
            
    except Exception as e:
        logger.error(f"Error saving command: {e}")
        emit('error_message', {'message': f'Error saving command: {str(e)}'})

@socketio.on('delete_command')
def handle_delete_command(data):
    """Handle command deletion requests from web interface"""
    try:
        command = data.get('name', '').strip().lower()  # Changed from 'command' to 'name'
        
        if not command:
            emit('error_message', {'message': 'Command name is required'})
            return
        
        if bot_instance:
            success = bot_instance.remove_dynamic_command(command)
            if success:
                emit('terminal_response', {'message': f'🗑️ Command !{command} deleted successfully'})
                emit('command_deleted', {'command': command})
                # Send updated commands list
                commands = bot_instance.get_dynamic_commands()
                enabled = {cmd: bot_instance.command_enabled.get(cmd, True) for cmd in commands.keys()}
                emit('commands_updated', {'commands': commands, 'enabled': enabled})
            else:
                emit('error_message', {'message': f'Failed to delete command !{command} (not found)'})
        else:
            emit('error_message', {'message': 'Bot not running'})
            
    except Exception as e:
        logger.error(f"Error deleting command: {e}")
        emit('error_message', {'message': f'Error deleting command: {str(e)}'})

@socketio.on('get_commands')
def handle_get_commands():
    """Handle request for current commands list"""
    try:
        if bot_instance:
            commands = bot_instance.get_dynamic_commands()
            enabled = {cmd: bot_instance.command_enabled.get(cmd, True) for cmd in commands.keys()}
            emit('commands_list', {'commands': commands, 'enabled': enabled})
        else:
            emit('error_message', {'message': 'Bot not running'})
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        emit('error_message', {'message': f'Error getting commands: {str(e)}'})

@socketio.on('toggle_command')
def handle_toggle_command(data):
    """Handle command enable/disable toggle"""
    try:
        if not bot_instance:
            emit('error_message', {'message': 'Bot not running'})
            return
            
        command_name = data.get('name', '').strip()
        enabled = data.get('enabled', True)
        
        if not command_name:
            emit('error_message', {'message': 'Command name is required'})
            return
        
        # Remove ! prefix if present
        if command_name.startswith('!'):
            command_name = command_name[1:]
        
        success = bot_instance.set_command_enabled(command_name, enabled)
        
        if success:
            emit('terminal_response', {'message': f'✅ Command !{command_name} {"enabled" if enabled else "disabled"}'})
            emit('command_toggled', {'command': command_name, 'enabled': enabled})
            # Send updated commands list
            commands = bot_instance.get_dynamic_commands()
            enabled_states = {cmd: bot_instance.command_enabled.get(cmd, True) for cmd in commands.keys()}
            emit('commands_updated', {'commands': commands, 'enabled': enabled_states}, broadcast=True)
        else:
            emit('error_message', {'message': f'Command !{command_name} not found'})
            
    except Exception as e:
        logger.error(f"Error toggling command: {e}")
        emit('error_message', {'message': f'Error toggling command: {str(e)}'})

@socketio.on('get_current_settings')
def handle_get_current_settings():
    """Get current bot settings"""
    try:
        # Helper function to mask credentials for display
        def mask_credential(value, show_length=4):
            if not value:
                return ""
            if len(value) <= show_length:
                return "*" * len(value)
            return value[:show_length] + "*" * (len(value) - show_length)
        
        settings = {
            'channel': config.CHANNEL or "",
            'username': config.BOT_USERNAME or "",
            'command_prefix': config.COMMAND_PREFIX or "!",
            'ai_responses': config.ENABLE_AI_RESPONSES,
            'response_chance': config.AI_RESPONSE_CHANCE,
            # Send masked credential values for display
            'client_id': mask_credential(config.CLIENT_ID),
            'client_secret': mask_credential(config.CLIENT_SECRET),
            'access_token': mask_credential(config.ACCESS_TOKEN),
            'refresh_token': mask_credential(config.REFRESH_TOKEN),
            # Also send boolean flags for status indicators
            'has_access_token': bool(config.ACCESS_TOKEN),
            'has_refresh_token': bool(config.REFRESH_TOKEN),
            'has_client_id': bool(config.CLIENT_ID),
            'has_client_secret': bool(config.CLIENT_SECRET)
        }
        
        # Add AI-specific settings if bot is initialized
        if bot_instance and bot_instance.conversation_manager:
            settings['temperature'] = getattr(bot_instance.conversation_manager, 'temperature', 0.7)
            settings['max_tokens'] = getattr(bot_instance.conversation_manager, 'max_tokens', 150)
        else:
            settings['temperature'] = 0.7
            settings['max_tokens'] = 150
            
        emit('current_settings', settings)
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('update_credential')
def handle_update_credential(data):
    """Update sensitive credentials (Client ID, Secret, OpenAI key)"""
    try:
        key = data.get('key')
        value = data.get('value', '').strip()
        
        if not value:
            emit('terminal_response', {'message': '❌ Credential cannot be empty'})
            return
            
        # Update environment variable and config
        if key == 'client_id':
            os.environ['TWITCH_CLIENT_ID'] = value
            config.CLIENT_ID = value
            emit('terminal_response', {'message': '🔑 Client ID updated successfully'})
        elif key == 'client_secret':
            os.environ['TWITCH_CLIENT_SECRET'] = value
            config.CLIENT_SECRET = value
            emit('terminal_response', {'message': '🔑 Client Secret updated successfully'})
        elif key == 'openai_key':
            os.environ['OPENAI_API_KEY'] = value
            emit('terminal_response', {'message': '🧠 OpenAI API Key updated successfully'})
        else:
            emit('terminal_response', {'message': f'❌ Unknown credential: {key}'})
            
        # Save to .env file
        save_to_env_file(key, value)
        
    except Exception as e:
        logger.error(f"Error updating credential: {e}")
        emit('terminal_response', {'message': f'❌ Error: {str(e)}'})

@socketio.on('start_oauth_flow')
def handle_start_oauth_flow():
    """Start OAuth flow for Twitch authentication"""
    try:
        if not config.CLIENT_ID:
            emit('terminal_response', {'message': '❌ Client ID not configured'})
            return
            
        # Import oauth helper
        from oauth_helper import start_oauth_server
        
        # Start OAuth flow
        oauth_url = start_oauth_server()
        emit('oauth_url', {'url': oauth_url})
        emit('terminal_response', {'message': '🔗 OAuth flow started. Check browser.'})
        
    except Exception as e:
        logger.error(f"Error starting OAuth: {e}")
        emit('terminal_response', {'message': f'❌ OAuth Error: {str(e)}'})

@socketio.on('test_oauth_tokens')
def handle_test_oauth_tokens():
    """Test OAuth tokens validity"""
    try:
        if not config.ACCESS_TOKEN:
            emit('token_test_result', {'valid': False})
            emit('terminal_response', {'message': '❌ No access token configured'})
            return
            
        # Test token with Twitch API
        import requests
        headers = {
            'Authorization': f'Bearer {config.ACCESS_TOKEN}',
            'Client-Id': config.CLIENT_ID
        }
        
        response = requests.get('https://api.twitch.tv/helix/users', headers=headers)
        valid = response.status_code == 200
        
        emit('token_test_result', {'valid': valid})
        
        if valid:
            emit('terminal_response', {'message': '✅ OAuth tokens are valid'})
        else:
            emit('terminal_response', {'message': '❌ OAuth tokens are invalid or expired'})
            
    except Exception as e:
        logger.error(f"Error testing tokens: {e}")
        emit('token_test_result', {'valid': False})
        emit('terminal_response', {'message': f'❌ Token test error: {str(e)}'})

@socketio.on('save_all_settings')
def handle_save_all_settings():
    """Save all current settings to file"""
    try:
        # Save current config to files
        save_config_to_file()
        emit('terminal_response', {'message': '💾 All settings saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        emit('terminal_response', {'message': f'❌ Save error: {str(e)}'})

@socketio.on('reset_settings')
def handle_reset_settings():
    """Reset settings to defaults"""
    try:
        # Reset to default values
        config.AI_RESPONSE_CHANCE = 0.3
        config.ENABLE_AI_RESPONSES = True
        config.COMMAND_PREFIX = "!"
        
        if bot_instance and bot_instance.conversation_manager:
            bot_instance.conversation_manager.temperature = 0.7
            bot_instance.conversation_manager.max_tokens = 150
            
        emit('terminal_response', {'message': '🔄 Settings reset to defaults'})
        
        # Send updated settings
        handle_get_current_settings()
        
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        emit('terminal_response', {'message': f'❌ Reset error: {str(e)}'})

@socketio.on('export_settings')
def handle_export_settings():
    """Export current settings to JSON"""
    try:
        settings = {
            'bot_settings': {
                'channel': config.CHANNEL,
                'username': config.BOT_USERNAME,
                'command_prefix': config.COMMAND_PREFIX,
                'ai_responses': config.ENABLE_AI_RESPONSES,
                'response_chance': config.AI_RESPONSE_CHANCE
            },
            'ai_settings': {
                'temperature': getattr(bot_instance.conversation_manager, 'temperature', 0.7) if bot_instance and bot_instance.conversation_manager else 0.7,
                'max_tokens': getattr(bot_instance.conversation_manager, 'max_tokens', 150) if bot_instance and bot_instance.conversation_manager else 150
            }
        }
        
        emit('settings_exported', {'settings': settings})
        
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        emit('terminal_response', {'message': f'❌ Export error: {str(e)}'})

@socketio.on('import_settings')
def handle_import_settings(data):
    """Import settings from JSON"""
    try:
        settings = data.get('settings', {})
        
        # Apply bot settings
        if 'bot_settings' in settings:
            bot_settings = settings['bot_settings']
            if 'command_prefix' in bot_settings:
                config.COMMAND_PREFIX = bot_settings['command_prefix']
            if 'ai_responses' in bot_settings:
                config.ENABLE_AI_RESPONSES = bot_settings['ai_responses']
            if 'response_chance' in bot_settings:
                config.AI_RESPONSE_CHANCE = bot_settings['response_chance']
                
        # Apply AI settings
        if 'ai_settings' in settings and bot_instance and bot_instance.conversation_manager:
            ai_settings = settings['ai_settings']
            if 'temperature' in ai_settings:
                bot_instance.conversation_manager.temperature = ai_settings['temperature']
            if 'max_tokens' in ai_settings:
                bot_instance.conversation_manager.max_tokens = ai_settings['max_tokens']
                
        emit('terminal_response', {'message': '📥 Settings imported successfully'})
        
        # Send updated settings
        handle_get_current_settings()
        
    except Exception as e:
        logger.error(f"Error importing settings: {e}")
        emit('terminal_response', {'message': f'❌ Import error: {str(e)}'})

def save_to_env_file(key, value):
    """Save a key-value pair to the .env file"""
    try:
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        
        # Read existing .env file
        lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Map key to environment variable name
        env_key_map = {
            'client_id': 'TWITCH_CLIENT_ID',
            'client_secret': 'TWITCH_CLIENT_SECRET',
            'openai_key': 'OPENAI_API_KEY'
        }
        
        env_key = env_key_map.get(key, key.upper())
        
        # Update or add the key
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f'{env_key}='):
                lines[i] = f'{env_key}={value}\n'
                updated = True
                break
                
        if not updated:
            lines.append(f'{env_key}={value}\n')
            
        # Write back to file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
    except Exception as e:
        logger.error(f"Error saving to .env file: {e}")

def save_config_to_file():
    """Save current configuration to config file"""
    try:
        config_data = {
            'CHANNEL': config.CHANNEL,
            'BOT_USERNAME': config.BOT_USERNAME,
            'COMMAND_PREFIX': config.COMMAND_PREFIX,
            'ENABLE_AI_RESPONSES': config.ENABLE_AI_RESPONSES,
            'AI_RESPONSE_CHANCE': config.AI_RESPONSE_CHANCE
        }
        
        config_file = os.path.join(os.path.dirname(__file__), 'bot_config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error saving config file: {e}")

def main():
    """Main entry point"""
    logger.info("🤖 Starting Aetherra Twitch Bot Web Interface")
    logger.info(f"💻 Web interface will be available at: http://localhost:5000")
    
    try:
        # Run Flask-SocketIO server
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,  # Set to True for development
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down web interface")
        if bot_running and bot_instance:
            bot_instance.stop()
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == '__main__':
    main()
