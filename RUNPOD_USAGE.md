# Using RunPod Serverless Endpoint from Terminal

This guide shows you how to send PDFs to your RunPod serverless endpoint and get markdown files back.

## Prerequisites

1. **RunPod Endpoint Running**: Your endpoint must be deployed and active
2. **Python 3.7+** installed on your Mac
3. **Required Python packages**:
   ```bash
   pip install requests Pillow
   ```

## Step 1: Get Your RunPod Credentials

### Get Your Endpoint URL

1. Go to [RunPod Dashboard](https://www.runpod.io/console/serverless)
2. Click on your DeepSeek-OCR endpoint
3. Go to the **"API"** tab
4. Copy your endpoint URL - it looks like:
   ```
   https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync
   ```

### Get Your API Key

1. Go to [RunPod Settings](https://www.runpod.io/console/user/settings)
2. Click **"API Keys"**
3. Copy your API key or create a new one

## Step 2: Set Environment Variables

On your Mac terminal:

```bash
# Set your RunPod API key
export RUNPOD_API_KEY='your_api_key_here'

# Set your endpoint URL (use /runsync for synchronous responses)
export RUNPOD_ENDPOINT_URL='https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync'
```

**Pro Tip**: Add these to your `~/.zshrc` or `~/.bashrc` to make them permanent:

```bash
echo "export RUNPOD_API_KEY='your_api_key_here'" >> ~/.zshrc
echo "export RUNPOD_ENDPOINT_URL='https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync'" >> ~/.zshrc
source ~/.zshrc
```

## Step 3: Test with a Single PDF

### Option A: Quick Test Script

```bash
# Test a single PDF
python test_runpod_endpoint.py path/to/your/document.pdf
```

This will:
- Send the PDF to your RunPod endpoint
- Wait for processing (can take 1-5 minutes depending on PDF size)
- Save the result as `document-MD.md` in the same directory

### Option B: Using curl (Advanced)

```bash
# Encode your PDF to base64
PDF_BASE64=$(base64 -i your_document.pdf)

# Send to RunPod
curl -X POST "${RUNPOD_ENDPOINT_URL}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -d '{
    "input": {
      "pdf_base64": "'"${PDF_BASE64}"'",
      "prompt": "<image>\n<|grounding|>Convert the document to markdown."
    }
  }'
```

## Step 4: Batch Process Multiple PDFs

### Process all PDFs in a folder

1. **Create a `data` folder** and put your PDFs there:
   ```bash
   mkdir -p data
   cp your_pdfs/*.pdf data/
   ```

2. **Run the batch processor**:
   ```bash
   python pdf_to_markdown_runpod.py
   ```

This will:
- Find all PDF files in the `data/` folder
- Process each one using your RunPod endpoint
- Save markdown files with `-MD.md` suffix
- Create a log file: `pdf_processor_runpod.log`

### Example Output

```
PDF to Markdown Processor (RunPod Serverless)

[1/3] Processing: invoice_2024.pdf
✅ Saved: data/invoice_2024-MD.md

[2/3] Processing: report.pdf
✅ Saved: data/report-MD.md

[3/3] Processing: manual.pdf
✅ Saved: data/manual-MD.md

✅ Successfully converted 3 PDF files!
   📄 data/invoice_2024-MD.md
   📄 data/report-MD.md
   📄 data/manual-MD.md
```

## Understanding the Response Format

Your RunPod handler returns responses in this format:

### Single-page PDF response:
```json
{
  "output": {
    "success": true,
    "result": "# Markdown content here..."
  }
}
```

### Multi-page PDF response:
```json
{
  "output": {
    "success": true,
    "total_pages": 3,
    "results": [
      {"page": 1, "result": "Page 1 markdown..."},
      {"page": 2, "result": "Page 2 markdown..."},
      {"page": 3, "result": "Page 3 markdown..."}
    ]
  }
}
```

## Troubleshooting

### Error: "Cannot connect to API"
- ✅ Check that your endpoint is **Active** in RunPod dashboard
- ✅ Verify the endpoint URL is correct (should end with `/runsync` or `/run`)
- ✅ Check your API key is valid

### Error: "worker exited with exit code 1"
- ❌ This is the PyTorch/transformers compatibility issue
- ✅ **Solution**: Rebuild your Docker image with the fix (see main README)

### Error: "Request timeout"
- Large PDFs can take 5-10 minutes
- ✅ Increase the timeout in the script (default is 600 seconds)
- ✅ Or use `/run` endpoint for async processing (returns job ID)

### Error: "Handler error: ..."
- Check the RunPod logs in your dashboard
- Look at `pdf_processor_runpod.log` for details

## Cost Optimization Tips

1. **Use `/runsync` endpoint** for immediate results (blocks until complete)
2. **Use `/run` endpoint** for async (returns job ID, check later with `/status`)
3. **Scale down workers** when not in use to save costs
4. **Test with small PDFs first** to verify everything works

## Advanced: Using Async Endpoint

For very large PDFs, use async mode:

```bash
# Send request (returns immediately with job ID)
JOB_ID=$(curl -X POST "${RUNPOD_ENDPOINT_URL/runsync/run}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -d '{"input": {...}}' | jq -r '.id')

echo "Job ID: ${JOB_ID}"

# Check status later
curl "${RUNPOD_ENDPOINT_URL/runsync/status}/${JOB_ID}" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}"
```

## Scripts Included

| Script | Purpose |
|--------|---------|
| `test_runpod_endpoint.py` | Test a single PDF file |
| `pdf_to_markdown_runpod.py` | Batch process all PDFs in `data/` folder |
| `pdf_to_markdown_processor_enhanced.py` | Original script (for local API) |

## Need Help?

- Check RunPod logs: Dashboard -> Your Endpoint -> Logs
- Check local logs: `pdf_processor_runpod.log`
- Verify worker is running: Dashboard -> Your Endpoint -> Workers
