# DeepSeek OCR PDF to Markdown - Windows Compatible

A Windows-friendly Python script to convert PDF files to Markdown format using DeepSeek OCR.

## Problem Solved

This script fixes the common Windows Unicode encoding error:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' in position 0: character maps to <undefined>
```

## Features

- Full Windows compatibility with proper UTF-8 encoding
- Converts PDF documents to clean Markdown format
- Extracts and saves embedded images
- Automatic content cleaning (remove OCR markers)
- Support for custom OCR prompts
- High-quality image conversion with configurable DPI
- Both raw and cleaned output options

## Requirements

```bash
pip install torch vllm PyMuPDF Pillow
pip install deepseek-ocr
```

## Quick Start

### Basic Usage

```bash
python DeepSeek_OCR_pdf_to_md.py --input document.pdf
```

This will:
- Convert `document.pdf` to Markdown
- Save output to `./output/document_cleaned.md`
- Extract images to `./output/images/`

### Advanced Usage

#### Custom Output Directory
```bash
python DeepSeek_OCR_pdf_to_md.py --input document.pdf --output ./my_output
```

#### Save Both Raw and Cleaned Versions
```bash
python DeepSeek_OCR_pdf_to_md.py --input document.pdf --save-raw
```

This creates:
- `document_cleaned.md` - Clean markdown without OCR markers
- `document_raw.md` - Raw OCR output with all markers

#### Custom OCR Prompt
```bash
python DeepSeek_OCR_pdf_to_md.py --input document.pdf --prompt "<image>\n<|grounding|>Extract all text and tables."
```

#### Higher Quality Conversion
```bash
python DeepSeek_OCR_pdf_to_md.py --input document.pdf --dpi 300
```

#### Skip Auto-Cleaning
```bash
python DeepSeek_OCR_pdf_to_md.py --input document.pdf --no-clean
```

## Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input` | Input PDF file path (required) | - |
| `--output` | Output directory path | `output` |
| `--model` | Path to DeepSeek OCR model | From `MODEL_PATH` env or `deepseek-ai/deepseek-ocr` |
| `--prompt` | Custom OCR prompt | `<image>\n<|grounding|>Convert the document to markdown.` |
| `--dpi` | DPI for PDF to image conversion | `144` |
| `--no-clean` | Disable automatic cleaning | `False` |
| `--save-raw` | Save raw OCR output | `False` |
| `--max-concurrency` | Maximum concurrent processing | `1` |

## Windows-Specific Fixes

### 1. UTF-8 Console Encoding
The script automatically detects Windows and forces UTF-8 encoding:
```python
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

### 2. ASCII-Safe Symbols
Replaced Unicode characters with ASCII equivalents:
- `✓` (U+2713) → `[OK]`
- `✗` (U+2717) → `[X]`
- Other symbols replaced similarly

### 3. Safe Print Function
Gracefully handles encoding errors:
```python
def safe_print(message: str):
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('ascii', errors='replace').decode('ascii'))
```

### 4. File Path Handling
Uses `pathlib.Path` for cross-platform path handling.

## Output Format

### Cleaned Markdown
- Removes OCR grounding markers (`<|ref|>`, `<|det|>`, etc.)
- Converts image references to Markdown syntax
- Cleans up LaTeX symbols
- Removes excessive newlines

### Raw Markdown
- Preserves all OCR markers
- Useful for debugging or custom post-processing

## Example Output Structure

```
output/
├── document_cleaned.md
├── document_raw.md (if --save-raw used)
└── images/
    ├── 0_0.jpg
    ├── 0_1.jpg
    └── ...
```

## Troubleshooting

### Issue: Model not found
**Solution:** Set the `MODEL_PATH` environment variable:
```bash
set MODEL_PATH=C:\path\to\deepseek-ocr-model
python DeepSeek_OCR_pdf_to_md.py --input document.pdf
```

### Issue: CUDA out of memory
**Solution:** Reduce max concurrency:
```bash
python DeepSeek_OCR_pdf_to_md.py --input document.pdf --max-concurrency 1
```

### Issue: Unicode errors still occurring
**Solution:** Try running with Python UTF-8 mode:
```bash
set PYTHONUTF8=1
python DeepSeek_OCR_pdf_to_md.py --input document.pdf
```

### Issue: Poor OCR quality
**Solution:** Increase DPI for better image quality:
```bash
python DeepSeek_OCR_pdf_to_md.py --input document.pdf --dpi 300
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_PATH` | Path to DeepSeek OCR model | `deepseek-ai/deepseek-ocr` |
| `PYTHONUTF8` | Force UTF-8 mode in Python | Not set |
| `CUDA_VISIBLE_DEVICES` | GPU device selection | `0` |

## Technical Details

### PDF Conversion Process
1. PDF pages → High-resolution images (configurable DPI)
2. Images → OCR processing with DeepSeek
3. OCR results → Markdown with image extraction
4. Content cleaning → Final markdown output

### Image Processing
- Default DPI: 144 (good balance of quality and size)
- Format: PNG → RGB conversion
- Cropping mode: Enabled by default for better accuracy

### OCR Configuration
- Temperature: 0.0 (deterministic output)
- Max tokens: 8192
- No-repeat n-gram filtering (size: 20, window: 50)

## Performance Tips

1. **For large PDFs:** Process in batches or use higher concurrency
2. **For better quality:** Increase DPI to 200-300
3. **For faster processing:** Reduce DPI to 100-120
4. **GPU memory:** Adjust `--max-concurrency` based on available VRAM

## License

This script is part of the DeepSeek-OCR Dockerized API project.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the error messages for specific guidance
3. Open an issue on the project repository
