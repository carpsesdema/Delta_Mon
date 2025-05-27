#!/usr/bin/env python3
"""
DeltaMon - Complete Build and Deployment Script
==============================================

This script handles:
1. Building the executable with PyInstaller (including Tesseract bundle)
2. Creating GitHub releases
3. Uploading the executable
4. Managing version updates

Usage:
    python build_and_deploy.py --version 1.0.1 --changelog "Bug fixes and improvements"
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

import requests


class BuildError(Exception):
    """Custom exception for build-related errors"""
    pass


class DeploymentError(Exception):
    """Custom exception for deployment-related errors"""
    pass


class DeltaMonBuilder:
    """Handles building and deploying the DeltaMon application"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.releases_dir = self.project_root / "releases"

        # GitHub configuration - Using your specific environment variables!
        self.github_token = os.getenv('GITHUB_TOKEN3')
        self.github_repo = os.getenv('GITHUB_REPO3', 'carpsesdema/Delta_Mon')

        # Application details
        self.app_name = "DeltaMon"
        self.main_script = "main.py"
        self.icon_file = "assets/app_icon.ico"

        print(f"🚀 DeltaMon Builder")
        print(f"📁 Project root: {self.project_root}")
        print(f"📦 Target repo: {self.github_repo}")

    def clean_build_dirs(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning build directories...")

        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Cleaned: {dir_path}")

        # Create releases directory
        self.releases_dir.mkdir(exist_ok=True)
        print("✅ Build directories cleaned")

    def update_version_in_code(self, version: str):
        """Update the version number in the main script"""
        print(f"📝 Updating version to {version}...")

        main_file = self.project_root / self.main_script
        if not main_file.exists():
            raise BuildError(f"Main script not found: {main_file}")

        # Read the file
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace the version - look for common patterns
        import re
        patterns = [
            (r'VERSION = "[^"]*"', f'VERSION = "{version}"'),
            (r'CURRENT_VERSION = "[^"]*"', f'CURRENT_VERSION = "{version}"'),
            (r'APP_VERSION = "[^"]*"', f'APP_VERSION = "{version}"'),
            (r'__version__ = "[^"]*"', f'__version__ = "{version}"'),
        ]

        updated = False
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updated = True
                break

        if updated:
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Version updated to {version}")
        else:
            print("⚠️  Warning: Could not find version pattern in main script")
            print("   You might need to manually add: VERSION = \"1.0.0\" to your main.py")

    def check_tesseract_bundle(self):
        """Check if Tesseract is bundled and ready"""
        tesseract_dir = self.project_root / "tesseract"
        tesseract_exe = tesseract_dir / "tesseract.exe"
        tessdata_dir = tesseract_dir / "tessdata"

        if not tesseract_dir.exists():
            raise BuildError("❌ Tesseract folder not found! You need to bundle Tesseract first.")

        if not tesseract_exe.exists():
            raise BuildError("❌ tesseract.exe not found in tesseract/ folder!")

        if not tessdata_dir.exists():
            raise BuildError("❌ tessdata/ folder not found in tesseract/ folder!")

        eng_data = tessdata_dir / "eng.traineddata"
        if not eng_data.exists():
            raise BuildError("❌ eng.traineddata not found in tesseract/tessdata/ folder!")

        print("✅ Tesseract bundle verified - ready for inclusion")
        return True

    def build_executable(self, version: str) -> Path:
        """Build the executable using PyInstaller"""
        print("🔨 Building DeltaMon executable...")

        # Check Tesseract bundle first
        self.check_tesseract_bundle()

        exe_name = f"{self.app_name}_v{version}"

        # Check if PyInstaller is available
        try:
            import PyInstaller
        except ImportError:
            raise BuildError("PyInstaller is not installed. Run: pip install pyinstaller")

        # ENSURE WE'RE IN THE PROJECT ROOT
        original_cwd = os.getcwd()
        os.chdir(str(self.project_root))

        try:
            # Check for icon file
            icon_path = self.project_root / self.icon_file
            if not icon_path.exists():
                print(f"⚠️  Warning: Icon file not found: {icon_path}")
                icon_path = None

            # PyInstaller command
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--windowed",
                "--name", exe_name,
                "--distpath", str(self.dist_dir),
                "--workpath", str(self.build_dir),
                "--specpath", str(self.build_dir),
                "--clean",
                "--noconsole",
            ]

            # Add icon if available
            if icon_path:
                cmd.extend(["--icon", str(icon_path)])
                print(f"   Using icon: {icon_path}")

            # Add data files - Use ABSOLUTE PATHS
            tesseract_source = self.project_root / "tesseract"
            if tesseract_source.exists():
                cmd.extend(["--add-data", f"{tesseract_source}{os.pathsep}tesseract"])
                print(f"   Including Tesseract from: {tesseract_source}")
            else:
                raise BuildError(f"Tesseract folder not found at: {tesseract_source}")

            # Add assets folder if it exists
            assets_source = self.project_root / "assets"
            if assets_source.exists():
                cmd.extend(["--add-data", f"{assets_source}{os.pathsep}assets"])
                print(f"   Including assets from: {assets_source}")

            # Hidden imports for DeltaMon
            hidden_imports = [
                "PySide6.QtCore",
                "PySide6.QtWidgets",
                "PySide6.QtGui",
                "cv2",
                "numpy",
                "pyautogui",
                "pywin32",
                "win32gui",
                "win32con",
                "win32api",
                "pytesseract",
                "requests",
                "configparser",
                "keyring",
                "cryptography",
            ]

            for imp in hidden_imports:
                cmd.extend(["--hidden-import", imp])

            # Add the main script
            main_file = self.project_root / self.main_script
            if not main_file.exists():
                raise BuildError(f"Main script not found: {main_file}")

            cmd.append(str(main_file))

            print(f"   Building executable with bundled Tesseract...")
            print(f"   This may take a few minutes...")

            # DEBUG: Print the actual command being run
            print(f"   Command: {' '.join(cmd)}")

            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            exe_path = self.dist_dir / f"{exe_name}.exe"
            if exe_path.exists():
                # Move to releases directory
                final_path = self.releases_dir / f"{self.app_name}_v{version}.exe"
                shutil.move(str(exe_path), str(final_path))

                file_size = final_path.stat().st_size / (1024 * 1024)  # MB
                print(f"✅ Build completed successfully!")
                print(f"   📦 Executable: {final_path}")
                print(f"   📏 Size: {file_size:.1f} MB")
                print(f"   📁 Includes: Tesseract OCR, Assets, App Icon")
                return final_path
            else:
                raise BuildError("Executable not found after build")

        except subprocess.CalledProcessError as e:
            print(f"❌ PyInstaller failed:")
            print(f"   Output: {e.stdout}")
            print(f"   Error: {e.stderr}")
            raise BuildError(f"PyInstaller failed: {e}")

        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def create_release_info(self, version: str, changelog: str, exe_path: Path) -> dict:
        """Create release information JSON"""
        release_info = {
            "version": version,
            "build_date": datetime.now().isoformat(),
            "changelog": changelog,
            "critical": False,  # Set to True for critical updates
            "min_version": "1.0.0",  # Minimum supported version
            "file_name": exe_path.name,
            "file_size": exe_path.stat().st_size,
            "download_url": f"https://github.com/{self.github_repo}/releases/download/v{version}/{exe_path.name}",
            "features": [
                "OptionDelta monitoring",
                "Account auto-discovery",
                "Discord/Telegram alerts",
                "Always-on-top overlay",
                "Bundled OCR (no setup required)"
            ]
        }

        # Save release info
        info_file = self.releases_dir / f"update_info_v{version}.json"

        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(release_info, f, indent=2)

        print(f"📋 Release info saved: {info_file}")
        return release_info

    def create_git_tag(self, version: str) -> bool:
        """Create and push git tag"""
        try:
            print(f"📝 Creating git tag v{version}...")

            # Create tag locally
            result = subprocess.run(['git', 'tag', f'v{version}'],
                                    capture_output=True, text=True, check=False)

            if result.returncode != 0 and "already exists" not in result.stderr:
                print(f"   Warning: Could not create tag locally: {result.stderr}")

            # Push tag to GitHub
            result = subprocess.run(['git', 'push', 'origin', f'v{version}'],
                                    capture_output=True, text=True, check=False)

            if result.returncode == 0:
                print(f"✅ Git tag v{version} created and pushed")
                return True
            else:
                print(f"   Warning: Could not push tag: {result.stderr}")
                return True  # Continue anyway, tag might already exist

        except Exception as e:
            print(f"   Warning: Git tag creation failed: {e}")
            return True  # Continue anyway

    def create_github_release(self, version: str, changelog: str, exe_path: Path) -> bool:
        """Create a GitHub release and upload the executable"""
        if not self.github_token:
            print("⚠️  GITHUB_TOKEN3 not found in environment variables")
            print("   To set up automatic GitHub releases:")
            print("   1. Go to GitHub Settings > Developer settings > Personal access tokens")
            print("   2. Create a token with 'repo' permissions")
            print("   3. Set environment variable: setx GITHUB_TOKEN3 your_token_here")
            print("   4. Also set: setx GITHUB_REPO3 carpsesdema/Delta_Mon")
            print("")
            print("   For now, you can manually upload the executable to GitHub releases")
            return False

        # Create git tag first
        self.create_git_tag(version)

        print("🚀 Creating GitHub release...")

        # Release data
        release_data = {
            "tag_name": f"v{version}",
            "target_commitish": "main",
            "name": f"DeltaMon v{version}",
            "body": f"## DeltaMon v{version}\n\n{changelog}\n\n### Features Included:\n- ✅ OptionDelta monitoring\n- ✅ Account auto-discovery\n- ✅ Discord/Telegram alerts\n- ✅ Always-on-top overlay\n- ✅ Bundled OCR (no setup required)\n\n### Installation:\n1. Download the .exe file below\n2. Run it - no installation needed!\n3. All dependencies are bundled",
            "draft": False,
            "prerelease": False
        }

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DeltaMon-Builder"
        }

        try:
            # Create the release
            print(f"   Creating release for {self.github_repo}...")
            response = requests.post(
                f"https://api.github.com/repos/{self.github_repo}/releases",
                headers=headers,
                json=release_data,
                timeout=30
            )

            if response.status_code == 201:
                release_info = response.json()
                print(f"✅ GitHub release created!")
                print(f"   🔗 URL: {release_info['html_url']}")

                # Upload the executable
                return self._upload_asset_to_release(release_info, exe_path, headers)
            else:
                print(f"❌ Failed to create GitHub release:")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ GitHub API error: {e}")
            return False

    def _upload_asset_to_release(self, release_info: dict, exe_path: Path, headers: dict) -> bool:
        """Upload executable to GitHub release"""
        print("📤 Uploading DeltaMon executable to GitHub...")

        upload_url = release_info['upload_url'].replace('{?name,label}', '')

        try:
            with open(exe_path, 'rb') as f:
                upload_headers = headers.copy()
                upload_headers['Content-Type'] = 'application/octet-stream'

                print(f"   Uploading {exe_path.name} ({exe_path.stat().st_size / (1024 * 1024):.1f} MB)...")

                upload_response = requests.post(
                    f"{upload_url}?name={exe_path.name}",
                    headers=upload_headers,
                    data=f.read(),
                    timeout=600  # 10 minutes for large files with Tesseract
                )

            if upload_response.status_code == 201:
                asset_info = upload_response.json()
                print("✅ Executable uploaded successfully!")
                print(f"   📦 Download URL: {asset_info['browser_download_url']}")
                return True
            else:
                print(f"❌ Failed to upload executable:")
                print(f"   Status: {upload_response.status_code}")
                print(f"   Response: {upload_response.text}")
                return False

        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False

    def build_and_deploy(self, version: str, changelog: str, deploy_to_github: bool = True) -> bool:
        """Complete build and deploy process"""
        print(f"🚀 Starting DeltaMon build and deploy process for version {version}")
        print("=" * 70)

        try:
            # Step 1: Clean build directories
            self.clean_build_dirs()

            # Step 2: Update version in code
            self.update_version_in_code(version)

            # Step 3: Build executable (includes Tesseract bundle)
            exe_path = self.build_executable(version)

            # Step 4: Create update info
            self.create_release_info(version, changelog, exe_path)

            # Step 5: Deploy to GitHub (optional)
            if deploy_to_github:
                success = self.create_github_release(version, changelog, exe_path)
                if success:
                    print("")
                    print("🎉 DELTAMONT DEPLOYMENT COMPLETED SUCCESSFULLY!")
                    print(f"   📱 Your client will automatically be notified of version {version}")
                    print(f"   📥 They can update with one click!")
                    print(f"   🔗 Release: https://github.com/{self.github_repo}/releases/tag/v{version}")
                    return True
                else:
                    print("")
                    print("⚠️  GitHub deployment failed, but executable is ready")
                    print(f"   📦 Executable location: {exe_path}")
                    print("   You can manually upload it to GitHub releases")
                    return False
            else:
                print("")
                print("📦 Build completed. Executable ready for manual deployment.")
                print(f"   📦 Location: {exe_path}")
                return True

        except Exception as e:
            print(f"❌ BUILD FAILED: {e}")
            import traceback
            print(f"   Full error: {traceback.format_exc()}")
            return False


def validate_version(version: str) -> bool:
    """Validate version format"""
    import re
    return bool(re.match(r'^\d+\.\d+\.\d+$', version))


def main():
    parser = argparse.ArgumentParser(
        description='Build and deploy DeltaMon updates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_and_deploy.py --version 1.0.1 --changelog "Bug fixes and improvements"
  python build_and_deploy.py --version 1.2.0 --changelog "Added new features" --no-github

Environment Variables:
  GITHUB_TOKEN3   Your GitHub personal access token
  GITHUB_REPO3    Your repository name (carpsesdema/Delta_Mon)
        """
    )

    parser.add_argument('--version', required=True,
                        help='Version number (e.g., 1.0.1)')
    parser.add_argument('--changelog', required=True,
                        help='Changelog description')
    parser.add_argument('--no-github', action='store_true',
                        help='Skip GitHub deployment')

    args = parser.parse_args()

    # Validate version format
    if not validate_version(args.version):
        print("❌ Version must be in format X.Y.Z (e.g., 1.0.1)")
        sys.exit(1)

    # Check for required files
    if not Path('main.py').exists():
        print("❌ main.py not found in current directory")
        print("   Make sure you're running this script from your project root")
        sys.exit(1)

    if not Path('tesseract').exists():
        print("❌ tesseract/ folder not found!")
        print("   Make sure you have bundled Tesseract in your project")
        print("   See: https://github.com/carpsesdema/Delta_Mon/blob/main/README.md")
        sys.exit(1)

    builder = DeltaMonBuilder()

    success = builder.build_and_deploy(
        version=args.version,
        changelog=args.changelog,
        deploy_to_github=not args.no_github
    )

    if success:
        print("\n🎉 SUCCESS! Your DeltaMon update system is ready!")
        sys.exit(0)
    else:
        print("\n❌ FAILED! Check the output above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()