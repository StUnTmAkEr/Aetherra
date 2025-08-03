# 🔐 Aetherra Twitch Bot - Security Setup

## Environment Variables Setup

This bot uses environment variables to keep your Twitch credentials secure and prevent them from being accidentally committed to version control.

### Quick Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file with your actual credentials:**
   ```bash
   # Get these from: https://dev.twitch.tv/console/apps
   TWITCH_CLIENT_ID=your-actual-client-id
   TWITCH_CLIENT_SECRET=your-actual-client-secret
   
   # Bot configuration
   TWITCH_USERNAME=your-bot-username
   TWITCH_CHANNEL=your-twitch-channel
   
   # These will be auto-generated during OAuth flow
   TWITCH_ACCESS_TOKEN=
   TWITCH_REFRESH_TOKEN=
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the bot:**
   ```bash
   python web_server.py
   ```

### Security Features

✅ **Environment Variables**: Credentials are loaded from `.env` file  
✅ **GitIgnore Protection**: `.env` files are automatically ignored by Git  
✅ **Token File Backup**: Old token files are preserved as `.backup`  
✅ **Priority System**: Environment variables take precedence over token files  

### Files That Are Ignored by Git

- `.env` (your actual credentials)
- `twitch_token.json` (legacy token storage)
- `*.log` (log files)
- `*.db` (database files)

### Files That Are Safe to Commit

- `.env.example` (template with placeholder values)
- `config.py` (loads from environment variables)
- All source code files

## Getting Twitch Credentials

1. Visit [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Create a new application
3. Set the OAuth Redirect URL to: `http://localhost:3000`
4. Copy the Client ID and Client Secret to your `.env` file

## Troubleshooting

**"No credentials found" error:**
- Make sure your `.env` file exists in the twitchbot directory
- Check that your Client ID and Client Secret are set correctly
- Verify the `.env` file doesn't have syntax errors

**OAuth flow issues:**
- Ensure the redirect URL in your Twitch app matches `http://localhost:3000`
- Check that the bot username matches your Twitch account

For more help, see the main project README or create an issue on GitHub.
