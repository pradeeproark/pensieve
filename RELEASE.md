# Release Process

This document describes how to create a new release of Pensieve.

## Overview

Pensieve uses a semi-automated release process:
1. Update version number
2. Create git tag
3. Push tag to trigger GitHub Actions
4. GitHub Actions builds and releases macOS binary
5. Manually update Homebrew formula (will be automated in future)

## Version Strategy

Pensieve follows [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Step-by-Step Release

### 1. Prepare the Release

**Update version in `pyproject.toml`:**
```toml
[project]
version = "X.Y.Z"  # Update this line
```

**Test everything works:**
```bash
# Run tests
pytest

# Test build locally
python build_executable.py

# Verify version is correct
dist/pensieve-X.Y.Z-macos --version
```

### 2. Commit Version Bump

```bash
git add pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
git push origin main
```

### 3. Create and Push Tag

```bash
# Create annotated tag
git tag -a vX.Y.Z -m "Release version X.Y.Z"

# Push tag to trigger release workflow
git push origin vX.Y.Z
```

**GitHub Actions will automatically:**
- Build macOS executable
- Create GitHub Release with version notes
- Upload binary and checksum files

### 4. Verify Release

1. Go to: https://github.com/pradeeproark/pensieve/releases
2. Verify release was created with tag `vX.Y.Z`
3. Verify assets are attached:
   - `pensieve-X.Y.Z-macos`
   - `pensieve-X.Y.Z-macos.sha256`
4. Download and test the binary:
   ```bash
   curl -L https://github.com/pradeeproark/pensieve/releases/download/vX.Y.Z/pensieve-X.Y.Z-macos -o pensieve-test
   chmod +x pensieve-test
   ./pensieve-test --version
   ```

### 5. Update Homebrew Formula

**Until automation is implemented, manually update the formula:**

1. Get the SHA256 checksum from the release or locally:
   ```bash
   # From release assets (download .sha256 file)
   curl -L https://github.com/pradeeproark/pensieve/releases/download/vX.Y.Z/pensieve-X.Y.Z-macos.sha256

   # Or calculate from downloaded binary
   shasum -a 256 pensieve-X.Y.Z-macos
   ```

2. Clone/update the Homebrew tap repository:
   ```bash
   cd ~/repos  # or wherever you keep repos
   git clone https://github.com/pradeeproark/homebrew-pensieve.git
   cd homebrew-pensieve
   ```

3. Edit `Formula/pensieve.rb`:
   ```ruby
   class Pensieve < Formula
     desc "Memory recording tool for Claude Code agents"
     homepage "https://github.com/pradeeproark/pensieve"
     version "X.Y.Z"  # ← Update this

     url "https://github.com/pradeeproark/pensieve/releases/download/vX.Y.Z/pensieve-X.Y.Z-macos"  # ← Update this
     sha256 "ACTUAL_SHA256_CHECKSUM_HERE"  # ← Update this

     def install
       bin.install "pensieve-X.Y.Z-macos" => "pensieve"  # ← Update this
     end

     test do
       assert_match "pensieve, version #{version}", shell_output("#{bin}/pensieve --version")
     end
   end
   ```

4. Test the formula locally:
   ```bash
   # Uninstall previous version if installed
   brew uninstall pensieve

   # Install from local formula
   brew install --build-from-source Formula/pensieve.rb

   # Test
   pensieve --version

   # Run formula test
   brew test pensieve
   ```

5. Commit and push the formula update:
   ```bash
   git add Formula/pensieve.rb
   git commit -m "chore: bump to version X.Y.Z"
   git push origin main
   ```

6. Verify users can install:
   ```bash
   brew uninstall pensieve
   brew update
   brew install pensieve
   pensieve --version
   ```

## Hotfix Releases

For urgent bug fixes:

1. Create a branch from the release tag:
   ```bash
   git checkout -b hotfix/X.Y.Z+1 vX.Y.Z
   ```

2. Fix the bug and commit:
   ```bash
   git commit -m "fix: description of urgent fix"
   ```

3. Update version to X.Y.Z+1 in pyproject.toml

4. Merge to main and follow normal release process

## Rollback

If a release has critical issues:

1. Delete the tag and release:
   ```bash
   # Delete local tag
   git tag -d vX.Y.Z

   # Delete remote tag
   git push origin :refs/tags/vX.Y.Z

   # Delete GitHub Release manually from web UI
   ```

2. Fix the issue

3. Create new release with incremented patch version

## Future Automation

**Planned improvements:**
- Automatic Homebrew formula updates via GitHub Actions
- Linux and Windows binary builds
- Changelog generation from commits
- Release notes from git history

## Troubleshooting

### GitHub Actions fails to build

- Check workflow logs: https://github.com/pradeeproark/pensieve/actions
- Common issues:
  - PyInstaller fails: Check dependencies in pyproject.toml
  - Tests fail: Run `pytest` locally first
  - Permission issues: Check GITHUB_TOKEN permissions

### Homebrew install fails

- Test the formula locally first: `brew install --build-from-source Formula/pensieve.rb`
- Verify SHA256 matches: `shasum -a 256 downloaded-binary`
- Check binary is executable: `chmod +x pensieve-X.Y.Z-macos`

### Version mismatch

- Ensure pyproject.toml version matches git tag
- Clear pip cache if testing locally: `pip cache purge`
- Reinstall package: `pip uninstall pensieve && pip install -e .`

## Checklist

Before creating a release, verify:

- [ ] All tests pass: `pytest`
- [ ] Version updated in `pyproject.toml`
- [ ] Changelog updated (if you maintain one)
- [ ] Build works locally: `python build_executable.py`
- [ ] Binary runs: `dist/pensieve-X.Y.Z-macos --version`
- [ ] Committed version bump: `git commit -m "chore: bump version to X.Y.Z"`
- [ ] Created annotated tag: `git tag -a vX.Y.Z -m "Release version X.Y.Z"`
- [ ] Pushed tag: `git push origin vX.Y.Z`
- [ ] GitHub Actions completed successfully
- [ ] Release created on GitHub with assets
- [ ] Downloaded and tested binary from release
- [ ] Updated Homebrew formula
- [ ] Tested Homebrew installation
