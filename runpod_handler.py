import runpod
import base64
from io import BytesIO
from PIL import Image
import sys
import os
import json
import requests
import fitz  # PyMuPDF
import subprocess
import io
import contextlib

# Verify transformers and tokenizers versions for DeepSeek-OCR compatibility
print("Checking transformers and tokenizers version compatibility...")
try:
    import transformers
    import tokenizers

    transformers_version = transformers.__version__
    tokenizers_version = tokenizers.__version__

    print(f"Current transformers version: {transformers_version}")
    print(f"Current tokenizers version: {tokenizers_version}")

    # DeepSeek-OCR requires specific versions to read tokenizer files correctly
    REQUIRED_TRANSFORMERS = "4.46.3"
    REQUIRED_TOKENIZERS = "0.20.3"

    needs_update = False

    if transformers_version != REQUIRED_TRANSFORMERS:
        print(f"Warning: transformers {transformers_version} detected, but DeepSeek-OCR requires {REQUIRED_TRANSFORMERS}")
        needs_update = True

    if tokenizers_version != REQUIRED_TOKENIZERS:
        print(f"Warning: tokenizers {tokenizers_version} detected, but DeepSeek-OCR requires {REQUIRED_TOKENIZERS}")
        needs_update = True

    if needs_update:
        print(f"Installing required versions: transformers=={REQUIRED_TRANSFORMERS}, tokenizers=={REQUIRED_TOKENIZERS}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--no-cache-dir",
            f"transformers=={REQUIRED_TRANSFORMERS}",
            f"tokenizers=={REQUIRED_TOKENIZERS}"
        ])
        print("Dependencies updated successfully. Reloading...")
        import importlib
        importlib.reload(transformers)
        importlib.reload(tokenizers)
    else:
        print("✓ All versions compatible with DeepSeek-OCR")

except Exception as e:
    print(f"Warning during version check: {e}")

# Add DeepSeek-OCR to path
sys.path.insert(0, '/app/DeepSeek-OCR')

from transformers import AutoModel, AutoTokenizer
import torch

# Initialize model at startup
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/models/DeepSeek-OCR")
print(f"Loading model from: {MODEL_PATH}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

# Try to use flash_attention_2 for optimal performance
try:
    print("Attempting to load model with flash_attention_2...")
    model = AutoModel.from_pretrained(
        MODEL_PATH,
        _attn_implementation='flash_attention_2',
        trust_remote_code=True,
        use_safetensors=True,
        torch_dtype=torch.bfloat16
    ).cuda().eval()
    print("Model loaded successfully with flash_attention_2!")
except Exception as e:
    print(f"Failed to load with flash_attention_2: {e}")
    print("Falling back to standard attention implementation...")
    model = AutoModel.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        use_safetensors=True,
        torch_dtype=torch.bfloat16
    ).cuda().eval()
    print("Model loaded successfully with standard attention!")

# Chunk storage directory (use network volume if available, otherwise /tmp)
CHUNK_STORAGE_DIR = os.environ.get("RUNPOD_VOLUME_PATH", "/tmp") + "/pdf_chunks"
os.makedirs(CHUNK_STORAGE_DIR, exist_ok=True)

def download_from_url(url, timeout=300):
    """Download file from URL"""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise Exception(f"Failed to download from URL: {str(e)}")

def pdf_to_images(pdf_data, dpi=144):
    """Convert PDF bytes to list of PIL Images"""
    images = []
    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]

        # Render page to pixmap
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        image = Image.open(BytesIO(img_data)).convert("RGB")
        images.append(image)

    pdf_document.close()
    return images

def process_image_with_model(image, prompt, page_num=None):
    """Process a single image with the model and capture stdout"""
    # Save image temporarily
    temp_path = f"/tmp/temp_image_{page_num or 0}.jpg"
    image.save(temp_path)
    
    # Capture stdout - DeepSeek-OCR prints results instead of returning them
    captured_output = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(captured_output):
            result = model.infer(
                tokenizer,
                prompt=prompt,
                image_file=temp_path,
                output_path="/tmp",
                base_size=1024,
                image_size=640,
                crop_mode=True
            )
    except Exception as e:
        print(f"Error during inference: {e}")
        result = None
    
    # Get the captured text from stdout
    ocr_text = captured_output.getvalue()
    
    # Clean up temp file
    try:
        os.remove(temp_path)
    except:
        pass
    
    # Clean up the OCR text by removing debug lines
    if ocr_text:
        lines = ocr_text.split('\n')
        # Filter out debug/log lines, keep only the actual OCR content
        cleaned_lines = []
        skip_markers = ['=====', 'PATCHES:', 'BASE:', 'Setting `pad_token_id`', 
                       'The attention mask', 'Processing page']
        
        for line in lines:
            # Skip empty lines and debug markers
            should_skip = False
            for marker in skip_markers:
                if marker in line:
                    should_skip = True
                    break
            
            if not should_skip and line.strip():
                cleaned_lines.append(line)
        
        ocr_text = '\n'.join(cleaned_lines).strip()
    
    # Return the captured output if result is None, otherwise return result
    return ocr_text if (result is None and ocr_text) else result

def handler(event):
    """
    RunPod handler for DeepSeek-OCR
    
    Returns markdown file as base64-encoded download
    """
    try:
        input_data = event.get("input", {})
        prompt = input_data.get("prompt", "<image>\n<|grounding|>Convert the document to markdown.")

        # Method 1: Handle chunked upload
        if "chunk_data" in input_data:
            return handle_chunked_upload(input_data, prompt)

        # Method 2: Handle PDF from URL
        elif "pdf_url" in input_data:
            pdf_url = input_data["pdf_url"]
            filename = pdf_url.split('/')[-1].replace('.pdf', '')
            print(f"Downloading PDF from URL: {pdf_url}")
            pdf_data = download_from_url(pdf_url)
            return process_pdf(pdf_data, prompt, filename)

        # Method 3: Handle PDF from base64
        elif "pdf_base64" in input_data:
            print("Processing PDF from base64")
            filename = input_data.get("filename", "document")
            pdf_data = base64.b64decode(input_data["pdf_base64"])
            return process_pdf(pdf_data, prompt, filename)

        # Method 4: Handle single image (backward compatible)
        elif "image_base64" in input_data:
            print("Processing single image")
            image_bytes = base64.b64decode(input_data["image_base64"])
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            result = process_image_with_model(image, prompt)
            return {
                "success": True,
                "result": result
            }

        else:
            return {
                "error": "No valid input provided. Expected one of: image_base64, pdf_base64, pdf_url, or chunk_data"
            }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def process_pdf(pdf_data, prompt, filename="document"):
    """Process a complete PDF and return markdown file"""
    print(f"Converting PDF to images (size: {len(pdf_data)} bytes)")
    images = pdf_to_images(pdf_data)
    print(f"Processing {len(images)} pages")

    results = []
    markdown_pages = []
    
    for i, image in enumerate(images):
        print(f"Processing page {i+1}/{len(images)}")
        page_result = process_image_with_model(image, prompt, page_num=i+1)
        
        results.append({
            "page": i + 1,
            "result": page_result
        })
        
        if page_result:
            # Add page separator
            if i > 0:
                markdown_pages.append("\n\n---\n\n")
            markdown_pages.append(f"# Page {i + 1}\n\n")
            markdown_pages.append(page_result)
    
    # Combine all pages into a single markdown document
    full_markdown = "".join(markdown_pages)
    
    # Save markdown to file
    md_filename = f"{filename}-MD.md"
    md_filepath = f"/tmp/{md_filename}"
    
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(full_markdown)
    
    print(f"Saved markdown to {md_filepath}")
    
    # Encode file as base64 for download
    with open(md_filepath, 'rb') as f:
        md_file_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Clean up temp file
    try:
        os.remove(md_filepath)
    except:
        pass

    return {
        "success": True,
        "total_pages": len(images),
        "results": results,
        "markdown": full_markdown,  # Full text content
        "markdown_file": {
            "filename": md_filename,
            "content_base64": md_file_base64,  # Base64-encoded file for download
            "size_bytes": len(full_markdown.encode('utf-8'))
        }
    }

def handle_chunked_upload(input_data, prompt):
    """
    Handle chunked PDF uploads with disk-based storage.
    Works across multiple workers if they share a network volume.
    """
    chunk_id = input_data.get("chunk_id")
    chunk_index = input_data.get("chunk_index")
    total_chunks = input_data.get("total_chunks")
    chunk_data = input_data.get("chunk_data")
    filename = input_data.get("filename", "document")

    if not all([chunk_id, chunk_index is not None, total_chunks, chunk_data]):
        return {"error": "Missing required chunk parameters"}

    # Create directory for this upload
    upload_dir = os.path.join(CHUNK_STORAGE_DIR, chunk_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Write metadata file on first chunk
    metadata_file = os.path.join(upload_dir, "metadata.json")
    if not os.path.exists(metadata_file):
        with open(metadata_file, 'w') as f:
            json.dump({"total_chunks": total_chunks, "filename": filename}, f)

    # Save this chunk to disk
    chunk_file = os.path.join(upload_dir, f"chunk_{chunk_index:04d}.bin")
    chunk_bytes = base64.b64decode(chunk_data)
    with open(chunk_file, 'wb') as f:
        f.write(chunk_bytes)

    print(f"Saved chunk {chunk_index + 1}/{total_chunks} for upload {chunk_id} ({len(chunk_bytes)} bytes)")

    # Check how many chunks we have
    existing_chunks = [f for f in os.listdir(upload_dir) if f.startswith("chunk_")]
    received_chunks = len(existing_chunks)

    print(f"Progress: {received_chunks}/{total_chunks} chunks received")

    # Check if all chunks received
    if received_chunks >= total_chunks:
        print(f"All chunks received for {chunk_id}, assembling PDF...")

        # Read metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            filename = metadata.get("filename", "document")

        # Assemble PDF from chunks
        pdf_data = b""
        for i in range(total_chunks):
            chunk_file = os.path.join(upload_dir, f"chunk_{i:04d}.bin")
            if not os.path.exists(chunk_file):
                return {"error": f"Missing chunk {i}"}
            with open(chunk_file, 'rb') as f:
                pdf_data += f.read()

        # Clean up chunk files
        try:
            import shutil
            shutil.rmtree(upload_dir)
            print(f"Cleaned up temporary files for {chunk_id}")
        except Exception as e:
            print(f"Warning: Failed to clean up chunks: {e}")

        # Process the complete PDF
        print(f"Assembled PDF: {len(pdf_data)} bytes, processing...")
        return process_pdf(pdf_data, prompt, filename)
    else:
        # Return status - more chunks needed
        return {
            "success": True,
            "status": "chunks_received",
            "received": received_chunks,
            "total": total_chunks,
            "message": f"Received {received_chunks}/{total_chunks} chunks"
        }

runpod.serverless.start({"handler": handler})
