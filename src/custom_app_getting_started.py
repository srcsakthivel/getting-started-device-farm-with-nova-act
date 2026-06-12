"""Getting Started: Nova Act + AWS Device Farm (Custom App Upload).

Upload your own APK/IPA to Device Farm and run Nova Act tests on it.

Prerequisites:
    1. pip install -r requirements.txt
    2. export NOVA_ACT_API_KEY="your-api-key"
    3. AWS credentials configured with Device Farm access
    4. An APK or IPA file to test

Usage:
    # Android
    python custom_app_getting_started.py \
        --app-path /path/to/your-app.apk \
        --app-package com.yourcompany.app \
        --app-activity .MainActivity

    # iOS
    python custom_app_getting_started.py \
        --app-path /path/to/your-app.ipa \
        --bundle-id com.yourcompany.app
"""

import os
import sys
import logging
import time
import argparse
from dotenv import load_dotenv
from pathlib import Path

import boto3
import requests
from appium import webdriver
from appium.options.common import AppiumOptions
from nova_act import workflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Nova Act Workflow Definition (production auth)
WORKFLOW_DEFINITION_NAME = os.environ["NOVA_ACT_WORKFLOW_DEFINITION_NAME"]


# --- Device Farm Helpers ---

def get_or_create_project(client) -> str:
    """Get first Device Farm project or create one."""
    projects = client.list_projects().get("projects", [])
    if projects:
        return projects[0]["arn"]
    response = client.create_project(name="Nova Act Getting Started")
    return response["project"]["arn"]


def upload_app(client, project_arn: str, app_path: str) -> str:
    """Upload APK/IPA to Device Farm and wait for success. Returns upload ARN."""
    path = Path(app_path)
    if not path.exists():
        raise FileNotFoundError(f"App file not found: {app_path}")

    # Determine upload type from extension
    ext = path.suffix.lower()
    if ext == ".apk":
        upload_type = "ANDROID_APP"
    elif ext == ".ipa":
        upload_type = "IOS_APP"
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use .apk or .ipa")

    logger.info(f"📤 Uploading {path.name} to Device Farm...")

    # Create upload entry
    response = client.create_upload(
        projectArn=project_arn,
        name=path.name,
        type=upload_type,
    )
    upload_arn = response["upload"]["arn"]
    upload_url = response["upload"]["url"]

    # Upload the file to the presigned URL
    with open(app_path, "rb") as f:
        put_response = requests.put(upload_url, data=f)
        put_response.raise_for_status()

    # Poll until upload succeeds
    for attempt in range(30):
        status_response = client.get_upload(arn=upload_arn)
        status = status_response["upload"]["status"]
        if status == "SUCCEEDED":
            logger.info(f"✅ Upload complete: {upload_arn}")
            return upload_arn
        elif status == "FAILED":
            error = status_response["upload"].get("message", "Unknown error")
            raise RuntimeError(f"Upload failed: {error}")
        time.sleep(2)

    raise RuntimeError("Upload timed out")


def discover_device(client, platform: str) -> str:
    """Find a device with remote access enabled for the given platform."""
    devices = client.list_devices().get("devices", [])
    candidates = [
        d for d in devices
        if d.get("platform") == platform and d.get("remoteAccessEnabled") is True
    ]
    if not candidates:
        raise RuntimeError(f"No {platform} devices with remote access found")

    # Pick newest OS version
    candidates.sort(key=lambda d: str(d.get("os", "0")), reverse=True)
    device = candidates[0]
    logger.info(f"📱 Using device: {device['name']} ({platform} {device.get('os')})")
    return device["arn"]


def create_session(client, project_arn: str, device_arn: str, app_arn: str = None) -> str:
    """Create Remote Access Session with optional app pre-install."""
    kwargs = {
        "projectArn": project_arn,
        "deviceArn": device_arn,
        "name": "nova-act-custom-app",
    }
    if app_arn:
        kwargs["appArn"] = app_arn  # Device Farm pre-installs the app

    response = client.create_remote_access_session(**kwargs)
    session_arn = response["remoteAccessSession"]["arn"]

    logger.info("⏳ Waiting for device session...")
    for _ in range(60):
        status_response = client.get_remote_access_session(arn=session_arn)
        session = status_response["remoteAccessSession"]
        if session["status"] == "RUNNING":
            endpoint = session["endpoints"]["remoteDriverEndpoint"]
            logger.info("✅ Device session ready!")
            return endpoint
        elif session["status"] in ("COMPLETED", "STOPPING"):
            raise RuntimeError(f"Session failed: {session['status']}")
        time.sleep(5)

    raise RuntimeError("Session timed out")


# --- Main Test ---

@workflow(workflow_definition_name=WORKFLOW_DEFINITION_NAME, model_id="nova-act-latest")
def main(app_path: str, app_package: str = None, app_activity: str = None,
         bundle_id: str = None, device_arn: str = None) -> None:
    """Upload a custom app and run Nova Act tests on a real device."""

    logger.info("🚀 Starting Nova Act + Device Farm (Custom App)")

    client = boto3.client("devicefarm", region_name="us-west-2")

    # Determine platform
    ext = Path(app_path).suffix.lower()
    is_android = ext == ".apk"
    platform = "ANDROID" if is_android else "IOS"

    # Validate args
    if is_android and not (app_package and app_activity):
        raise ValueError("Android apps require --app-package and --app-activity")
    if not is_android and not bundle_id:
        raise ValueError("iOS apps require --bundle-id")

    # Step 1: Setup
    project_arn = get_or_create_project(client)
    logger.info(f"Using project: {project_arn}")

    # Step 2: Upload app
    app_arn = upload_app(client, project_arn, app_path)

    # Step 3: Discover device (or use provided ARN)
    if not device_arn:
        device_arn = discover_device(client, platform)

    # Step 4: Create session (app is pre-installed by Device Farm)
    endpoint_url = create_session(client, project_arn, device_arn, app_arn)

    # Step 5: Connect Appium
    options = AppiumOptions()
    options.set_capability("platformName", "Android" if is_android else "iOS")
    options.set_capability("appium:deviceName", "Device Farm Device")

    if is_android:
        options.set_capability("appium:automationName", "UiAutomator2")
        options.set_capability("appPackage", app_package)
        options.set_capability("appActivity", app_activity)
    else:
        options.set_capability("appium:automationName", "XCUITest")
        options.set_capability("appium:bundleId", bundle_id)

    driver = webdriver.Remote(endpoint_url, options=options)
    logger.info("✅ Connected to device. App launched!")

    try:
        # Take initial screenshot
        screenshot = driver.get_screenshot_as_png()
        with open("../screenshots/custom_app_screenshot.png", "wb") as f:
            f.write(screenshot)
        logger.info("📸 Initial screenshot saved: ../screenshots/custom_app_screenshot.png")

        # --- This is where Nova Act shines ---
        # With NovaActMobile (from nova-act-samples), you'd write:
        #
        #   nova.act("Tap the Sign In button")
        #   nova.act("Enter 'testuser@example.com' in the email field")
        #   nova.act("Enter 'password123' in the password field")
        #   nova.act("Tap Submit")
        #   nova.check("The dashboard is visible with a welcome message")
        #
        # Instead of fragile XPath selectors that break when the UI changes!

        logger.info("\n🎉 Custom app is running on a real device!")
        logger.info("   With NovaActMobile, you can now drive it with natural language.")
        logger.info("   See the 'Full Integration' section in the README.")

    finally:
        driver.quit()
        logger.info("\n✅ Session closed. Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nova Act + Device Farm custom app test")
    parser.add_argument("--app-path", required=True, help="Path to APK or IPA file")
    parser.add_argument("--app-package", help="Android app package (e.g. com.example.app)")
    parser.add_argument("--app-activity", help="Android launch activity (e.g. .MainActivity)")
    parser.add_argument("--bundle-id", help="iOS bundle identifier")
    parser.add_argument("--device-arn", help="Specific Device Farm device ARN (auto-discovers if not set)")
    args = parser.parse_args()

    main(
        app_path=args.app_path,
        app_package=args.app_package,
        app_activity=args.app_activity,
        bundle_id=args.bundle_id,
        device_arn=args.device_arn,
    )
