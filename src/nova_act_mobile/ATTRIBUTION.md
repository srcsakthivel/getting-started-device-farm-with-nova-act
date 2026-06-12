# Attribution

This `nova_act_mobile/` package is a vendored (self-contained) copy of the mobile actuation package from:

**Source:** [amazon-agi-labs/nova-act-samples](https://github.com/amazon-agi-labs/nova-act-samples)
**Path:** `examples/actuation/mobile/nova_act_mobile/`
**Branch:** `main`
**Commit SHA:** _To fill in — run: `git ls-remote https://github.com/amazon-agi-labs/nova-act-samples HEAD | cut -f1`_
**License:** MIT-0 (see the source repository)
**Copied on:** 2026-06-08

## Modifications from original

1. All imports rewritten from `from examples.actuation.mobile.nova_act_mobile.*` → `from nova_act_mobile.*` (self-contained)
2. Added `_utils.py` bundling `get_logger()` and `poll_until()` (originally in `examples/utils.py` and `examples/actuation/mobile/utils/polling.py`)
3. `mypy_boto3_devicefarm` type stubs moved behind `TYPE_CHECKING` guards (not required at runtime)
4. Removed sample APK (21MB) from `app/samples/`

## Keeping in sync

To update this vendored copy from the upstream repo:

```bash
# Clone or update the source
cd /path/to/nova-act-samples
git pull

# Copy the package
cp -r examples/actuation/mobile/nova_act_mobile/ /path/to/this-repo/nova_act_mobile/

# Re-apply import fixes
# (or run the import rewrite script — see the project README)
```

## Why vendored (not pip-installed)?

The `nova-act-samples` repository is not structured as a pip-installable package (no `pyproject.toml` or `setup.py` at the root). Until it becomes installable, vendoring with fixed imports is the recommended approach for standalone projects.
