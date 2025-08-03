# 🤖 Aetherra Twitch Bot

A sophisticated Twitch chat bot powered by the Aetherra AI system with a modern web interface for real-time management. This bot provides IRC connectivity, AI-powered conversations, dynamic command management, and a complete web control panel with real-time settings persistence.

## ✨ Features

### 🌐 Web Interface
- **Real-time Web Control Panel**: Modern cyberpunk-themed interface at http://localhost:5000
- **Live Chat Monitoring**: See all Twitch messages in real-time through the web interface
- **Advanced Settings Management**: Complete configuration interface with instant persistence
- **Command Management**: Add, edit, delete, and toggle commands through the web UI
- **Bot Status Dashboard**: Monitor connection status, AI engine, and activity metrics
- **Tabbed Interface**: Separate Chat, Commands, and Settings tabs for organized management
- **Real-time Updates**: All changes sync instantly between web interface and bot

### 🔌 Core Bot Features
- **IRC Connection**: Robust SSL connection to Twitch IRC with auto-reconnection
- **Real-time Chat**: Bidirectional chat communication with rate limiting
- **Dynamic Commands**: Hot-reload command system with enable/disable toggles
- **Persistent Storage**: Commands and settings saved to JSON with real-time sync
- **Configuration Validation**: Pre-startup checks ensure proper setup

### 🧠 AI Integration
- **Aetherra AI**: Deep integration with Lyrixa conversation system
- **Smart Responses**: Context-aware AI responses with conversation memory
- **Fallback System**: Graceful degradation when AI services unavailable
- **User Context**: Per-user conversation tracking and memory
- **Configurable AI**: Adjustable response probability and settings

### ⚡ Built-in Commands
- `!hello` - Friendly greeting message
- `!help` - Display available commands (dynamically generated)
- `!status` - Show detailed bot status and statistics
- `!ping` - Test bot responsiveness
- `!ai` - Information about AI features and status
- `!ask <question>` - Direct AI question and response
- `!chat <message>` - Conversational AI interaction

### 👑 Moderator Commands
- `!addcmd <name> <response>` - Add new commands (moderators only)
- `!delcmd <name>` - Delete existing commands (moderators only)
- `!togglecmd <name>` - Enable/disable commands (moderators only)

### 🛡️ Security Features
- **Environment Variables**: Secure credential storage in `.env` files
- **Git Protection**: Automatic `.gitignore` for sensitive files
- **Token Management**: OAuth token refresh and validation
- **Moderator Permissions**: Role-based command access control

## 🚀 Quick Start

## 🆕 Recent Updates

### ✅ Version 2.0 - Enhanced Web Interface & Settings Management
- **🐛 Critical Bug Fixes**: Resolved undefined function references in settings functionality
- **⚙️ Complete Settings Tab**: Full configuration management with real-time persistence
- **🔐 Enhanced Security**: Improved credential management with OAuth integration
- **🧹 Repository Cleanup**: Streamlined codebase, removed unused files for publication
- **🎨 UI Improvements**: Fixed border-radius inconsistencies and visual polish
- **🔄 Real-time Sync**: All settings changes instantly saved to memory and config files
- **📡 Socket.IO Enhancement**: Improved client-server communication for settings updates

### Prerequisites

1. **Twitch Account**: Bot account (can be your main account)
2. **Twitch Application**: Create at [Twitch Developer Console](https://dev.twitch.tv/console/apps)
3. **Python 3.8+**: Required for the bot and web interface
4. **Aetherra Project**: Optional for enhanced AI features

### 🔧 Security Setup (Required)

**Important**: This bot uses environment variables to keep your credentials secure!

1. **Copy the environment template**:
   ```bash
   cd twitchbot
   cp .env.example .env
   ```

2. **Get your Twitch credentials**:
   - Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
   - Create a new application or use existing
   - Set OAuth Redirect URL to: `http://localhost:3000`
   - Copy your Client ID and Client Secret

3. **Edit your `.env` file**:
   ```bash
   # Required - Get from Twitch Developer Console
   TWITCH_CLIENT_ID=your-actual-client-id
   TWITCH_CLIENT_SECRET=your-actual-client-secret
   
   # Required - Your bot and channel info
   TWITCH_USERNAME=your-bot-username
   TWITCH_CHANNEL=your-twitch-channel
   
   # Optional - For enhanced AI features
   OPENAI_API_KEY=your-openai-key
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 🎮 Running the Bot

#### Option 1: Web Interface (Recommended)
```bash
python web_server.py
```
Then open http://localhost:5000 in your browser for the full control panel!

#### Option 2: Direct Start
```bash
python start_bot.py
```
Starts the bot directly with configuration validation.

#### Option 3: Interactive Setup
```bash
python main.py
```
Guided setup with OAuth flow for first-time users.

### 🌐 Web Interface Features

The web control panel provides:
- **📱 Real-time Chat**: See live Twitch messages
- **⚙️ Bot Controls**: Start/stop bot with buttons
- **⚡ Command Manager**: Add/edit/delete commands instantly
- **🔄 Toggle Switches**: Enable/disable commands with visual feedback
- **📊 Status Dashboard**: Monitor connection and AI status
- **🎛️ Settings Tab**: Complete configuration management with real-time persistence
- **🔐 Secure Credential Management**: OAuth token management and API key settings
- **🤖 AI Configuration**: Response rates, model settings, and behavioral controls

Access at: **http://localhost:5000**

## 🔧 Configuration

### 🔐 Environment Variables (Recommended)

All sensitive credentials are stored in a `.env` file that's automatically ignored by Git:

```env
# Twitch Application Credentials
TWITCH_CLIENT_ID=your-client-id-here
TWITCH_CLIENT_SECRET=your-client-secret-here

# Bot Configuration
TWITCH_USERNAME=your-bot-username
TWITCH_CHANNEL=your-twitch-channel

# OAuth Tokens (auto-generated)
TWITCH_ACCESS_TOKEN=automatically-generated
TWITCH_REFRESH_TOKEN=automatically-generated

# Optional AI Enhancement
OPENAI_API_KEY=your-openai-key-here
```

### 📁 File Structure

**🏗️ Cleaned Repository Structure (19 Essential Files):**
- **`.env`** - Your actual credentials (Git ignored)
- **`.env.example`** - Template file (safe to commit)
- **`commands.json`** - Dynamic command storage with real-time sync
- **`config.py`** - Configuration management with enhanced validation
- **`web_interface.html`** - Modern web control panel with full settings management
- **`web_server.py`** - Enhanced Flask-SocketIO server with real-time persistence
- **`aetherra_bot.py`** - Main bot engine with improved error handling
- **Core files**: `start_bot.py`, `main.py`, `twitch_client.py`, and supporting modules
- **Documentation**: `README.md`, `SECURITY_SETUP.md`

**🗑️ Removed Development Files:**
- `demo.py`, `launch_web.py`, `test_openai.py` - Development testing files
- `test_socket.html` - HTML testing artifacts  
- `*.log` files - Log file cleanup
- `__pycache__/` directories - Python cache cleanup

### ⚙️ Advanced Configuration

The `config.py` file contains additional settings:

```python
# Rate limiting
RATE_LIMIT_MESSAGES = 20  # Messages per 30 seconds
RATE_LIMIT_WINDOW = 30    # Time window

# AI behavior
AI_RESPONSE_CHANCE = 0.1  # 10% chance for auto-responses
AI_ENABLED = True         # Enable AI features

# Logging
LOG_LEVEL = "INFO"        # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True        # Save logs to file
```

## 🎮 Usage Options

### 🌐 Web Interface
```bash
python web_server.py
```
- Full-featured web control panel
- Real-time chat monitoring
- Visual command management
- Status dashboard and AI controls
- Available at: http://localhost:5000

### ⚡ Direct Start
```bash
python start_bot.py
```
- Quick bot startup with validation
- Configuration check before connecting
- Lightweight console operation
- Ideal for production deployment

### 🛠️ Interactive Setup
```bash
python main.py
```
- Guided OAuth setup process
- Configuration wizard
- Menu-driven interface
- Perfect for first-time setup

### 📋 Command Line Options
```bash
python main.py --headless   # Run without interactive menu
python main.py --test       # Test configuration only
python main.py --help       # Show all options
```

## 💻 Web Interface Guide

### 📱 Chat Tab
- **Live Chat Window**: See all Twitch messages in real-time
- **Message Input**: Send messages directly to Twitch
- **Bot Controls**: Start/stop/restart buttons
- **Status Indicators**: Connection and AI status
- **Terminal Output**: Real-time system messages and feedback

### ⚡ Commands Tab
- **Command List**: All available commands with responses
- **Toggle Switches**: Enable/disable commands visually
- **Add Command**: Create new commands instantly
- **Edit Commands**: Modify existing command responses
- **Delete Commands**: Remove unwanted commands
- **Refresh**: Sync with server state

### ⚙️ Settings Tab
- **Twitch Connection**: Configure channel name and bot username
- **API Credentials**: Manage Twitch Client ID, Client Secret, and OAuth tokens
- **AI Configuration**: Response chance, cooldown settings, and model parameters
- **Real-time Persistence**: All settings save instantly to memory and configuration files
- **OAuth Helper**: Built-in OAuth flow for secure token generation
- **Credential Security**: Password-masked inputs with show/hide toggles

### 🔄 Real-time Features
- **Live Updates**: Changes sync instantly between web and bot
- **WebSocket Communication**: Real-time bidirectional updates
- **Status Monitoring**: Live connection and activity tracking
- **Error Handling**: Graceful error display and recovery
- **Settings Persistence**: All configuration changes save immediately to memory
- **Terminal Feedback**: Real-time system messages and operation status

## 🏗️ Architecture

### 🔧 Core Components

- **`web_server.py`**: Flask-SocketIO web server with real-time communication
- **`web_interface.html`**: Modern cyberpunk-themed control panel
- **`aetherra_bot.py`**: Main bot engine with AI integration and command handling
- **`twitch_client.py`**: Low-level IRC client with message parsing
- **`config.py`**: Configuration management with environment variable support
- **`start_bot.py`**: Direct startup script with validation
- **`main.py`**: Interactive launcher with OAuth setup

### 🔗 Integration Flow

```
Web Interface ↔ Flask-SocketIO ↔ AetherraBot ↔ TwitchIRC ↔ Twitch.tv
                     ↓                ↓
                Commands.json    Aetherra AI
```

### 🧠 AI Integration

- **Lyrixa Enhanced Conversation Manager**: Advanced context-aware responses
- **Memory System**: Per-user conversation tracking and context
- **Fallback Responses**: Graceful degradation when AI unavailable
- **OpenAI Integration**: Optional enhanced AI capabilities
- **Smart Response Logic**: Keyword detection and probability-based responses

## 🔧 Advanced Usage

### 🎯 Custom Commands

#### Via Web Interface (Recommended)
1. Open http://localhost:5000
2. Go to Commands tab
3. Click "ADD COMMAND"
4. Enter command name and response
5. Save - instantly available in chat!

#### Via Code
Add custom commands in `aetherra_bot.py`:

```python
# In _setup_handlers method
self.irc_client.add_command_handler("mycmd", self._cmd_mycmd)

# Add the handler method
def _cmd_mycmd(self, username: str, message_data: dict):
    response = f"@{username} Custom command response!"
    self.irc_client.send_message(response)
```

### 🤖 AI Response Customization

Modify `_should_respond_with_ai` in `aetherra_bot.py`:

```python
def _should_respond_with_ai(self, username: str, channel: str, message: str) -> bool:
    # Custom keywords that trigger AI responses
    ai_keywords = ["bot", "ai", "help", "question"]
    has_keyword = any(keyword in message.lower() for keyword in ai_keywords)
    
    # Respond if keywords found or random chance
    return has_keyword or random.random() < self.config.AI_RESPONSE_CHANCE
```

### 👑 Moderator System

The bot automatically detects Twitch moderators and channel owners:

```python
def _is_moderator(self, message_data: dict) -> bool:
    badges = message_data.get('badges', {})
    return 'moderator' in badges or 'broadcaster' in badges
```

Moderators can use special commands:
- `!addcmd <name> <response>` - Add commands
- `!delcmd <name>` - Delete commands  
- `!togglecmd <name>` - Enable/disable commands

### 🔄 Dynamic Command System

Commands are stored in `commands.json` with this structure:

```json
{
  "commands": {
    "hello": "Hello there! Welcome to the stream!",
    "status": "Bot is running and ready to chat!"
  },
  "enabled": {
    "hello": true,
    "status": false
  }
}
```

Commands can be managed via:
- Web interface (real-time)
- Moderator chat commands
- Direct JSON file editing

## 🛠️ Troubleshooting

### 🚨 Common Issues

#### "Bot configuration is incomplete!"
- **Check your `.env` file** - ensure all required fields are filled
- **Verify credentials** - test Client ID/Secret at Twitch Developer Console
- **Run configuration test**: `python start_bot.py` (will show missing fields)

#### "Connection failed to Twitch IRC"
- **Check internet connection** and Twitch server status
- **Verify OAuth tokens** - they may have expired
- **Check channel name** - ensure it exists and is spelled correctly
- **Firewall issues** - ensure port 6697 (SSL) is accessible

#### "Web interface won't load"
- **Check port 5000** - ensure it's not blocked by firewall
- **Try different browser** - clear cache and cookies
- **Check console logs** - run `python web_server.py` and watch for errors
- **Verify dependencies** - ensure `flask-socketio` is installed

#### "Settings not saving"
- **Check browser console** - look for JavaScript errors (F12 → Console)
- **Verify WebSocket connection** - should show "Connected" status in web interface
- **Test with different browser** - clear cache and try again
- **Check file permissions** - ensure `.env` and `config.py` are writable
- **Monitor terminal output** - watch for error messages when updating settings

#### "Commands not working"
- **Check command format** - must start with `!` (e.g., `!hello`)
- **Verify bot is in channel** - check web interface status
- **Check rate limiting** - bot may be temporarily throttled
- **Test with moderator account** - some commands require mod permissions
- **Refresh commands list** - use refresh button in Commands tab

#### "AI responses not working"
- **Check OpenAI API key** - verify it's set in `.env` file
- **Monitor API usage** - ensure you haven't exceeded quotas
- **Check AI settings** - adjust response probability in web interface
- **Verify Aetherra installation** - AI features require Aetherra components

### 📋 Configuration Validation

Run diagnostics to check your setup:

```bash
# Test bot configuration
python start_bot.py

# Test web server
python web_server.py

# Full interactive diagnostics
python main.py --test
```

### 📊 Logging and Debugging

#### Enable Debug Logging
Edit your `.env` file:
```env
LOG_LEVEL=DEBUG
LOG_TO_FILE=true
```

#### Check Log Files
```bash
# Windows
Get-Content -Wait twitchbot.log

# Linux/Mac
tail -f twitchbot.log
```

#### Web Interface Console
- Open browser Developer Tools (F12)
- Check Console tab for JavaScript errors
- Monitor Network tab for WebSocket connection issues

### 🔄 Recovery Procedures

#### Reset Configuration
```bash
# Backup current settings
cp .env .env.backup

# Start fresh setup
python main.py
# Choose option 1 for OAuth setup
```

#### Clear Command Cache
```bash
# Backup commands
cp commands.json commands.backup.json

# Reset to defaults
echo '{"commands": {}, "enabled": {}}' > commands.json
```

#### Restart Services
```bash
# Stop all Python processes
pkill -f python  # Linux/Mac
# Or manually close terminal windows

# Restart web server
python web_server.py
```

### 📞 Getting Help

1. **Check logs first** - most issues show clear error messages
2. **Verify configuration** - use built-in validation tools
3. **Test components separately** - isolate web vs bot vs AI issues
4. **Check dependencies** - ensure all packages are installed
5. **Review recent changes** - what was modified before the issue?

## 🔒 Security Considerations

### 🛡️ Credential Protection
- **Environment Variables**: All sensitive data stored in `.env` files
- **Git Ignore**: Automatic protection from accidental commits
- **No Hardcoded Secrets**: No credentials in source code
- **Token Rotation**: OAuth tokens automatically refresh

### 🔐 Best Practices
- **Regular Updates**: Keep dependencies and tokens current
- **Monitor Activity**: Review logs for unexpected behavior
- **Limited Permissions**: Bot only needs chat access, not channel management
- **Secure Deployment**: Use environment variables in production

### 📁 File Security
```
✅ SAFE TO COMMIT:
- .env.example (template with placeholders)
- *.py (source code files)
- README.md (documentation)
- requirements.txt (dependencies)

🚫 NEVER COMMIT:
- .env (your actual credentials)
- twitch_token.json (legacy token file)
- *.log (log files with potential tokens)
- *.db (database files)
```

### 🔄 Security Setup Checklist
- [ ] Copy `.env.example` to `.env`
- [ ] Fill in actual credentials in `.env`
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test configuration validation
- [ ] Monitor for credential leaks in commits

## 🚀 Production Ready

### ✅ Publication Checklist
- **🧹 Repository Cleaned**: 19 essential files, removed development artifacts
- **🐛 Bugs Fixed**: All critical web interface functionality issues resolved
- **⚙️ Settings Complete**: Full configuration management with real-time persistence
- **🔐 Security Verified**: All credentials properly protected with environment variables
- **📚 Documentation Updated**: Comprehensive setup and troubleshooting guides
- **🎨 UI Polished**: Consistent styling and improved user experience
- **🔄 Real-time Sync**: All features tested and working with instant updates

### 🌟 Key Features Ready for Use
- **Complete Web Interface**: Chat monitoring, command management, and full settings control
- **Real-time Configuration**: All settings save instantly to memory and persist across restarts
- **Enhanced Security**: OAuth integration, credential masking, and environment variable protection
- **AI Integration**: Context-aware responses with configurable behavior and fallback systems
- **Robust Error Handling**: Graceful degradation and comprehensive error reporting
- **Professional Codebase**: Clean, well-documented, and maintainable code structure

This bot is now **production-ready** and suitable for public release! 🎉

## 🤝 Contributing

### 💡 Development Setup
1. **Fork the repository** and create a feature branch
2. **Set up environment** with `.env.example` template
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Test thoroughly** with different scenarios and configurations
5. **Follow code style** and add appropriate logging

### 📝 Code Guidelines
- **Error Handling**: Include try/catch blocks for external services
- **Logging**: Add INFO/DEBUG logs for new features
- **Documentation**: Update README for new functionality
- **Security**: Never commit credentials or sensitive data
- **Testing**: Verify changes work with and without Aetherra AI

### 🧪 Testing Checklist
- [ ] Bot connects to Twitch successfully
- [ ] Web interface loads and functions
- [ ] Commands work in chat and web interface
- [ ] AI responses function (if configured)
- [ ] Configuration validation works
- [ ] Error handling graceful

### 🔄 Pull Request Process
1. **Test your changes** thoroughly
2. **Update documentation** if needed
3. **Add security considerations** for new features
4. **Include example configurations** if applicable
5. **Verify no credentials leaked** in commits

## 📄 License

This bot is part of the Aetherra project and follows the same licensing terms.

## 📞 Support

### 🆘 Getting Help
1. **Check the troubleshooting section** above
2. **Review log files** for specific error messages
3. **Test configuration** with validation tools
4. **Verify all dependencies** are properly installed
5. **Check Twitch API status** if connection issues persist

### 📚 Documentation
- **SECURITY_SETUP.md**: Detailed security configuration guide
- **Web Interface**: Built-in help and status indicators
- **Code Comments**: Inline documentation in source files
- **Example Files**: Templates for configuration and setup

---

**🎉 Happy streaming with your AI-powered Twitch bot! 🤖✨**
