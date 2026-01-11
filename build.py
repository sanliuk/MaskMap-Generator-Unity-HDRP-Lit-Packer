#!/usr/bin/env python3
"""
Build script for MaskMap Generator
Creates standalone executables for Windows and macOS
"""

import subprocess
import sys
import os
import shutil

APP_NAME = "MaskMapGenerator"
MAIN_SCRIPT = "MaskMapHDRP.py"
ICON_PATH = None  # Set to icon path if you have one, e.g., "icon.ico"

def build():
    """Build the executable using PyInstaller"""

    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",           # Single executable file
        "--windowed",          # No console window (GUI app)
        "--clean",             # Clean cache before building
        "--noconfirm",         # Replace output without asking
    ]

    # Add icon if available
    if ICON_PATH and os.path.exists(ICON_PATH):
        cmd.extend(["--icon", ICON_PATH])

    # Hidden imports for tkinterdnd2
    cmd.extend([
        "--hidden-import", "tkinterdnd2",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageTk",
        "--hidden-import", "PIL.ImageOps",
    ])

    # Collect tkinterdnd2 data files
    cmd.extend([
        "--collect-all", "tkinterdnd2",
    ])

    # Add main script
    cmd.append(MAIN_SCRIPT)

    print("=" * 50)
    print(f"Building {APP_NAME}...")
    print("=" * 50)
    print(f"Command: {' '.join(cmd)}")
    print()

    # Run PyInstaller
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print()
        print("=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)

        # Determine output path
        if sys.platform == "win32":
            exe_name = f"{APP_NAME}.exe"
        else:
            exe_name = APP_NAME

        dist_path = os.path.join("dist", exe_name)

        if os.path.exists(dist_path):
            size_mb = os.path.getsize(dist_path) / (1024 * 1024)
            print(f"Executable: {dist_path}")
            print(f"Size: {size_mb:.1f} MB")

        print()
        print("You can find your executable in the 'dist' folder.")
    else:
        print()
        print("BUILD FAILED!")
        print("Check the error messages above.")
        sys.exit(1)

def clean():
    """Clean build artifacts"""
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = [f"{APP_NAME}.spec"]

    for d in dirs_to_remove:
        if os.path.exists(d):
            print(f"Removing {d}/")
            shutil.rmtree(d)

    for f in files_to_remove:
        if os.path.exists(f):
            print(f"Removing {f}")
            os.remove(f)

    print("Clean complete!")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean()
    else:
        build()
