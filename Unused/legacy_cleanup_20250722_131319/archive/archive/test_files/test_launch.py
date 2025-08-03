#!/usr/bin/env python3
"""
Simple test to run Lyrixa v2.0 and catch any errors
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Explicitly add src directory to sys.path
src_path = Path(__file__).resolve().parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Debug: Print sys.path to verify
print("sys.path:", sys.path)

try:
    print("🔍 Testing Lyrixa v2.0 launch...")

    # Test import
    print("[DISC] Importing modules...")
    from PySide6.QtWidgets import QApplication

    from Aetherra.ui.enhanced_lyrixa import (
        EnhancedLyrixaWindow as ModernLyrixaWindow,
    )

    # Define QT_AVAILABLE manually if needed
    QT_AVAILABLE = True  # Adjust based on actual logic in enhanced_lyrixa

    print(f"✅ Qt Available: {QT_AVAILABLE}")

    if not QT_AVAILABLE:
        print("❌ Qt not available")
        sys.exit(1)

    # Test application creation
    print("🚀 Creating application...")
    app = QApplication(sys.argv)

    print("🏗️ Creating window...")
    try:
        window = ModernLyrixaWindow()
        print("✅ Window created successfully!")
    except Exception as e:
        print(f"❌ Error creating window: {e}")
        import traceback

        traceback.print_exc()
        raise
    print("👁️ Showing window...")
    window.show()

    print("🎉 Launch successful! Window should be visible.")

    # Don't start the event loop, just test creation

except Exception as e:
    print(f"❌ Error during launch: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
