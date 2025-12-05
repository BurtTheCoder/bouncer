#!/usr/bin/env python3
"""
Test script to verify wizard can be imported and initialized
"""

import sys
from pathlib import Path

# Test imports
try:
    from bouncer.wizard import BouncerWizard
    print("✅ Wizard module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import wizard: {e}")
    sys.exit(1)

# Test initialization
try:
    wizard = BouncerWizard(config_path=Path("/tmp/test_wizard.yaml"))
    print("✅ Wizard initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize wizard: {e}")
    sys.exit(1)

# Test screen imports
try:
    from bouncer.wizard.screens import (
        WelcomeScreen,
        DirectoryScreen,
        BouncersScreen,
        NotificationsScreen,
        IntegrationsScreen,
        ReviewScreen,
        SuccessScreen
    )
    print("✅ All screens imported successfully")
except ImportError as e:
    print(f"❌ Failed to import screens: {e}")
    sys.exit(1)

# Verify CSS file exists
css_path = Path("bouncer/wizard/styles.tcss")
if css_path.exists():
    print(f"✅ CSS file exists: {css_path}")
else:
    print(f"⚠️  CSS file not found: {css_path}")

print("\n🎉 All wizard components verified!")
print("\nTo launch the wizard:")
print("  python main.py wizard")
print("  python main.py wizard --config my_config.yaml")
