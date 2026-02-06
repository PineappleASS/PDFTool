# Quick Fix for Your Windows Error

You're seeing: `Unable to get page count. Is poppler installed and in PATH?`

## Solution 1: Automated Installer (Recommended)

```powershell
python install_windows_deps.py
```

This will download and install poppler automatically.

## Solution 2: Manual Install (Fast)

1. **Download Poppler:**
   - Go to: https://github.com/oschwartz10612/poppler-windows/releases/
   - Download: `Release-23.11.0-0.zip` (or latest version)
   
2. **Extract:**
   - Extract the ZIP file
   - Move the `poppler-23.11.0` folder to: `C:\Program Files\poppler`

3. **Configure:**
   - Create/edit `.env` file in your project folder
   - Add this line:
     ```
     POPPLER_PATH=C:\Program Files\poppler\Library\bin
     ```

4. **Add your OpenAI API key to `.env`:**
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

5. **Try again:**
   ```powershell
   python main.py presentation.pdf -o output.json
   ```

## Solution 3: Quick Test (Alternative Path)

If you extract poppler to your Downloads folder:

1. Extract poppler to: `C:\Users\nawaf\Downloads\poppler`
2. In `.env` add:
   ```
   POPPLER_PATH=C:\Users\nawaf\Downloads\poppler\Library\bin
   ```

## Verify It Works

After installation, test it:

```powershell
# This should show poppler help
C:\Program Files\poppler\Library\bin\pdftoppm.exe -h
```

## Still Having Issues?

Run the verbose mode to see exactly what's happening:

```powershell
python main.py presentation.pdf -v
```

Or check the full setup guide:
```powershell
type WINDOWS_SETUP.md
```
