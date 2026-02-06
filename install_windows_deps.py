#!/usr/bin/env python3
"""
Windows dependency installer for PDF Extractor.
Downloads and installs poppler and tesseract on Windows.
"""
import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def check_admin():
    """Check if running with admin privileges."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def download_file(url, dest_path):
    """Download a file with progress."""
    print(f"Downloading: {url}")
    print(f"Destination: {dest_path}")
    
    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100 / total_size, 100)
            print(f"\rProgress: {percent:.1f}%", end='')
    
    urllib.request.urlretrieve(url, dest_path, progress)
    print("\n✓ Download complete")


def install_poppler():
    """Install poppler on Windows."""
    print_header("Installing Poppler")
    
    # Check if already installed
    poppler_path = Path("C:/Program Files/poppler")
    if poppler_path.exists():
        print("⚠ Poppler already exists at C:/Program Files/poppler")
        response = input("Reinstall? (y/n): ").lower()
        if response != 'y':
            print("Skipping poppler installation")
            return True
    
    # Download poppler
    print("Downloading poppler for Windows...")
    poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
    download_path = Path("poppler.zip")
    
    try:
        download_file(poppler_url, download_path)
    except Exception as e:
        print(f"✗ Download failed: {e}")
        print("\nManual installation required:")
        print("1. Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("2. Extract to C:\\Program Files\\poppler")
        print("3. Add C:\\Program Files\\poppler\\Library\\bin to PATH")
        return False
    
    # Extract
    print("\nExtracting poppler...")
    try:
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            extract_path = Path("poppler_temp")
            zip_ref.extractall(extract_path)
        
        # Move to Program Files
        if not check_admin():
            print("\n⚠ Administrator privileges required to install to Program Files")
            print("Moving to local directory instead...")
            dest_path = Path.home() / "poppler"
        else:
            dest_path = Path("C:/Program Files/poppler")
        
        # Find the extracted folder
        extracted_folders = list(extract_path.glob("poppler-*"))
        if extracted_folders:
            source = extracted_folders[0]
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.move(str(source), str(dest_path))
            print(f"✓ Poppler installed to: {dest_path}")
        
        # Cleanup
        download_path.unlink()
        shutil.rmtree(extract_path)
        
        # Add to PATH
        bin_path = dest_path / "Library" / "bin"
        print(f"\n✓ Poppler binaries location: {bin_path}")
        print("\nIMPORTANT: Add this to your PATH:")
        print(f"  {bin_path}")
        print("\nOr set in .env file:")
        print(f"  POPPLER_PATH={bin_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Installation failed: {e}")
        return False


def check_tesseract():
    """Check if tesseract is installed."""
    print_header("Checking Tesseract OCR")
    
    # Common installation paths
    common_paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
        Path.home() / "AppData/Local/Programs/Tesseract-OCR/tesseract.exe"
    ]
    
    # Check PATH
    try:
        result = subprocess.run(["tesseract", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Tesseract found in PATH")
            print(f"  Version: {result.stdout.split()[1]}")
            return True
    except:
        pass
    
    # Check common paths
    for path in common_paths:
        if path.exists():
            print(f"✓ Tesseract found at: {path}")
            print(f"\nAdd to .env file:")
            print(f"  TESSERACT_CMD={path}")
            return True
    
    print("✗ Tesseract not found")
    print("\nTo install Tesseract:")
    print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. Run installer (tesseract-ocr-w64-setup-5.x.x.exe)")
    print("3. During installation, select 'Arabic' language data")
    print("4. Add to PATH or set TESSERACT_CMD in .env")
    
    return False


def update_env_file():
    """Update .env file with Windows-specific settings."""
    print_header("Updating Configuration")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✓ Created .env from .env.example")
        else:
            env_file.write_text("# PDF Extractor Configuration\n")
            print("✓ Created .env file")
    
    # Check for poppler path
    poppler_paths = [
        Path("C:/Program Files/poppler/Library/bin"),
        Path.home() / "poppler/Library/bin"
    ]
    
    poppler_bin = None
    for path in poppler_paths:
        if path.exists():
            poppler_bin = path
            break
    
    if poppler_bin:
        env_content = env_file.read_text()
        if "POPPLER_PATH" not in env_content:
            env_file.write_text(env_content + f"\nPOPPLER_PATH={poppler_bin}\n")
            print(f"✓ Added POPPLER_PATH to .env: {poppler_bin}")
    
    print("\n⚠ Don't forget to add your OPENAI_API_KEY to .env!")


def main():
    """Main installation routine."""
    print_header("Windows Dependency Installer for PDF Extractor")
    
    if sys.platform != "win32":
        print("This installer is for Windows only.")
        print("For Linux/Mac, see README.md for installation instructions.")
        sys.exit(1)
    
    print("This script will help you install required dependencies:")
    print("  - Poppler (PDF rendering)")
    print("  - Tesseract OCR (text extraction)")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    # Install poppler
    poppler_ok = install_poppler()
    
    # Check tesseract
    tesseract_ok = check_tesseract()
    
    # Update .env
    update_env_file()
    
    # Summary
    print_header("Installation Summary")
    
    print(f"Poppler:    {'✓ Installed' if poppler_ok else '✗ Manual installation required'}")
    print(f"Tesseract:  {'✓ Found' if tesseract_ok else '✗ Manual installation required'}")
    
    if poppler_ok and tesseract_ok:
        print("\n✓ All dependencies installed!")
        print("\nNext steps:")
        print("1. Add your OPENAI_API_KEY to .env")
        print("2. Run: python main.py presentation.pdf")
    else:
        print("\n⚠ Some dependencies need manual installation.")
        print("See instructions above and README.md for details.")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Installation failed: {e}")
        sys.exit(1)
