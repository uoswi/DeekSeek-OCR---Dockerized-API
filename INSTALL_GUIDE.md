# Installation Guide for DeepSeek_OCR_pdf_to_md.py

## Quick Install (macOS/Linux/Windows)

### Step 1: Install Python Dependencies

Open Terminal (macOS/Linux) or Command Prompt (Windows) and run:

```bash
pip3 install PyMuPDF Pillow torch
```

Or use the requirements file:

```bash
pip3 install -r requirements_pdf_to_md.txt
```

### Step 2: Install DeepSeek OCR Dependencies (Optional)

**Only needed if running the model locally** (not using the API endpoint):

```bash
pip3 install vllm transformers
```

For flash-attention support (optional, speeds up inference):

```bash
pip3 install flash-attn
```

## Platform-Specific Instructions

### macOS

```bash
# Install Python 3 if not already installed
brew install python3

# Install dependencies
pip3 install PyMuPDF Pillow torch

# For M1/M2/M3 Macs, use MPS (Metal Performance Shaders) backend
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

### Windows

```bash
# Open Command Prompt or PowerShell

# Install dependencies
pip install PyMuPDF Pillow torch

# Force UTF-8 mode (recommended)
set PYTHONUTF8=1
```

### Linux

```bash
# Install dependencies
pip3 install PyMuPDF Pillow torch

# For CUDA support (if you have NVIDIA GPU)
pip3 install torch --index-url https://download.pytorch.org/whl/cu118
```

## Verify Installation

Create a test script to verify all modules are installed:

```python
# test_imports.py
try:
    import fitz
    print("[OK] PyMuPDF (fitz) installed")
except ImportError:
    print("[X] PyMuPDF (fitz) NOT installed - run: pip3 install PyMuPDF")

try:
    from PIL import Image
    print("[OK] Pillow (PIL) installed")
except ImportError:
    print("[X] Pillow NOT installed - run: pip3 install Pillow")

try:
    import torch
    print(f"[OK] PyTorch installed (version {torch.__version__})")
except ImportError:
    print("[X] PyTorch NOT installed - run: pip3 install torch")

print("\nAll required dependencies are installed!")
```

Run it:
```bash
python3 test_imports.py
```

## Usage After Installation

Once dependencies are installed, you can run the script:

```bash
# macOS/Linux
python3 DeepSeek_OCR_pdf_to_md.py --input /path/to/your/document.pdf

# Windows
python DeepSeek_OCR_pdf_to_md.py --input C:\path\to\document.pdf
```

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'fitz'`
**Solution:**
```bash
pip3 install PyMuPDF
```

### Issue: `ModuleNotFoundError: No module named 'PIL'`
**Solution:**
```bash
pip3 install Pillow
```

### Issue: `ModuleNotFoundError: No module named 'torch'`
**Solution:**
```bash
pip3 install torch
```

### Issue: Using `pip` vs `pip3`
If you have both Python 2 and Python 3 installed, use `pip3`:
```bash
pip3 install PyMuPDF Pillow torch
```

If you only have Python 3, you can use either:
```bash
pip install PyMuPDF Pillow torch
```

### Issue: Permission denied
Try installing with `--user` flag:
```bash
pip3 install --user PyMuPDF Pillow torch
```

Or use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install PyMuPDF Pillow torch
```

## Virtual Environment (Recommended)

Using a virtual environment keeps your dependencies isolated:

### macOS/Linux
```bash
# Create virtual environment
python3 -m venv deepseek_env

# Activate it
source deepseek_env/bin/activate

# Install dependencies
pip install PyMuPDF Pillow torch

# Run the script
python DeepSeek_OCR_pdf_to_md.py --input document.pdf

# When done, deactivate
deactivate
```

### Windows
```bash
# Create virtual environment
python -m venv deepseek_env

# Activate it
deepseek_env\Scripts\activate

# Install dependencies
pip install PyMuPDF Pillow torch

# Run the script
python DeepSeek_OCR_pdf_to_md.py --input document.pdf

# When done, deactivate
deactivate
```

## Minimal Installation (API Mode Only)

If you're using the script to call a remote API (not running the model locally), you only need:

```bash
pip3 install PyMuPDF Pillow torch
```

This gives you PDF processing, image handling, and basic PyTorch support.

## Full Installation (Local Model)

If you want to run the DeepSeek OCR model locally:

```bash
pip3 install PyMuPDF Pillow torch vllm transformers flash-attn
```

**Note:** This requires significant GPU resources (8GB+ VRAM recommended).

## Checking Your Installation

After installation, verify everything works:

```bash
python3 -c "import fitz; from PIL import Image; import torch; print('All dependencies OK!')"
```

If this runs without errors, you're ready to use the script!
