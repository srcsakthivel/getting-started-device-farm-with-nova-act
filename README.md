# Getting Started: Amazon Nova Act + AWS Device Farm (Mobile Testing)

A minimal, standalone sample showing how to run **Amazon Nova Act** tests on **real mobile devices** via **AWS Device Farm** — define test actions in plain English, and Nova Act drives the device visually.

```
You (natural language) → Nova Act (visual AI) → Appium → Device Farm (real device)
```

## What This Does

Nova Act's visual AI model drives real Android/iOS devices on AWS Device Farm. You define test actions in plain English, and Nova Act taps, swipes, and verifies the UI visually — no selectors, no Appium scripts to maintain.

## Project Structure

```
getting-started-device-farm-with-nova-act/
├── README.md
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── apps/
│   └── AWSDeviceFarmAndroidReferenceApp.apk  # Reference app for testing
├── screenshots/                           # Test output screenshots
│   ├── battery_screenshot.png
│   ├── display_screenshot.png
│   ├── traditional_battery_screenshot.png
│   └── traditional_display_screenshot.png
└── src/
    ├── android_getting_started.py         # Android quick start (Settings app)
    ├── ios_getting_started.py             # iOS quick start (Settings app)
    ├── android_custom_app.py              # Reference App tests (Login, Alerts, Fixtures)
    ├── custom_app_getting_started.py      # Custom app with upload (generic template)
    ├── android_traditional_appium.py      # Traditional Appium comparison (shows fragility)
    └── nova_act_mobile/                   # Vendored mobile helper library
        ├── ATTRIBUTION.md
        └── ...
```

## Prerequisites

1. **Python 3.11+**
2. **AWS Account** with Device Farm access (us-west-2)
3. **AWS CLI** configured with credentials that have `devicefarm:*` permissions

## Setup

```bash
# Clone this repo
git clone <repo-url>
cd getting-started-device-farm-with-nova-act

# Install dependencies
pip install -r requirements.txt
# OR with uv:
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your workflow definition name and device ARN
```

## Authentication

| Method | How | When |
|--------|-----|------|
| **Workflow Definition** (recommended) | `workflow_definition_name="device-farm-sample"` in code | Production, CI/CD, team usage |
| **API Key** (quick start) | `export NOVA_ACT_API_KEY=...` | Local development |

## Run

All scripts are in the `src/` directory:

```bash
cd src/
```

### Android — Settings App (no app upload needed)
```bash
python android_getting_started.py
```

### iOS — Settings App (no app upload needed)
```bash
python ios_getting_started.py
```

### Custom App — AWS Device Farm Reference App
```bash
python android_custom_app.py
```

### Custom App — Generic Template (bring your own APK/IPA)
```bash
python custom_app_getting_started.py --app-path ../apps/your-app.apk \
    --app-package com.yourcompany.app \
    --app-activity .MainActivity
```

### Traditional Appium (comparison)
```bash
python android_traditional_appium.py
```

## Key Learnings & Best Practices

| Pattern | Why |
|---------|-----|
| Use `type_text()` for credentials | Avoids guardrails + prevents prompt leaking |
| Use `clear_focused()` before typing | Prevents text concatenation with existing field content |
| One action per `act()` call | More reliable than compound instructions |
| Tap tabs directly (don't swipe) | Portrait viewport causes swipe issues |
| `workflow_definition_name` auth | Production-grade; logs to S3, team-shareable |

## Dependencies

The `src/nova_act_mobile/` directory contains helper code vendored from
[amazon-agi-labs/nova-act-samples](https://github.com/amazon-agi-labs/nova-act-samples)
with import path adjustments for this project. See `src/nova_act_mobile/ATTRIBUTION.md`
for source details, commit SHA, and modification notes.

### Key Classes (from nova_act_mobile)

| Class | Purpose |
|-------|---------|
| `NovaActMobile` | Main entry point — extends `NovaAct` with mobile support |
| `MobileActuator` | Appium-based actuator (handles screenshots, taps, scrolls) |
| `DeviceFarmActuator` | Provisions Device Farm remote sessions automatically |

## IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "devicefarm:ListProjects",
        "devicefarm:CreateProject",
        "devicefarm:ListDevices",
        "devicefarm:CreateRemoteAccessSession",
        "devicefarm:GetRemoteAccessSession",
        "devicefarm:StopRemoteAccessSession",
        "devicefarm:CreateUpload",
        "devicefarm:GetUpload",
        "devicefarm:ListUploads"
      ],
      "Resource": "*"
    }
  ]
}
```

## Cost

- **Device Farm**: $0.17/device minute (first 1000 min free with AWS Free Tier)
- **Nova Act**: Pay-per-step pricing (see [pricing page](https://aws.amazon.com/nova/act/pricing/))
- **Typical getting-started run**: ~$0.50 (3 min device time + ~10 Nova Act steps)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `No devices with remote access enabled` | Ensure your account has Device Farm access in us-west-2 |
| `NOVA_ACT_API_KEY not set` | Export your API key or use workflow definition auth |
| `Session failed to reach RUNNING state` | Device Farm is provisioning — retry in 30s |
| `Upload failed` | Check your APK/IPA is valid and not corrupted |

## Next Steps

- **QA assertions**: See `examples/qa/mobile_qa/` in `nova-act-samples` for `nova.check()` and `nova.expect()`
- **Deep links**: Launch apps at specific screens with `deep_link="myapp://screen"`
- **Permissions**: Pre-grant Android permissions to suppress dialogs
- **CI/CD deployment**: See `cdk/` in `nova-act-samples` for Lambda/ECS deployment

## References

- [Amazon Nova Act Documentation](https://docs.aws.amazon.com/nova-act/)
- [AWS Device Farm Documentation](https://docs.aws.amazon.com/devicefarm/)
- [nova-act-samples (full repo)](https://github.com/amazon-agi-labs/nova-act-samples)
- [Mobile Actuation README](https://github.com/amazon-agi-labs/nova-act-samples/tree/main/examples/actuation/mobile)

## License

MIT-0
