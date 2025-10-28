# RunPod Deployment Guide - Large PDF Support

This guide covers deploying the enhanced DeepSeek-OCR handler with large PDF support to RunPod.

## What's New

The updated handler supports:
- **Chunked uploads** - Split large PDFs into 5MB chunks
- **URL-based uploads** - Download PDFs from external URLs
- **Multi-page PDF processing** - Automatic page-by-page OCR
- **Backward compatible** - Original image base64 method still works

---

## Prerequisites

1. **Docker installed** on your local machine
2. **Docker Hub account** (or other container registry)
3. **RunPod account** with API access
4. Your **RunPod API key** and **Endpoint ID**

## Version Requirements

**Important:** DeepSeek-OCR requires specific library versions:
- **transformers 4.46.3** - Required for model compatibility
- **tokenizers 0.20.3** - Required to read tokenizer files correctly
- **PyTorch 2.1.1+** - Base image provides this

These exact versions are needed because the model's tokenizer files were created with tokenizers 0.20.3 and cannot be read by older versions (e.g., 0.15.x). The Dockerfile.runpod automatically installs the correct versions.

---

## Step 1: Build the Docker Image

```bash
# Log in to Docker Hub
docker login

# Set your Docker Hub username
export DOCKER_USERNAME="your_dockerhub_username"

# Build the image (this will take 10-15 minutes)
docker build -f Dockerfile.runpod -t ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest .

# Tag with version
docker tag ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest ${DOCKER_USERNAME}/deepseek-ocr-runpod:v2.0
```

**Note:** The build includes:
- PyTorch 2.1.1 base image (~5 GB)
- DeepSeek-OCR model weights (~3 GB downloaded from HuggingFace)
- transformers 4.46.3 and tokenizers 0.20.3 (official DeepSeek-OCR versions)
- All dependencies including PyMuPDF for PDF processing

---

## Step 2: Push to Docker Hub

```bash
# Push latest tag
docker push ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest

# Push version tag
docker push ${DOCKER_USERNAME}/deepseek-ocr-runpod:v2.0
```

**Expected push time:** 5-10 minutes depending on your upload speed

---

## Step 3: Deploy to RunPod

### Option A: Update Existing Endpoint

1. Go to [RunPod Console](https://www.runpod.io/console/serverless)
2. Click on your endpoint (`99kl7k5tmp154s`)
3. Click **"Edit Template"**
4. Update the **Container Image** to: `your_dockerhub_username/deepseek-ocr-runpod:latest`
5. Click **"Save"**
6. Wait for workers to restart (2-3 minutes)

### Option B: Create New Endpoint

1. Go to **Serverless** → **New Endpoint**
2. Select GPU type (recommend: **RTX 4090** or **A100**)
3. Configure:
   - **Container Image:** `your_dockerhub_username/deepseek-ocr-runpod:latest`
   - **Container Disk:** 20 GB minimum
   - **Environment Variables:** (optional)
     - `MODEL_PATH=/app/models/DeepSeek-OCR`
     - `RUNPOD_VOLUME_PATH=/runpod-volume` (if using network volume)
4. Set **Workers:**
   - Min: 0 (scale to zero when idle)
   - Max: 3 (adjust based on needs)
5. Click **"Deploy"**

---

## Step 4: Test the Deployment

### Test 1: Single Image (Verify Basic Functionality)

```bash
# Create test script
cat > test_basic.py << 'EOF'
import requests
import base64

API_KEY = "your_runpod_api_key"
ENDPOINT_ID = "99kl7k5tmp154s"

# Create a simple test image
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (400, 100), color='white')
d = ImageDraw.Draw(img)
d.text((10,10), "Hello World", fill='black')

# Convert to base64
from io import BytesIO
buffer = BytesIO()
img.save(buffer, format='PNG')
img_base64 = base64.b64encode(buffer.getvalue()).decode()

# Send to RunPod
response = requests.post(
    f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run",
    headers={'Authorization': f'Bearer {API_KEY}'},
    json={'input': {'image_base64': img_base64}}
)

print(response.json())
EOF

python3 test_basic.py
```

**Expected output:** Job ID and status "IN_QUEUE" or "IN_PROGRESS"

### Test 2: Chunked Upload (Large PDF)

```bash
# Set environment variables
export RUNPOD_API_KEY="your_api_key"
export RUNPOD_ENDPOINT_ID="99kl7k5tmp154s"
export PDF_PATH="/path/to/your/large.pdf"

# Run the upload script
python3 upload_large_pdf_to_runpod.py
```

Choose option **1** (Chunked upload) when prompted.

### Test 3: Check Job Status

```python
import requests

API_KEY = "your_api_key"
ENDPOINT_ID = "99kl7k5tmp154s"
JOB_ID = "job_id_from_previous_test"

response = requests.get(
    f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{JOB_ID}",
    headers={'Authorization': f'Bearer {API_KEY}'}
)

print(response.json())
```

---

## Step 5: Monitor and Debug

### Check RunPod Logs

1. Go to **RunPod Console** → Your Endpoint
2. Click **"Logs"** tab
3. Look for:
   ```
   Model loaded successfully!
   Saved chunk 1/2 for upload <uuid>
   All chunks received for <uuid>, assembling PDF...
   Processing 10 pages
   ```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Container failed to start" | Check Docker image exists and is public |
| "Model not found" | Ensure `MODEL_PATH` env var is set |
| "Missing chunk X" | Check network stability, retry upload |
| "Out of memory" | Reduce DPI in PDF processing or use larger GPU |
| "data did not match any variant of untagged enum ModelWrapper" | Tokenizers version incompatibility - requires transformers 4.46.3 and tokenizers 0.20.3. Rebuild with latest Dockerfile.runpod |

---

## Optimizations

### Enable Network Volumes (Recommended for Production)

Network volumes allow chunk storage to persist across workers:

1. Create a network volume in RunPod
2. Attach to your endpoint
3. Set environment variable: `RUNPOD_VOLUME_PATH=/runpod-volume`
4. Chunks will be stored in `/runpod-volume/pdf_chunks`

**Benefits:**
- Chunks persist if worker restarts
- Works with multiple workers
- Faster for repeated uploads

### Adjust Chunk Size

Edit `upload_large_pdf_to_runpod.py`:
```python
CHUNK_SIZE_MB = 5  # Increase to 8 for faster uploads (but closer to limit)
```

### Tune GPU Settings

For faster processing, adjust in `runpod_handler.py`:
```python
base_size=1024,  # Increase to 2048 for higher quality
image_size=640,  # Increase to 1024 for better accuracy
dpi=144          # Increase to 300 for higher resolution PDFs
```

---

## Cost Estimation

**GPU Costs (approximate):**
- RTX 4090: $0.40/hour
- A100 40GB: $1.50/hour

**Example processing:**
- 100-page PDF
- ~30 seconds per page
- Total: ~50 minutes
- RTX 4090 cost: ~$0.33
- A100 cost: ~$1.25

**With scale-to-zero:** Workers shut down when idle, so you only pay for actual processing time.

---

## API Reference

### Chunked Upload Request Format

```json
{
  "input": {
    "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
    "chunk_index": 0,
    "total_chunks": 3,
    "chunk_data": "base64_encoded_chunk_data",
    "prompt": "<image>\\n<|grounding|>Convert to markdown."
  }
}
```

### URL Upload Request Format

```json
{
  "input": {
    "pdf_url": "https://example.com/document.pdf",
    "prompt": "<image>\\n<|grounding|>Convert to markdown."
  }
}
```

### Response Format

```json
{
  "success": true,
  "total_pages": 10,
  "results": [
    {
      "page": 1,
      "result": "# Page 1 Content\\n\\nExtracted markdown..."
    },
    {
      "page": 2,
      "result": "# Page 2 Content\\n\\n..."
    }
  ]
}
```

---

## Support

- **GitHub Issues:** [Create an issue](https://github.com/uoswi/DeekSeek-OCR---Dockerized-API/issues)
- **RunPod Docs:** https://docs.runpod.io/
- **DeepSeek-OCR:** https://github.com/deepseek-ai/DeepSeek-OCR

---

## Next Steps

After successful deployment:

1. ✅ Test with your 7.9 MB PDF
2. ✅ Monitor processing time and costs
3. ✅ Integrate into your application
4. Consider adding:
   - Result caching
   - Webhook notifications for long jobs
   - Batch processing queue
   - Custom post-processing pipelines
