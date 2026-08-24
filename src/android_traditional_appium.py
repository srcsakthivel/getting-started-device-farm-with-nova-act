"""Traditional Appium Test — Same scenario as android_getting_started.py.

This file does the EXACT same thing as android_getting_started.py (Nova Act version),
but uses traditional Appium with XPath/UiAutomator selectors.

Compare the two approaches:
  - android_getting_started.py    → Nova Act (natural language, AI-driven)
  - android_traditional_appium.py → Traditional Appium (selectors, manual setup)

Prerequisites:
    1. pip install Appium-Python-Client boto3 requests
    2. AWS credentials configured with Device Farm access (us-west-2)

Usage:
    python android_traditional_appium.py
"""

import os
import logging
import time

from dotenv import load_dotenv
import boto3
from appium import webdriver
from appium.options.common import AppiumOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration ---

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

DEFAULT_DEVICE_ARN = os.environ["DEVICE_FARM_DEVICE_ARN"]

# Screenshots dir (relative to project root, resolved from this file — works
# regardless of the current working directory)
SCREENSHOTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots"
)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


# --- Device Farm Session Setup (manual) ---
# In traditional Appium, YOU manage the entire Device Farm lifecycle.

def create_device_farm_session(device_arn: str) -> tuple[str, str]:
    """Create a Device Farm Remote Access Session.

    Returns (endpoint_url, session_arn) so we can clean up later.
    """
    client = boto3.client("devicefarm", region_name="us-west-2")

    # Discover or create project
    projects = client.list_projects().get("projects", [])
    if projects:
        project_arn = projects[0]["arn"]
    else:
        response = client.create_project(name="Traditional Appium Test")
        project_arn = response["project"]["arn"]

    # Create remote access session
    logger.info(f"Creating remote access session on device: {device_arn}")
    response = client.create_remote_access_session(
        projectArn=project_arn,
        deviceArn=device_arn,
        name="traditional-appium-test",
    )
    session_arn = response["remoteAccessSession"]["arn"]

    # Poll until RUNNING
    logger.info("Waiting for device session to be ready...")
    for _ in range(60):
        status_response = client.get_remote_access_session(arn=session_arn)
        session = status_response["remoteAccessSession"]
        status = session["status"]
        if status == "RUNNING":
            endpoint = session["endpoints"]["remoteDriverEndpoint"]
            logger.info(f"✅ Device session ready!")
            return endpoint, session_arn
        elif status in ("COMPLETED", "STOPPING"):
            raise RuntimeError(f"Session failed with status: {status}")
        time.sleep(5)

    raise RuntimeError("Session timed out waiting for RUNNING state")


def stop_session(session_arn: str):
    """Clean up — stop the remote access session."""
    try:
        client = boto3.client("devicefarm", region_name="us-west-2")
        client.stop_remote_access_session(arn=session_arn)
        logger.info("🧹 Device Farm session stopped")
    except Exception as e:
        logger.warning(f"Could not stop session: {e}")


# --- Traditional Appium Test ---

def main() -> None:
    """Traditional Appium test — same scenario as android_getting_started.py."""

    logger.info("🚀 Starting Traditional Appium Test (Android)")
    logger.info("   ⚠️  Compare with android_getting_started.py (Nova Act version)")

    # Step 1: Create Device Farm session (manual setup)
    endpoint_url, session_arn = create_device_farm_session(DEFAULT_DEVICE_ARN)

    # Step 2: Configure Appium capabilities (manual)
    options = AppiumOptions()
    options.set_capability("platformName", "Android")
    options.set_capability("appium:deviceName", "Google Pixel 10")
    options.set_capability("appium:automationName", "UiAutomator2")
    options.set_capability("appPackage", "com.android.settings")
    options.set_capability("appActivity", ".Settings")
    options.set_capability("appium:newCommandTimeout", 120)

    # Step 3: Connect to the device
    driver = webdriver.Remote(endpoint_url, options=options)
    logger.info("✅ Connected to device via Appium")

    try:
        # Wait for Settings to load
        logger.info("⏳ Waiting for Settings app to load...")
        time.sleep(5)

        # ─────────────────────────────────────────────────────────────
        # Step 4: Navigate to Battery page
        # ─────────────────────────────────────────────────────────────
        # PROBLEM: We need the exact text or selector for "Battery".
        # Different Android versions/skins use different labels:
        #   - Stock Android 14+: "Battery"
        #   - Samsung OneUI: "Battery and device care"
        #   - Xiaomi MIUI: "Battery & performance"
        # This test will BREAK if the label changes!
        # ─────────────────────────────────────────────────────────────
        logger.info("\n📱 Navigating to Battery page...")

        # Try multiple selectors (fragile — breaks across devices/OS versions)
        battery_selectors = [
            ('xpath', '//*[@text="Battery"]'),
            ('xpath', '//*[contains(@text, "Battery")]'),
            ('-android uiautomator', 'new UiScrollable(new UiSelector().scrollable(true)).scrollTextIntoView("Battery")'),
        ]

        battery_found = False
        for by, selector in battery_selectors:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                element.click()
                battery_found = True
                logger.info("   ✅ Found and tapped 'Battery'")
                break
            except Exception:
                continue

        if not battery_found:
            # Last resort: scroll down and try again
            driver.execute_script(
                "mobile: scrollGesture",
                {"left": 100, "top": 500, "width": 800, "height": 500, "direction": "down", "percent": 0.75}
            )
            time.sleep(2)
            try:
                element = driver.find_element("xpath", '//*[contains(@text, "Battery")]')
                element.click()
                logger.info("   ✅ Found 'Battery' after scrolling")
            except Exception as e:
                logger.error(f"   ❌ Could not find Battery: {e}")
                logger.error("   This is the problem with selectors — they break across devices!")
                raise

        time.sleep(2)

        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        with open("../screenshots/traditional_battery_screenshot.png", "wb") as f:
            f.write(screenshot)
        logger.info("📸 Battery screenshot saved: ../screenshots/traditional_battery_screenshot.png")

        # ─────────────────────────────────────────────────────────────
        # Step 5: Go back to Settings home
        # ─────────────────────────────────────────────────────────────
        logger.info("⬅️  Going back to Settings home...")
        driver.back()
        time.sleep(2)

        # ─────────────────────────────────────────────────────────────
        # Step 6: Navigate to Display settings
        # ─────────────────────────────────────────────────────────────
        # PROBLEM: Same fragility — text might be "Display",
        # "Display & brightness", "Screen", etc.
        # ─────────────────────────────────────────────────────────────
        logger.info("🖥️  Navigating to Display settings...")

        display_selectors = [
            ('xpath', '//*[@text="Display"]'),
            ('xpath', '//*[contains(@text, "Display")]'),
            ('xpath', '//*[contains(@text, "display")]'),
            ('-android uiautomator', 'new UiScrollable(new UiSelector().scrollable(true)).scrollTextIntoView("Display")'),
        ]

        display_found = False
        for by, selector in display_selectors:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                element.click()
                display_found = True
                logger.info("   ✅ Found and tapped 'Display'")
                break
            except Exception:
                continue

        if not display_found:
            # Even more fallbacks — this is the POINT of the demo
            logger.warning("   ⚠️  Could not find 'Display' — trying scroll + broader match")
            driver.execute_script(
                "mobile: scrollGesture",
                {"left": 100, "top": 500, "width": 800, "height": 500, "direction": "down", "percent": 0.75}
            )
            time.sleep(2)
            try:
                element = driver.find_element("xpath", '//*[contains(@text, "isplay")]')
                element.click()
                display_found = True
                logger.info("   ✅ Found 'Display' after scroll + fuzzy match")
            except Exception:
                logger.error("   ❌ Could not find Display — THIS IS THE POINT!")
                logger.error("   Traditional selectors BREAK across devices/OS versions.")
                logger.error("   Nova Act would simply: nova.act(\"Tap on Display\")")

        time.sleep(2)

        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        with open("../screenshots/traditional_display_screenshot.png", "wb") as f:
            f.write(screenshot)
        logger.info("📸 Display screenshot saved: ../screenshots/traditional_display_screenshot.png")

        logger.info("\n✅ Traditional Appium test completed!")
        logger.info("   ⚠️  Notice the problems with this approach:")
        logger.info("   • Multiple fallback selectors needed for ONE element")
        logger.info("   • Scrolling logic required (what if Battery is below the fold?)")
        logger.info("   • Test breaks on different devices/OS versions/skins")
        logger.info("   • Explicit waits and sleeps everywhere")
        logger.info("   • 150+ lines of code for what Nova Act does in 4 lines")

    finally:
        driver.quit()
        stop_session(session_arn)
        logger.info("✅ Session closed. Done!")


# ─────────────────────────────────────────────────────────────────────
# COMPARISON:
#
# ┌────────────────────────────────────┬────────────────────────────────┐
# │  Nova Act (android_getting_started)│  Traditional Appium (this file)│
# ├────────────────────────────────────┼────────────────────────────────┤
# │  nova.act("Tap on 'Battery'")     │  15+ lines of selector logic   │
# │                                    │  + fallbacks + scroll + waits  │
# ├────────────────────────────────────┼────────────────────────────────┤
# │  nova.act("Press the back button  │  driver.back()                 │
# │  to return to Settings")           │  time.sleep(2)                 │
# ├────────────────────────────────────┼────────────────────────────────┤
# │  nova.act("Tap on 'Display'")     │  15+ lines of selector logic   │
# │                                    │  + fallbacks + scroll + waits  │
# ├────────────────────────────────────┼────────────────────────────────┤
# │  Device Farm setup: AUTOMATIC      │  Device Farm setup: 50+ lines │
# │  (NovaActMobile handles it)        │  (manual boto3 + polling)     │
# ├────────────────────────────────────┼────────────────────────────────┤
# │  Cleanup: AUTOMATIC                │  Cleanup: manual stop_session()│
# ├────────────────────────────────────┼────────────────────────────────┤
# │  Adapts to UI changes: YES         │  Breaks on UI changes: YES     │
# ├────────────────────────────────────┼────────────────────────────────┤
# │  Total lines: ~30                  │  Total lines: ~170             │
# └────────────────────────────────────┴────────────────────────────────┘
# ─────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    main()
