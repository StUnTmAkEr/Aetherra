# oauth_helper.py
"""
Twitch OAuth Helper
===================

Helper functions for handling Twitch OAuth authentication.
Supports both App Access Tokens and User Access Tokens.
"""

import requests
import webbrowser
import http.server
import socketserver
import urllib.parse
from typing import Optional, Dict, Any
import threading
import time
import json
import logging


class TwitchOAuth:
    """Handle Twitch OAuth authentication flows"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_port: int = 3000):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_port = redirect_port
        self.logger = logging.getLogger("TwitchOAuth")
        
        # OAuth endpoints
        self.auth_url = "https://id.twitch.tv/oauth2/authorize"
        self.token_url = "https://id.twitch.tv/oauth2/token"
        self.validate_url = "https://id.twitch.tv/oauth2/validate"
        
        # For user OAuth flow - construct redirect URI based on port
        if redirect_port == 80:
            self.redirect_uri = "http://localhost"
        else:
            self.redirect_uri = f"http://localhost:{redirect_port}"
        
        self.auth_code = None
        self.server = None
    
    def get_app_access_token(self) -> Optional[Dict[str, Any]]:
        """
        Get an App Access Token for server-to-server requests.
        This is good for basic API calls but not for chat.
        """
        try:
            self.logger.info("Requesting App Access Token...")
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.logger.info("App Access Token obtained successfully")
            return token_data
            
        except Exception as e:
            self.logger.error(f"Failed to get App Access Token: {e}")
            return None
    
    def get_user_access_token_url(self, scopes: list = None) -> str:
        """
        Generate the URL for user OAuth flow.
        Default scopes for chat functionality.
        """
        if scopes is None:
            scopes = [
                'chat:read',     # Read chat messages
                'chat:edit',     # Send chat messages
                'user:read:email'  # Basic user info
            ]
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scopes),
            'state': 'aetherra_bot_auth'  # CSRF protection
        }
        
        url = f"{self.auth_url}?" + urllib.parse.urlencode(params)
        return url
    
    def start_oauth_flow(self, scopes: list = None) -> Optional[Dict[str, Any]]:
        """
        Start the complete OAuth flow with local callback server.
        Returns token data if successful.
        """
        try:
            self.logger.info("Starting OAuth flow...")
            
            # Start local server to catch callback
            self._start_callback_server()
            
            # Open browser for authorization
            auth_url = self.get_user_access_token_url(scopes)
            print(f"\n🌐 Opening browser for Twitch authorization...")
            print(f"If browser doesn't open, visit: {auth_url}")
            webbrowser.open(auth_url)
            
            # Wait for authorization code
            print("⏳ Waiting for authorization... (will timeout in 120 seconds)")
            timeout = 120
            start_time = time.time()
            
            while self.auth_code is None and (time.time() - start_time) < timeout:
                time.sleep(1)
            
            # Stop server
            self._stop_callback_server()
            
            if self.auth_code is None:
                self.logger.error("OAuth flow timed out")
                print("❌ Authorization timed out. Please try again.")
                return None
            
            # Exchange code for token
            token_data = self._exchange_code_for_token(self.auth_code)
            if token_data:
                self.logger.info("OAuth flow completed successfully")
                print("✅ Authorization successful!")
                return token_data
            else:
                print("❌ Failed to exchange authorization code for token")
                return None
                
        except Exception as e:
            self.logger.error(f"OAuth flow failed: {e}")
            print(f"❌ OAuth flow failed: {e}")
            return None
    
    def _start_callback_server(self):
        """Start local HTTP server to catch OAuth callback"""
        class CallbackHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, oauth_instance, *args, **kwargs):
                self.oauth_instance = oauth_instance
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                # Parse the callback URL
                parsed_url = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                
                if 'code' in query_params:
                    self.oauth_instance.auth_code = query_params['code'][0]
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    success_html = """
                    <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ Authorization Successful!</h1>
                    <p>You can close this tab and return to your bot.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                    </body></html>
                    """
                    self.wfile.write(success_html.encode())
                else:
                    # Send error response
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    error_html = """
                    <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ Authorization Failed</h1>
                    <p>Please try again.</p>
                    </body></html>
                    """
                    self.wfile.write(error_html.encode())
            
            def log_message(self, format, *args):
                pass  # Suppress default logging
        
        # Create handler with oauth instance
        handler = lambda *args, **kwargs: CallbackHandler(self, *args, **kwargs)
        
        # Start server
        try:
            self.server = socketserver.TCPServer(("localhost", self.redirect_port), handler)
            server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            server_thread.start()
        except PermissionError:
            if self.redirect_port == 80:
                self.logger.error("Cannot bind to port 80 without admin privileges")
                print("❌ Cannot use port 80 without admin privileges.")
                print("Please update your Twitch app redirect URI to: http://localhost:3000")
                raise
            else:
                raise
    
    def _stop_callback_server(self):
        """Stop the callback server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
    
    def _exchange_code_for_token(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to exchange code for token: {e}")
            return None
    
    def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Validate an access token and get user info"""
        try:
            headers = {'Authorization': f'OAuth {access_token}'}
            response = requests.get(self.validate_url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Token validation failed: {e}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh an access token using refresh token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            return None


def save_token_data(token_data: Dict[str, Any], filename: str = "twitch_token.json"):
    """Save token data to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(token_data, f, indent=2)
        print(f"✅ Token data saved to {filename}")
    except Exception as e:
        print(f"❌ Failed to save token data: {e}")


def load_token_data(filename: str = "twitch_token.json") -> Optional[Dict[str, Any]]:
    """Load token data from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"❌ Failed to load token data: {e}")
        return None


def interactive_oauth_setup():
    """Interactive OAuth setup for users"""
    print("\n" + "="*60)
    print("🔑 TWITCH OAUTH SETUP")
    print("="*60)
    print()
    print("You'll need your Twitch application credentials:")
    print("1. Go to https://dev.twitch.tv/console/apps")
    print("2. Create/select your application")
    print("3. Copy the Client ID and Client Secret")
    print()
    print("⚠️  IMPORTANT: OAuth Redirect URI Setup")
    print("Make sure your Twitch app has one of these redirect URIs:")
    print("   - http://localhost:3000 (recommended)")
    print("   - http://localhost (requires admin privileges)")
    print()
    
    client_id = input("Enter your Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required")
        return None
    
    client_secret = input("Enter your Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required")
        return None
    
    # Ask about redirect URI preference
    print("\nWhich redirect URI is configured in your Twitch app?")
    print("1. http://localhost:3000 (recommended)")
    print("2. http://localhost (port 80)")
    
    redirect_choice = input("Choose (1-2, default 1): ").strip()
    
    if redirect_choice == "2":
        redirect_port = 80
        print("⚠️  Using port 80 - you may need to run as administrator")
    else:
        redirect_port = 3000
        print("✅ Using port 3000")
    
    print("\n🔄 Starting OAuth flow...")
    oauth = TwitchOAuth(client_id, client_secret, redirect_port)
    
    # Try OAuth flow
    try:
        token_data = oauth.start_oauth_flow()
    except PermissionError:
        print("\n❌ Permission denied for port 80")
        print("Please either:")
        print("1. Run as administrator, or")
        print("2. Update your Twitch app redirect URI to: http://localhost:3000")
        return None
    except Exception as e:
        if "redirect_mismatch" in str(e).lower():
            print(f"\n❌ OAuth Error: Redirect URI mismatch")
            print("Please check your Twitch application settings:")
            print(f"Expected redirect URI: {oauth.redirect_uri}")
            print("\nTo fix this:")
            print("1. Go to https://dev.twitch.tv/console/apps")
            print("2. Select your application")
            print("3. Click 'Manage'")
            print(f"4. Add '{oauth.redirect_uri}' to OAuth Redirect URLs")
            print("5. Save and try again")
            return None
        else:
            print(f"❌ OAuth Error: {e}")
            return None
    
    if token_data:
        print(f"\n✅ OAuth successful!")
        print(f"Access Token: {token_data.get('access_token', 'N/A')[:20]}...")
        print(f"Token Type: {token_data.get('token_type', 'N/A')}")
        print(f"Expires In: {token_data.get('expires_in', 'N/A')} seconds")
        
        # Validate token to get user info
        user_info = oauth.validate_token(token_data['access_token'])
        if user_info:
            print(f"Bot Username: {user_info.get('login', 'N/A')}")
            print(f"User ID: {user_info.get('user_id', 'N/A')}")
        
        # Save token data
        save_token_data(token_data)
        
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'username': user_info.get('login') if user_info else None
        }
    
    return None


if __name__ == "__main__":
    # Run interactive setup
    result = interactive_oauth_setup()
    if result:
        print("\n🎉 Setup complete! You can now use your bot.")
        print("Run your bot with the generated token file.")
    else:
        print("\n❌ Setup failed. Please try again.")
