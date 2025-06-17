# Release Process

This document describes the release process for notion-to-json.

## Prerequisites

1. Ensure you have push access to the repository
2. Ensure the `release` environment is configured in GitHub repository settings
3. Configure PyPI trusted publishing:
   - Go to https://pypi.org/manage/account/publishing/
   - Add a new publisher with:
     - PyPI Project Name: `notion-to-json`
     - Owner: `jonatkinson`
     - Repository name: `notion-to-json`
     - Workflow name: `publish.yml`
     - Environment name: `release`

## Release Steps

1. **Update version**
   ```bash
   # Edit pyproject.toml and update the version field
   # Follow semantic versioning: MAJOR.MINOR.PATCH
   ```

2. **Update CHANGELOG.md**
   ```bash
   # Add a new section for the release with date
   # List all changes under appropriate categories:
   # - Added, Changed, Deprecated, Removed, Fixed, Security
   ```

3. **Run tests**
   ```bash
   make test
   make lint
   ```

4. **Commit changes**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: prepare release v0.2.0"
   ```

5. **Create and push tag**
   ```bash
   git tag v0.2.0
   git push origin main --tags
   ```

6. **Create GitHub release**
   - Go to https://github.com/jonatkinson/notion-to-json/releases/new
   - Choose the tag you just created
   - Set release title to "v0.2.0"
   - Copy the relevant section from CHANGELOG.md to the release description
   - Click "Publish release"

7. **Verify PyPI deployment**
   - The GitHub Action will automatically trigger
   - Check https://github.com/jonatkinson/notion-to-json/actions
   - Once successful, verify at https://pypi.org/project/notion-to-json/

## Post-release

1. **Test installation**
   ```bash
   # In a clean environment
   pip install notion-to-json
   notion-to-json --version
   ```

2. **Update development version**
   ```bash
   # Update pyproject.toml to next development version
   # e.g., 0.2.0 -> 0.3.0.dev0
   git add pyproject.toml
   git commit -m "chore: bump version to 0.3.0.dev0"
   git push
   ```