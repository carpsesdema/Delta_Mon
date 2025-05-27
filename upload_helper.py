#!/usr/bin/env python3
"""
Simple Upload Helper for DeltaMon
================================

This script makes manual uploading SUPER easy by:
1. Opening the GitHub releases page
2. Showing you exactly what to copy/paste
3. Opening the releases folder

Usage: python upload_helper.py 1.0.7 "New features added"
"""

import sys
import webbrowser
import subprocess
from pathlib import Path


def open_upload_helper(version: str, changelog: str):
    """Open everything you need for manual upload"""

    releases_dir = Path("releases")
    exe_file = releases_dir / f"DeltaMon_v{version}.exe"

    print(f"🚀 DeltaMon Upload Helper for Version {version}")
    print("=" * 60)

    # Check if executable exists
    if not exe_file.exists():
        print(f"❌ Executable not found: {exe_file}")
        print(f"   Run: python build_and_deploy.py --version {version} --changelog \"{changelog}\" --no-github")
        return

    print(f"✅ Executable ready: {exe_file}")
    print(f"📏 Size: {exe_file.stat().st_size / (1024 * 1024):.1f} MB")
    print(f"📦 Includes: Tesseract OCR, Assets, App Icon")
    print()

    # Open GitHub releases page
    github_url = "https://github.com/carpsesdema/Delta_Mon/releases/new"
    print(f"🌐 Opening GitHub releases page...")
    webbrowser.open(github_url)

    # Open releases folder
    print(f"📁 Opening releases folder...")
    if sys.platform == "win32":
        subprocess.run(["explorer", str(releases_dir)], check=False)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(releases_dir)], check=False)
    else:
        subprocess.run(["xdg-open", str(releases_dir)], check=False)

    print()
    print("📋 COPY THIS INFO TO GITHUB:")
    print("=" * 40)
    print(f"Tag version: v{version}")
    print(f"Release title: DeltaMon v{version}")
    print()
    print("Description:")
    print(f"## DeltaMon v{version}")
    print()
    print(f"{changelog}")
    print()
    print("### Features Included:")
    print("- ✅ OptionDelta monitoring")
    print("- ✅ Account auto-discovery")
    print("- ✅ Discord/Telegram alerts")
    print("- ✅ Always-on-top overlay")
    print("- ✅ Bundled OCR (no setup required)")
    print()
    print("### Installation:")
    print("1. Download the .exe file below")
    print("2. Run it - no installation needed!")
    print("3. All dependencies are bundled")
    print()
    print(f"Upload file: {exe_file.name}")
    print()
    print("🎯 STEPS:")
    print("1. Fill in the form with the info above")
    print("2. Drag & drop the .exe file from the opened folder")
    print("3. Click 'Publish release'")
    print("4. Done! Your client will get the update! 🎉")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python upload_helper.py 1.0.7 \"New features added\"")
        print("\nExample:")
        print("  python upload_helper.py 1.0.1 \"Fixed account discovery bug\"")
        print("  python upload_helper.py 1.1.0 \"Added Discord alerts\"")
        sys.exit(1)

    version = sys.argv[1]
    changelog = sys.argv[2]

    open_upload_helper(version, changelog)