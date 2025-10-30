# DeepSeek OCR PDF to Markdown - API Client (Windows Compatible)

**Simple API client script** that sends PDFs to your RunPod or local API endpoint for processing.

## What This Script Does

1. Takes a PDF file on your computer
2. Sends it to your RunPod API (or any DeepSeek OCR API endpoint)
3. Receives the markdown result
4. Saves it as a `.md` file

**No GPU, no heavy dependencies, no local model required!**

## Installation

### macOS
```bash
pip3 install requests
```

### Windows
```bash
pip install requests
```

That's it! Just one dependency.

## Usage

### Basic Usage (RunPod)

```bash
python3 DeepSeek_OCR_pdf_to_md_API.py \
  --input document.pdf \
  --api https://your-runpod-id.runpod.net/ocr/pdf
```

### Windows Example

```bash
python DeepSeek_OCR_pdf_to_md_API.py --input "C:\Users\YourName\Desktop\document.pdf" --api https://your-runpod.com/ocr/pdf
```

### macOS Example

```bash
python3 DeepSeek_OCR_pdf_to_md_API.py --input "/Users/nobody1/Desktop/Claude Code Screenshot.pdf" --api https://your-runpod.com/ocr/pdf
```

### Local API Server

If you're running the API locally:

```bash
python3 DeepSeek_OCR_pdf_to_md_API.py \
  --input document.pdf \
  --api http://localhost:8000/ocr/pdf
```

### Custom Output Directory

```bash
python3 DeepSeek_OCR_pdf_to_md_API.py \
  --input document.pdf \
  --api https://your-runpod.com/ocr/pdf \
  --output ./my_results
```

### Large PDF (Longer Timeout)

```bash
python3 DeepSeek_OCR_pdf_to_md_API.py \
  --input large_document.pdf \
  --api https://your-runpod.com/ocr/pdf \
  --timeout 600
```

### Custom Prompt

```bash
python3 DeepSeek_OCR_pdf_to_md_API.py \
  --input document.pdf \
  --api https://your-runpod.com/ocr/pdf \
  --prompt "<image>\n<|grounding|>Extract all tables and text."
```

## Command Line Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--input` | Yes | Input PDF file path | - |
| `--api` | Yes | API endpoint URL | - |
| `--output` | No | Output directory | `output` |
| `--prompt` | No | Custom OCR prompt | `<image>\n<|grounding|>Convert the document to markdown.` |
| `--timeout` | No | Request timeout (seconds) | `300` |

## Finding Your RunPod API URL

1. Go to your RunPod dashboard
2. Find your endpoint
3. The URL will look like: `https://xxxxx-yyyyy.runpod.net/ocr/pdf`
4. Use that full URL with the `--api` argument

## Output

The script creates:
```
output/
└── document.md
```

If the file already exists, it adds a number: `document_1.md`, `document_2.md`, etc.

## Windows-Specific Features

This script fixes the Windows Unicode encoding errors:
- No `✓` or `✗` symbols (uses `[OK]` and `[X]` instead)
- Forces UTF-8 encoding for console output
- Handles Windows file paths correctly

## Error Handling

### Connection Errors
If you see "Connection error", check:
1. Is your RunPod endpoint running?
2. Is the URL correct?
3. Do you have internet connection?

### Timeout Errors
If processing takes too long:
```bash
python3 DeepSeek_OCR_pdf_to_md_API.py --input large.pdf --api YOUR_URL --timeout 600
```

### API Errors
If you get a 4xx or 5xx error:
1. Check your API endpoint is correct
2. Verify your RunPod service is running
3. Check the API logs on RunPod

## Comparison with Local Script

| Feature | API Client (This Script) | Local Script |
|---------|-------------------------|--------------|
| Dependencies | Just `requests` | PyMuPDF, torch, vllm, etc. |
| GPU Required | No | Yes (8GB+ VRAM) |
| Where it runs | Sends to RunPod/API | On your machine |
| Installation | 1 minute | 30+ minutes |
| Use case | Remote processing | Local processing |

## Quick Start Checklist

- [ ] Install Python 3.7+
- [ ] Install requests: `pip3 install requests`
- [ ] Get your RunPod API URL
- [ ] Run: `python3 DeepSeek_OCR_pdf_to_md_API.py --input file.pdf --api YOUR_URL`
- [ ] Check the `output/` folder for your markdown file

## Troubleshooting

### "No module named 'requests'"
```bash
pip3 install requests
```

### "Connection error"
Check your API URL and internet connection.

### "Request timed out"
Increase timeout: `--timeout 600`

### Unicode errors on Windows
The script automatically handles this, but if you still see issues:
```bash
set PYTHONUTF8=1
python DeepSeek_OCR_pdf_to_md_API.py --input file.pdf --api YOUR_URL
```

## Examples

### Process multiple PDFs (Bash/Terminal)
```bash
for pdf in *.pdf; do
  python3 DeepSeek_OCR_pdf_to_md_API.py --input "$pdf" --api https://your-runpod.com/ocr/pdf
done
```

### Process multiple PDFs (Windows PowerShell)
```powershell
Get-ChildItem *.pdf | ForEach-Object {
  python DeepSeek_OCR_pdf_to_md_API.py --input $_.FullName --api https://your-runpod.com/ocr/pdf
}
```

## Support

If you encounter issues:
1. Check you have `requests` installed: `pip3 list | grep requests`
2. Verify your API endpoint is accessible
3. Check the error message for specific guidance

## License

Part of the DeepSeek-OCR Dockerized API project.
