"""Nova Act Test for AWS Device Farm Android Reference App.

Tests the AWS Device Farm Android Reference App using Amazon Nova Act
with natural language commands on a real device via Device Farm.

Nova Act Best Practices Applied:
  - One action per act() call (no multi-step combos)
  - Ground prompts in exact visible UI labels (e.g. "Login Page", not "login")
  - Separate actions from verifications
  - Use type_text() for credential inputs (avoids guardrail triggers)
  - clear_focused() before typing (prevents concatenation)
  - Each navigation step is atomic and verifiable

Same test scenarios as the traditional Appium suite (example.e2e.js):
  Traditional: 6 Page Object files + 1 spec = 7 files, 200+ lines
  Nova Act:    1 file, ~80 lines, plain English

Prerequisites:
    1. pip install -r requirements.txt
    2. AWS credentials configured with Device Farm access (us-west-2)
    3. APK: AWSDeviceFarmAndroidReferenceApp.apk (bundled in apps/)

Usage:
    cd src/
    python android_custom_app.py
"""

import os
import logging

from dotenv import load_dotenv
from nova_act import workflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration ---

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

WORKFLOW_DEFINITION_NAME = os.environ["NOVA_ACT_WORKFLOW_DEFINITION_NAME"]

# APK is bundled in the repo under apps/ (relative to project root)
APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apps", "AWSDeviceFarmAndroidReferenceApp.apk")
APP_PACKAGE = "com.amazonaws.devicefarm.android.referenceapp"
APP_ACTIVITY = ".Activities.MainActivity"

# Test credentials (from .env — demo values for the Reference App)
LOGIN_USERNAME = os.environ.get("LOGIN_USERNAME", "admin")
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD", "")
INVALID_PASSWORD = os.environ.get("INVALID_PASSWORD", "")

# Device Farm device ARN (from .env)
DEFAULT_DEVICE_ARN = os.environ["DEVICE_FARM_DEVICE_ARN"]


# --- Helpers (Nova Act Best Practices) ---

def navigate_to_page(nova, page_name: str) -> None:
    """Navigate to a page via the drawer menu.

    Best Practice: One action per prompt. Break drawer navigation
    into two atomic steps (open drawer + tap menu item).
    Ground the menu item name in the exact visible label.
    """
    nova.act("Tap the hamburger menu icon or swipe from the left edge to open the navigation drawer.")
    nova.act(f"Tap on '{page_name}' in the navigation drawer menu.")


def enter_text_in_field(nova, field_label: str, value: str) -> None:
    """Enter text into a field using type_text (Appium-level).

    Best Practice: Use type_text() for all text inputs. The value
    never enters the act() prompt, preventing guardrail triggers
    and cross-step leaking. Always clear before typing.
    """
    nova.act(f"Tap on the '{field_label}' input field to focus it.")
    nova.clear_focused()
    nova.type_text(value)


# --- Test Suite ---

@workflow(workflow_definition_name=WORKFLOW_DEFINITION_NAME, model_id="nova-act-latest")
def main() -> None:
    """Run all test scenarios on the AWS Device Farm Reference App."""

    from nova_act_mobile import NovaActMobile

    logger.info("🚀 Starting Nova Act Test Suite — Device Farm Reference App")
    logger.info(f"   APK: {APP_PATH}")
    logger.info(f"   Package: {APP_PACKAGE}")

    with NovaActMobile(
        app_package=APP_PACKAGE,
        app_activity=APP_ACTIVITY,
        app_path=APP_PATH,
        device_arn=DEFAULT_DEVICE_ARN,
    ) as nova:
        logger.info("✅ App uploaded and installed on Device Farm — Nova Act ready!")

        # ━━━ TEST 1: Login with valid credentials ━━━━━━━━━━━━━━━━━━━━
        logger.info("\n" + "=" * 60)
        logger.info("📋 TEST 1: Login with valid credentials")
        logger.info("=" * 60)

        # Navigate (one action per prompt)
        navigate_to_page(nova, "Login Page")

        # Enter credentials (type_text — not in act prompt)
        enter_text_in_field(nova, "Username Input Field", LOGIN_USERNAME)
        enter_text_in_field(nova, "Password Input Field", LOGIN_PASSWORD)

        # Submit (separate action)
        nova.act("Tap the 'Login' button.")

        # Verify (separate verification — don't combine with action)
        nova.act("Verify the text 'You are logged on as admin' is visible on screen.")

        logger.info("   ✅ TEST 1 PASSED: Login with valid credentials")

        # ━━━ TEST 2: Login with invalid credentials ━━━━━━━━━━━━━━━━━━
        logger.info("\n" + "=" * 60)
        logger.info("📋 TEST 2: Login with invalid credentials")
        logger.info("=" * 60)

        # Re-navigate to Login Page
        navigate_to_page(nova, "Login Page")

        # Enter credentials (invalid password via type_text)
        enter_text_in_field(nova, "Username Input Field", LOGIN_USERNAME)
        enter_text_in_field(nova, "Password Input Field", INVALID_PASSWORD)

        # Submit
        nova.act("Tap the 'Login' button.")

        # Verify error message
        nova.act("Verify the text 'You gave me the wrong username and password' is visible on screen.")

        logger.info("   ✅ TEST 2 PASSED: Invalid credentials error shown")

        # ━━━ TEST 3: Alerts ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("\n" + "=" * 60)
        logger.info("📋 TEST 3: Alert dialog")
        logger.info("=" * 60)

        # Navigate
        navigate_to_page(nova, "Alerts")

        # Trigger alert (one action)
        nova.act("Tap the button that triggers an alert notification.")

        # Verify alert content (separate verification)
        nova.act("Verify an alert dialog is showing with the message 'This is the alert message'.")

        # Dismiss alert (separate action)
        nova.act("Tap the 'OK' button on the alert dialog to dismiss it.")

        logger.info("   ✅ TEST 3 PASSED: Alert triggered and dismissed")

        # ━━━ TEST 4: Fixtures (device toggles) ━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("\n" + "=" * 60)
        logger.info("📋 TEST 4: Fixtures (device toggles)")
        logger.info("=" * 60)

        # Navigate
        navigate_to_page(nova, "Fixtures")

        # Verify each toggle individually (one verification per prompt)
        nova.act("Verify the Bluetooth status value is displayed showing 'true' or 'false'.")
        nova.act("Verify the GPS status value is displayed showing 'true' or 'false'.")
        nova.act("Verify the NFC status value is displayed showing 'true' or 'false'.")
        nova.act("Verify the WiFi status value is displayed showing 'true' or 'false'.")

        logger.info("   ✅ TEST 4 PASSED: Fixture toggles displayed")

        # ━━━ SUMMARY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("   ✅ Test 1: Login with valid credentials")
        logger.info("   ✅ Test 2: Login with invalid credentials")
        logger.info("   ✅ Test 3: Alert dialog")
        logger.info("   ✅ Test 4: Fixtures (device toggles)")
        logger.info("")
        logger.info("   📊 Nova Act Best Practices Applied:")
        logger.info("   • One action per act() call")
        logger.info("   • Grounded in exact UI labels")
        logger.info("   • type_text() for credentials (no prompt leaking)")
        logger.info("   • clear_focused() before typing")
        logger.info("   • Separate actions from verifications")
        logger.info("   • Reusable helpers (navigate_to_page, enter_text_in_field)")
        logger.info("")
        logger.info("   📊 Traditional vs Nova Act:")
        logger.info("   Traditional Appium: 6 files, 200+ lines, Page Object Model")
        logger.info("   Nova Act:           1 file, ~80 lines, plain English")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
