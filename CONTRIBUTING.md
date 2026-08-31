# Contributing / release workflow

## Version numbering

**Single source of truth:** `VERSION` in the bootstrap script
(`udi-unifiprotectapi-pg3x.py`).

After changing `VERSION`, sync mirrors:

```bash
make sync-version
# or
python scripts/sync_version.py --entry udi-unifiprotectapi-pg3x.py
```

Or bump in one step:

```bash
python scripts/bump_version.py 1.2.0 --entry udi-unifiprotectapi-pg3x.py
```

### Files updated automatically

| File | Purpose |
|------|---------|
| `profile/version.txt` | ISY/Easy UI profile sync |
| `server.json` → `credits[0].version` | Store manifest |

### Files you edit manually each release

| File | Purpose |
|------|---------|
| Bootstrap `VERSION` | Runtime version passed to `polyglot.start()` |
| `CHANGELOG.md` | Human-readable release notes |

CI (`test/test_profile.py`) fails if bootstrap `VERSION` ≠ `profile/version.txt`.

## Branch naming

Use **`main`** as the default branch.

## Dev commands

```bash
make install    # uv sync --dev
make lint       # ruff
make test       # pytest
make fulltest   # pre-commit all files
```

## server.json GitHub URLs

Development repo: `sejgit-udi-plugins/udi-unifiprotectapi-pg3x`.

Update `docs`, `credits[0].source`, and `credits[0].license` when migrating to UDI store org.
`sync_version.py` only updates `credits[0].version`, not URLs.
