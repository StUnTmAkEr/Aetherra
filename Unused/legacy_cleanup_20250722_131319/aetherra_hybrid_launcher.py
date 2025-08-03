#!/usr/bin/env python3
"""
Lyrixa Hybrid UI Launcher Demo
==============================

This script demonstrates how to launch Lyrixa with the hybrid UI.
It's designed as a drop-in replacement for the existing launcher
with minimal changes required.

Usage:
    python aetherra_hybrid_launcher.py

Environment Variables:
    LYRIXA_UI_MODE=hybrid    # Enable hybrid UI
    LYRIXA_UI_MODE=classic   # Use original UI (default)
"""

import asyncio
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

# Set environment for hybrid UI
os.environ["LYRIXA_UI_MODE"] = "hybrid"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the existing launcher but with hybrid UI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(project_root / "Aetherra" / "lyrixa" / "gui" / "ui_config.env")


def check_port_available(port, host="127.0.0.1"):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
    except Exception:
        return True


def start_api_server():
    """Start the Enhanced API server embedded (no separate window)."""
    try:
        # Check if server is already running (port not available = server running)
        if not check_port_available(8007):
            print("✅ API server already running on port 8007")
            return True

        print("🚀 Starting Enhanced Self-Improvement Server (Embedded)...")

        # Import and start the embedded server
        try:
            from enhanced_self_improvement_server import start_server_thread

            # Start server in background thread (no separate console window)
            success = start_server_thread()

            if success:
                print("✅ Enhanced Self-Improvement Server started successfully")
                print("   • Running on http://127.0.0.1:8007")
                print("   • No separate console window")
                print("   • Integrated with Lyrixa GUI")
                return True
            else:
                print("[ERROR] Failed to start embedded server")
                return False

        except ImportError as e:
            print(f"[ERROR] Failed to import embedded server: {e}")
            print("   Falling back to external server...")

            # Fallback to external server (but without console window)
            server_path = project_root / "enhanced_api_server.py"

            if not server_path.exists():
                print("[ERROR] Enhanced API server file not found")
                return False

            # Start server in background WITHOUT console window
            process = subprocess.Popen(
                [sys.executable, str(server_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root),
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32"
                else 0,
            )

            # Wait for server to start
            time.sleep(3)

            # Check if server is now running
            if not check_port_available(8007):
                print("✅ Enhanced API Server started successfully on port 8007")
                return True
            else:
                print("[ERROR] Failed to start API server")
                return False

    except Exception as e:
        print(f"[ERROR] Error starting API server: {e}")
        return False


def start_api_server_async():
    """Start API server in a separate thread."""

    def run_server():
        start_api_server()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return server_thread


# Import and modify the launcher
try:
    # Import from the original launcher
    from PySide6.QtWidgets import QApplication

    from Aetherra.lyrixa.gui.window_factory import create_lyrixa_window
    from Aetherra.lyrixa.launcher import initialize_system

    def main():
        """Main function for hybrid UI launcher"""
        print("🌟 Lyrixa Hybrid UI Launcher Starting...")
        print(f"UI Mode: {os.getenv('LYRIXA_UI_MODE', 'classic')}")

        # Start API server automatically
        print("[TOOL] Initializing API services...")
        start_api_server_async()

        # Create Qt application
        app = QApplication(sys.argv)

        # Create window using factory (will auto-select hybrid mode)
        window = create_lyrixa_window()

        # Show window first for immediate feedback
        window.show()

        try:
            # Import asyncio explicitly to avoid scope issues
            import asyncio

            # Create event loop for async initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run initialization with GUI window reference
            loop.run_until_complete(initialize_system(window))

            # Import the global variables from launcher
            from Aetherra.lyrixa.launcher import intelligence_stack, lyrixa, runtime

            print("🔗 Attaching components to GUI...")

            # Attach components to GUI using modular methods
            print(f"[TOOL] DEBUG: intelligence_stack = {intelligence_stack}")
            print(f"[TOOL] DEBUG: runtime = {runtime}")
            print(f"[TOOL] DEBUG: lyrixa = {lyrixa}")

            if intelligence_stack:
                window.attach_intelligence_stack(intelligence_stack)
                print("✅ Intelligence stack attached to GUI")

            if runtime:
                window.attach_runtime(runtime)
                print("✅ Runtime attached to GUI")

            if lyrixa:
                print(f"[TOOL] DEBUG: About to call attach_lyrixa with {type(lyrixa)}")
                window.attach_lyrixa(lyrixa)
                # GUI interface connection handled by attach_lyrixa method

                # Initialize autonomous capabilities in the GUI
                print("🧠 Initializing autonomous capabilities in GUI...")
                if hasattr(lyrixa, 'aetherra_integration') and lyrixa.aetherra_integration:
                    print("✅ Autonomous capabilities detected - starting autonomous mode")
                    # Start autonomous mode
                    try:
                        import asyncio
                        autonomous_result = asyncio.run(lyrixa.aetherra_integration.start_autonomous_mode())
                        if autonomous_result.get('success'):
                            print("✅ Autonomous mode started successfully")
                        else:
                            print(f"[WARN] Autonomous mode start result: {autonomous_result}")
                    except Exception as e:
                        print(f"[WARN] Error starting autonomous mode: {e}")
                else:
                    print("[WARN] No autonomous capabilities found")

                print("✅ Lyrixa agent attached to GUI with autonomous capabilities enabled")
            else:
                print("[ERROR] DEBUG: lyrixa is None or undefined!")

            print("✅ Hybrid UI initialized successfully!")
            print("🎉 Lyrixa is ready with modern hybrid interface!")

        except Exception as e:
            print(f"[ERROR] Error during initialization: {e}")
            import traceback

            traceback.print_exc()

        # Start Qt event loop
        return app.exec()

    if __name__ == "__main__":
        sys.exit(main())

except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("💡 Make sure PySide6 is installed: py -m pip install PySide6")
    print("💡 Or run: python aetherra_launcher.py (for classic UI)")
    sys.exit(1)
