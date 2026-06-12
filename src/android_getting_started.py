"""Getting Started: Nova Act + AWS Device Farm (Android).

This minimal example demonstrates how to use Amazon Nova Act to automate
a real Android device on AWS Device Farm using natural language commands.

No app upload required — uses pre-installed Android Settings.

Prerequisites:
    1. pip install -r requirements.txt
    2. AWS credentials configured with Device Farm access (us-west-2)

Usage:
    python android_getting_started.py
"""

import logging
import os

from dotenv import load_dotenv
from nova_act import workflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration ---

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Nova Act Workflow Definition (production auth — logs to S3, team-shareable)
WORKFLOW_DEFINITION_NAME = os.environ["NOVA_ACT_WORKFLOW_DEFINITION_NAME"]

# Device Farm device ARN (from .env)
# Find available devices with: aws devicefarm list-devices --region us-west-2
DEFAULT_DEVICE_ARN = os.environ["DEVICE_FARM_DEVICE_ARN"]


# --- Main Test (using NovaActMobile) ---

@workflow(workflow_definition_name=WORKFLOW_DEFINITION_NAME, model_id="nova-act-latest")
def main() -> None:
    """Run a Nova Act mobile test on a real Android device via Device Farm."""

    # Import the bundled NovaActMobile package
    from nova_act_mobile import NovaActMobile

    logger.info("🚀 Starting Nova Act + Device Farm (Android) Getting Started")
    logger.info("   Using NovaActMobile for natural language device automation")

    # NovaActMobile handles EVERYTHING:
    # 1. Creates Device Farm Remote Access Session
    # 2. Waits for device to be ready
    # 3. Connects Appium (UiAutomator2)
    # 4. Bridges Nova Act's visual AI with the mobile screen
    # 5. Cleans up session on exit

    with NovaActMobile(
        app_package="com.android.settings",
        app_activity=".Settings",
        device_arn=DEFAULT_DEVICE_ARN,
    ) as nova:
        logger.info("✅ Connected to Device Farm + Appium — Nova Act ready!")

        # --- Natural Language Commands ---
        # Nova Act sees the screen visually and acts like a human would.
        # No XPath, no element IDs, no brittle selectors!

        # Step 1: Verify Settings launched
        logger.info("\n📱 Step 1: Verifying Settings app launched...")
        nova.act("Verify the Settings page is visible")
        logger.info("   ✅ Settings page confirmed")

        # Step 2: Navigate to Battery
        logger.info("🔋 Step 2: Navigating to Battery...")
        nova.act("Tap on 'Battery'")
        logger.info("   ✅ Battery page opened")

        # Step 3: Go back to Settings home
        logger.info("⬅️  Step 3: Going back to Settings home...")
        nova.act("Press the back button to return to Settings")
        logger.info("   ✅ Back at Settings home")

        # Step 4: Navigate to Display
        logger.info("🖥️  Step 4: Navigating to Display...")
        nova.act("Tap on 'Display'")
        logger.info("   ✅ Display page opened")

        # Step 5: Go back to Settings home
        logger.info("⬅️  Step 5: Going back to Settings home...")
        nova.act("Press the back button to return to Settings")
        logger.info("   ✅ Back at Settings home")

        logger.info("\n🎉 SUCCESS! Nova Act Android mobile automation working end-to-end!")
        logger.info("   ✅ Device Farm session created automatically")
        logger.info("   ✅ Natural language commands executed on real Android device")
        logger.info("   ✅ Multi-screen navigation (Settings → Battery → Display)")
        logger.info("   ✅ No XPath, no element IDs — just plain English!")


if __name__ == "__main__":
    main()
