# Quick Start Guide - RunPod Large PDF Upload

## 🚀 Deploy to RunPod (One-Time Setup)

### Step 1: Build and Push Docker Image

```bash
export DOCKER_USERNAME="your_dockerhub_username"
./deploy_to_runpod.sh
```

This takes **10-15 minutes** and includes:
- Building Docker image with PyTorch 2.1.1
- Downloading DeepSeek-OCR model (~3GB)
- Installing PyMuPDF for PDF processing
- Pushing to Docker Hub

---

### Step 2: Configure RunPod Endpoint

1. Go to https://www.runpod.io/console/serverless
2. Click your endpoint or create new one
3. Update **Container Image** to: `your_dockerhub_username/deepseek-ocr-runpod:latest`
4. Set **Container Disk**: 20 GB minimum
5. Optional: Add environment variable `RUNPOD_VOLUME_PATH=/runpod-volume` if using network volume
6. Click **Save** and wait 2-3 minutes for restart

---

## 📤 Upload Large PDFs

### Method 1: Chunked Upload (Recommended)

```bash
# Set environment variables
export RUNPOD_API_KEY="your_api_key_here"
export RUNPOD_ENDPOINT_ID="your_endpoint_id"
export PDF_PATH="/path/to/your/large.pdf"

# Run the upload script
python3 upload_large_pdf_to_runpod.py
```

**Choose option 1** when prompted.

**How it works:**
- Splits your PDF into 5MB chunks
- Each chunk sent separately (under 10 MiB limit)
- RunPod assembles chunks on disk
- Processes complete PDF automatically

**Best for:** PDFs 7MB - 500MB

---

### Method 2: URL-Based Upload

For PDFs larger than 500MB or if you already have it hosted:

```bash
export RUNPOD_API_KEY="your_api_key"
export RUNPOD_ENDPOINT_ID="your_endpoint_id"

# Run the script
python3 upload_large_pdf_to_runpod.py
```

**Choose option 2** to upload to transfer.sh automatically, or **option 3** to provide your own URL.

**Best for:** Very large PDFs (>500MB) or when you have cloud storage

---

## 🧪 Test Your Deployment

### Test 1: Health Check

```bash
# Check if workers are running
curl -X GET "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/health" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Test 2: Single Image (Quick Test)

```python
import requests
import base64
from PIL import Image
from io import BytesIO

# Create test image
img = Image.new('RGB', (400, 100), color='white')
from PIL import ImageDraw
d = ImageDraw.Draw(img)
d.text((10,10), "Hello RunPod", fill='black')

# Convert to base64
buffer = BytesIO()
img.save(buffer, format='PNG')
img_base64 = base64.b64encode(buffer.getvalue()).decode()

# Send to RunPod
response = requests.post(
    "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run",
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={'input': {'image_base64': img_base64}}
)

print(response.json())
```

### Test 3: Your 7.9 MB PDF

```bash
export RUNPOD_API_KEY="your_api_key"
export RUNPOD_ENDPOINT_ID="99kl7k5tmp154s"
export PDF_PATH="/Users/nobody1/Documents/Demo/demo.pdf"

python3 upload_large_pdf_to_runpod.py
# Choose option 1 (Chunked Upload)
```

---

## 📊 Expected Results

### Chunked Upload Output

```
============================================================
RunPod DeepSeek-OCR Large PDF Upload
============================================================

PDF: /Users/nobody1/Documents/Demo/demo.pdf
Size: 7.90 MB

============================================================
Choose upload method:
  1. Chunked upload (splits file into 5MB chunks)
  2. URL-based upload (via transfer.sh)
  3. URL-based upload (provide your own URL)
============================================================

Enter choice [1-3] (default: 1): 1

============================================================
CHUNKED UPLOAD METHOD
============================================================
Reading PDF: /Users/nobody1/Documents/Demo/demo.pdf
PDF size: 7,908,827 bytes (7.90 MB)
Chunk size: 5 MB
Total chunks: 2
Upload ID: 550e8400-e29b-41d4-a716-446655440000

Uploading chunk 1/2 (5.00 MB, base64: 6.67 MB)...
Response: 200
  → Received 1/2 chunks

Uploading chunk 2/2 (2.90 MB, base64: 3.87 MB)...
Response: 200

============================================================
ALL CHUNKS UPLOADED SUCCESSFULLY!
============================================================
{
  "success": true,
  "total_pages": 10,
  "results": [
    {
      "page": 1,
      "result": "# Page 1 Content\n\n..."
    },
    ...
  ]
}
```

---

## 🔍 Troubleshooting

### Issue: "Container failed to start"

```bash
# Verify image exists
docker images | grep deepseek-ocr-runpod

# Push again if missing
docker push ${DOCKER_USERNAME}/deepseek-ocr-runpod:latest
```

### Issue: "No workers available"

1. Go to RunPod Console → Your Endpoint
2. Check "Worker Status" - should show at least 1 worker
3. If 0 workers, check your worker configuration and GPU availability

### Issue: "Missing chunk X"

- Network interruption during upload
- Solution: Re-run the upload script (it will use a new chunk_id)

### Issue: "Timeout"

- PDF is very large (>100 pages)
- Solution: Use URL-based upload method instead

---

## 💰 Cost Estimate (Your 7.9 MB PDF)

**Your PDF specs:**
- Size: 7.9 MB
- Estimated pages: ~10-20 pages
- Processing time: ~5-10 minutes on RTX 4090

**Costs:**
- RTX 4090: $0.40/hour → **~$0.03-0.07 per run**
- A100: $1.50/hour → **~$0.12-0.25 per run**

With scale-to-zero, workers shut down when idle, so you only pay for actual processing time!

---

## 📚 Additional Resources

- **Full Guide**: `DEPLOYMENT_GUIDE.md`
- **API Reference**: `DEPLOYMENT_GUIDE.md` (API Reference section)
- **Code**: `runpod_handler.py` (handler implementation)
- **Upload Script**: `upload_large_pdf_to_runpod.py`

---

## 🎯 Summary

**What you built:**
- ✅ RunPod handler supporting 4 input methods
- ✅ Chunked upload for large PDFs (bypasses 10 MiB limit)
- ✅ URL-based upload for unlimited file sizes
- ✅ Disk-based storage (works across multiple workers)
- ✅ Automated deployment script

**What you need to do:**
1. Run `./deploy_to_runpod.sh` to build and push Docker image
2. Update your RunPod endpoint to use the new image
3. Test with `upload_large_pdf_to_runpod.py`

**Your specific case:**
- 7.9 MB PDF → Use **chunked upload** (splits into 2 chunks)
- Cost: ~$0.03-0.07 per processing run on RTX 4090
- Processing time: ~5-10 minutes

---

Ready to deploy? Run: `./deploy_to_runpod.sh`
