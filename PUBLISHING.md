# Publishing to PyPI

When ready to publish to PyPI:

## First-time setup

1. Create account on [PyPI](https://pypi.org/)
2. Create API token at https://pypi.org/manage/account/token/
3. Configure `uv` with token:
   ```bash
   uv config set pypi.token "pypi-<your-token>"
   ```

## Publishing

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Commit changes:
   ```bash
   git add -A
   git commit -m "chore: prepare release v0.1.0"
   git tag v0.1.0
   git push origin main --tags
   ```
4. Build and publish:
   ```bash
   uv build
   uv publish
   ```

## Installation

After publishing, users can install with:
```bash
pip install notion-to-json
# or
uv pip install notion-to-json
# or
uvx notion-to-json
```