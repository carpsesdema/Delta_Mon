# DeltaMon Build & Update System 🚀

This document explains how to use the automated build and update system for DeltaMon.

## Quick Start

### 1. Set Environment Variables
```bash
# Set your GitHub token and repo
setx GITHUB_TOKEN3 "your_github_token_here"
setx GITHUB_REPO3 "carpsesdema/Delta_Mon"
```

### 2. Build and Deploy
```bash
# Build and deploy version 1.0.1
python build_and_deploy.py --version 1.0.1 --changelog "Fixed account discovery bug"
```

### 3. Manual Upload (if GitHub fails)
```bash
# Helper for manual upload
python upload_helper.py 1.0.1 "Fixed account discovery bug"
```

## Files Overview

| File | Purpose |
|------|---------|
| `build_and_deploy.py` | Main build script - creates executable and GitHub release |
| `upload_helper.py` | Manual upload helper - opens GitHub and gives instructions |
| `utils/auto_updater.py` | Auto-updater component for the main app |
| `main.py` | Updated main file with auto-updater integration |

## Prerequisites

### Required Software
- **Python 3.8+** with packages: `PyInstaller`, `requests`, `PySide6`
- **Git** (for tagging releases)
- **Tesseract OCR** bundled in `tesseract/` folder

### Required Files
```
Delta_Mon/
├── main.py                 # Main application file
├── app_icon.ico           # Application icon
├── tesseract/             # Bundled Tesseract OCR
│   ├── tesseract.exe      
│   ├── tessdata/
│   │   └── eng.traineddata
│   └── (other files)
├── assets/                # Assets folder (optional)
├── build_and_deploy.py    # Build script
└── upload_helper.py       # Upload helper
```

## GitHub Setup

### 1. Create Personal Access Token
1. Go to [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a name like "DeltaMon Build Token"
4. Select scope: **`repo`** (Full control of private repositories)
5. Copy the token and set environment variable:
   ```bash
   setx GITHUB_TOKEN3 "ghp_your_token_here"
   ```

### 2. Set Repository
```bash
setx GITHUB_REPO3 "carpsesdema/Delta_Mon"
```

## Build Process

### Automatic Build & Deploy
```bash
# Build version 1.2.0 and deploy to GitHub
python build_and_deploy.py --version 1.2.0 --changelog "Added Discord alerts and improved UI"
```

**What this does:**
1. ✅ Cleans build directories
2. ✅ Updates version in `main.py`
3. ✅ Builds executable with PyInstaller (includes Tesseract + assets)
4. ✅ Creates `releases/DeltaMon_v1.2.0.exe`
5. ✅ Creates Git tag `v1.2.0`
6. ✅ Creates GitHub release
7. ✅ Uploads executable to GitHub
8. ✅ Creates update info JSON

### Build Only (No GitHub)
```bash
# Build executable but don't deploy to GitHub
python build_and_deploy.py --version 1.2.0 --changelog "Added Discord alerts" --no-github
```

### Manual Upload
If GitHub deployment fails, use the upload helper:
```bash
python upload_helper.py 1.2.0 "Added Discord alerts and improved UI"
```

This will:
- ✅ Open GitHub releases page
- ✅ Open releases folder
- ✅ Show you exactly what to copy/paste

## Version Management

### Update Version in Code
The build script automatically updates the version in `main.py`. 

**Add this line to your `main.py`:**
```python
VERSION = "1.0.0"  # This gets updated automatically
```

### Version Format
Use semantic versioning: `MAJOR.MINOR.PATCH`
- `1.0.0` → `1.0.1` (patch - bug fixes)
- `1.0.1` → `1.1.0` (minor - new features)
- `1.1.0` → `2.0.0` (major - breaking changes)

## Auto-Updater Integration

### 1. Add to main.py
```python
from utils.auto_updater import AutoUpdater

VERSION = "1.0.0"  # Your current version

# In your main function:
updater = AutoUpdater(VERSION, main_window)
updater.start_periodic_checks()  # Check for updates daily
```

### 2. Add Update Menu/Button
The auto-updater can add:
- Menu item: "Help > Check for Updates"
- Button in your UI
- Automatic background checks

### 3. User Experience
- ✅ Checks for updates daily
- ✅ Shows changelog and download size
- ✅ One-click download from GitHub
- ✅ Preserves user settings

## Build Output

### Files Created
```
releases/
├── DeltaMon_v1.2.0.exe     # Main executable (bundled with everything)
└── update_info_v1.2.0.json # Update metadata
```

### Executable Includes
- ✅ All Python code
- ✅ PySide6 GUI framework
- ✅ OpenCV for image processing
- ✅ Tesseract OCR (complete bundle)
- ✅ All assets and icons
- ✅ Dependencies (no installation needed)

## Troubleshooting

### Build Fails
```bash
# Make sure you have all dependencies
pip install PyInstaller requests PySide6

# Check if tesseract/ folder exists and is complete
dir tesseract
dir tesseract\tessdata
```

### GitHub Deployment Fails
1. **Check token permissions:** Must have `repo` scope
2. **Check environment variables:**
   ```bash
   echo %GITHUB_TOKEN3%
   echo %GITHUB_REPO3%
   ```
3. **Use manual upload:**
   ```bash
   python upload_helper.py 1.0.1 "Your changelog"
   ```

### Auto-Updater Issues
- **No update notifications:** Check internet connection
- **Download fails:** GitHub releases may be private
- **Version not detected:** Ensure VERSION variable is set in main.py

## Distribution

### For Your Client
1. Build with: `python build_and_deploy.py --version 1.0.0 --changelog "Initial release"`
2. Send them: `releases/DeltaMon_v1.0.0.exe`
3. They run it - no installation needed!
4. Future updates are automatic

### File Size
Typical executable size: **~150-200 MB**
- Includes complete Tesseract OCR
- All Python dependencies
- GUI framework
- Worth it for zero-setup experience!

## Examples

### Release Examples
```bash
# Bug fix release
python build_and_deploy.py --version 1.0.1 --changelog "Fixed account dropdown detection issue"

# Feature release
python build_and_deploy.py --version 1.1.0 --changelog "Added Telegram alerts, improved overlay UI, faster account discovery"

# Major release
python build_and_deploy.py --version 2.0.0 --changelog "Complete UI redesign, new OptionDelta algorithm, multi-monitor support"

# Emergency fix (manual upload)
python build_and_deploy.py --version 1.0.2 --changelog "Critical fix for Windows 11" --no-github
python upload_helper.py 1.0.2 "Critical fix for Windows 11"
```

## Best Practices

### Before Building
1. ✅ Test the application thoroughly
2. ✅ Update changelog with clear descriptions
3. ✅ Increment version number appropriately
4. ✅ Commit your code changes first

### Changelog Tips
- ✅ Be specific: "Fixed account dropdown not opening on some systems"
- ✅ Highlight benefits: "50% faster account discovery"
- ✅ Group changes: Bug fixes, new features, improvements
- ❌ Don't be vague: "Various improvements"

### Version Strategy
- **Patch (1.0.1):** Bug fixes, minor tweaks
- **Minor (1.1.0):** New features, significant improvements
- **Major (2.0.0):** Breaking changes, complete rewrites

---

## 🎉 You're All Set!

Your DeltaMon now has:
- ✅ Automated building and deployment
- ✅ GitHub releases with changelogs  
- ✅ Automatic client updates
- ✅ Zero-setup distribution
- ✅ Professional update experience

Happy building! 🚀