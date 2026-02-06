# Windows Setup Guide

Quick guide for setting up the PDF Extractor on Windows.

## Quick Start (Automated)

```powershell
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Run the Windows installer (downloads and configures poppler)
python install_windows_deps.py

# 3. Create configuration file
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the extractor
python main.py presentation.pdf -o output.json
```

## Manual Installation

If the automated installer doesn't work, follow these steps:

### 1. Install Poppler

**Option A: Download Pre-built Binaries**
1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/
2. Download the latest `Release-XX.XX.X-X.zip`
3. Extract to `C:\Program Files\poppler`
4. Add to your `.env` file:
   ```
   POPPLER_PATH=C:\Program Files\poppler\Library\bin
   ```

**Option B: Use Package Manager (Chocolatey)**
```powershell
choco install poppler
```

### 2. Install Tesseract OCR

**Option A: Download Installer**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Get `tesseract-ocr-w64-setup-5.x.x.exe`
3. Run installer
4. **Important:** During installation, select "Arabic" in Additional Language Data
5. If not in PATH, add to `.env`:
   ```
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

**Option B: Use Package Manager (Chocolatey)**
```powershell
choco install tesseract
```

### 3. Verify Installation

```powershell
# Check poppler
pdftoppm -h

# Check tesseract
tesseract --version

# Test system
python validate_system.py
```

## Common Issues

### Issue: "Unable to get page count. Is poppler installed and in PATH?"

**Solution:**
1. Make sure poppler is installed
2. Add `POPPLER_PATH` to your `.env` file:
   ```
   POPPLER_PATH=C:\Program Files\poppler\Library\bin
   ```
3. Or add to Windows PATH:
   - Open System Properties → Environment Variables
   - Edit PATH variable
   - Add: `C:\Program Files\poppler\Library\bin`

### Issue: "pytesseract.pytesseract.TesseractNotFoundError"

**Solution:**
1. Install Tesseract OCR (see above)
2. Add to `.env`:
   ```
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

### Issue: "Arabic text not recognized by OCR"

**Solution:**
1. Reinstall Tesseract and select "Arabic" language data during installation
2. Or download Arabic data separately:
   - Download `ara.traineddata` from: https://github.com/tesseract-ocr/tessdata
   - Place in: `C:\Program Files\Tesseract-OCR\tessdata\`

### Issue: "ModuleNotFoundError: No module named 'pydantic'"

**Solution:**
```powershell
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file with the following:

```ini
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional - only if auto-detection fails
POPPLER_PATH=C:\Program Files\poppler\Library\bin
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Adjust as needed
PDF_RENDER_SCALE=2.5
MAX_PAGES_PER_RUN=20
TESSERACT_LANGUAGES=ara+eng
```

## PowerShell Usage Examples

```powershell
# Basic usage
python main.py presentation.pdf

# Specify output
python main.py deck.pdf -o output.json

# Process first 10 pages only
python main.py large_file.pdf --max-pages 10

# Verbose output for debugging
python main.py problematic.pdf -v

# Higher quality rendering (slower)
python main.py presentation.pdf --scale 3.0
```

## Troubleshooting

### Enable Verbose Logging

```powershell
python main.py presentation.pdf -v
```

This will show detailed information about:
- Configuration loading
- Poppler and Tesseract detection
- PDF rendering process
- Text extraction
- API calls
- Validation checks

### Check System Status

```powershell
python validate_system.py
```

This validates:
- File structure
- Python module imports
- Data model creation
- JSON serialization

### Manual Path Testing

Test poppler manually:
```powershell
& "C:\Program Files\poppler\Library\bin\pdftoppm.exe" -h
```

Test tesseract manually:
```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

## Performance Tips for Windows

1. **Disable Windows Defender for workspace folder** (temporarily during processing)
   - Scanning can slow down PDF rendering significantly

2. **Use SSD for temp files**
   - PDF rendering creates temporary image files

3. **Close background applications**
   - LLM processing is CPU/memory intensive

4. **Use lower scale for testing**
   - Start with `--scale 2.0` for faster processing
   - Increase to `--scale 3.0` for production

## Next Steps

Once everything is installed:

1. **Test with a small PDF:**
   ```powershell
   python main.py small_test.pdf -o test.json -v
   ```

2. **Check the output:**
   ```powershell
   type test.json
   ```

3. **Process your actual presentation:**
   ```powershell
   python main.py presentation.pdf -o results.json
   ```

## Getting Help

If you still encounter issues:

1. Run with verbose flag: `python main.py input.pdf -v`
2. Check the error message carefully
3. Verify all paths in `.env` are correct
4. Make sure all dependencies are installed
5. Try the automated installer: `python install_windows_deps.py`

## Alternative: Use WSL (Windows Subsystem for Linux)

If you continue having issues with Windows, consider using WSL:

```powershell
# Install WSL
wsl --install

# Inside WSL (Ubuntu)
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-ara
pip install -r requirements.txt
python main.py presentation.pdf
```

This gives you the Linux experience on Windows without dual-booting.
