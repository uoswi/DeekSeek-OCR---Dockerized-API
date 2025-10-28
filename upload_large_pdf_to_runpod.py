#!/usr/bin/env python3
"""
Enhanced PDF Upload to RunPod DeepSeek-OCR API
Supports large PDFs via chunked upload or URL-based upload
"""
import requests
import base64
import json
import sys
import os
import uuid
import math
from pathlib import Path

# Configuration
PDF_PATH = os.environ.get("PDF_PATH", "/path/to/your/file.pdf")
API_KEY = os.environ.get("RUNPOD_API_KEY", "your_api_key_here")
ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "your_endpoint_id")
BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

# Upload settings
CHUNK_SIZE_MB = 5  # 5 MB chunks (well under 10 MiB limit)
CHUNK_SIZE_BYTES = CHUNK_SIZE_MB * 1024 * 1024


def get_file_size_mb(file_path):
    """Get file size in MB"""
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)


def upload_chunked(pdf_path, prompt=None):
    """
    Upload large PDF in chunks
    Each chunk is base64 encoded and sent separately
    """
    print(f"\n{'='*60}")
    print("CHUNKED UPLOAD METHOD")
    print(f"{'='*60}")
    print(f"Reading PDF: {pdf_path}")

    try:
        # Read PDF
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        file_size = len(pdf_data)
        file_size_mb = file_size / (1024 * 1024)

        # Calculate chunks
        total_chunks = math.ceil(file_size / CHUNK_SIZE_BYTES)
        chunk_id = str(uuid.uuid4())

        print(f"PDF size: {file_size:,} bytes ({file_size_mb:.2f} MB)")
        print(f"Chunk size: {CHUNK_SIZE_MB} MB")
        print(f"Total chunks: {total_chunks}")
        print(f"Upload ID: {chunk_id}")
        print()

        # Upload each chunk
        for i in range(total_chunks):
            start = i * CHUNK_SIZE_BYTES
            end = min((i + 1) * CHUNK_SIZE_BYTES, file_size)
            chunk_data = pdf_data[start:end]
            chunk_base64 = base64.b64encode(chunk_data).decode('utf-8')

            chunk_size_mb = len(chunk_data) / (1024 * 1024)
            chunk_base64_mb = len(chunk_base64) / (1024 * 1024)

            print(f"Uploading chunk {i+1}/{total_chunks} "
                  f"({chunk_size_mb:.2f} MB, base64: {chunk_base64_mb:.2f} MB)...")

            payload = {
                'input': {
                    'chunk_id': chunk_id,
                    'chunk_index': i,
                    'total_chunks': total_chunks,
                    'chunk_data': chunk_base64
                }
            }

            # Add prompt on last chunk
            if i == total_chunks - 1 and prompt:
                payload['input']['prompt'] = prompt

            response = requests.post(
                f"{BASE_URL}/run",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {API_KEY}'
                },
                json=payload,
                timeout=300
            )

            print(f"Response: {response.status_code}")

            if response.status_code != 200:
                print(f"ERROR: {response.status_code}")
                print(response.text)
                return None

            result = response.json()

            # Check if this is the final response
            if i == total_chunks - 1:
                print(f"\n{'='*60}")
                print("ALL CHUNKS UPLOADED SUCCESSFULLY!")
                print(f"{'='*60}")
                print(json.dumps(result, indent=2))
                return result
            else:
                # Intermediate chunk response
                if 'status' in result:
                    print(f"  → {result.get('message', 'Chunk received')}")
                print()

        return None

    except FileNotFoundError:
        print(f"ERROR: PDF file not found at {pdf_path}")
        return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def upload_via_url(pdf_url, prompt=None):
    """
    Upload PDF by providing a URL
    RunPod will download the PDF directly from the URL

    Note: You need to upload the PDF to a temporary hosting service first
    Examples: transfer.sh, file.io, tmpfiles.org, or your own S3 bucket
    """
    print(f"\n{'='*60}")
    print("URL-BASED UPLOAD METHOD")
    print(f"{'='*60}")
    print(f"PDF URL: {pdf_url}")
    print(f"\nSending to: {BASE_URL}/run")

    try:
        payload = {
            'input': {
                'pdf_url': pdf_url
            }
        }

        if prompt:
            payload['input']['prompt'] = prompt

        response = requests.post(
            f"{BASE_URL}/run",
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {API_KEY}'
            },
            json=payload,
            timeout=600  # 10 minutes for large files
        )

        print(f"\nResponse Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n{'='*60}")
            print("SUCCESS!")
            print(f"{'='*60}")
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"\nERROR: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def upload_to_transfer_sh(pdf_path):
    """
    Upload PDF to transfer.sh (temporary file hosting)
    Returns URL for the uploaded file
    """
    print(f"\n{'='*60}")
    print("Uploading to transfer.sh for URL-based method...")
    print(f"{'='*60}")

    try:
        filename = os.path.basename(pdf_path)

        with open(pdf_path, 'rb') as f:
            response = requests.post(
                'https://transfer.sh/',
                files={filename: f},
                timeout=300
            )

        if response.status_code == 200:
            url = response.text.strip()
            print(f"✓ Uploaded successfully!")
            print(f"URL: {url}")
            print(f"Note: This URL expires in 14 days")
            return url
        else:
            print(f"ERROR: Failed to upload to transfer.sh ({response.status_code})")
            return None

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None


def check_job_status(job_id):
    """Check the status of a RunPod job"""
    try:
        response = requests.get(
            f"{BASE_URL}/status/{job_id}",
            headers={
                'Authorization': f'Bearer {API_KEY}'
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"ERROR checking status: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None


def main():
    print("="*60)
    print("RunPod DeepSeek-OCR Large PDF Upload")
    print("="*60)

    if not os.path.exists(PDF_PATH):
        print(f"\nERROR: PDF file not found at {PDF_PATH}")
        print("Please update PDF_PATH in the script")
        return

    file_size_mb = get_file_size_mb(PDF_PATH)
    print(f"\nPDF: {PDF_PATH}")
    print(f"Size: {file_size_mb:.2f} MB")

    # Choose method based on file size
    if file_size_mb < 7:
        print("\nFile is small enough for direct upload")
        print("However, showing chunked upload for demonstration...")
        method = "chunked"
    else:
        print("\nFile is too large for direct base64 upload")
        print("Recommended method: URL-based upload")
        method = "url"

    # Let user choose
    print(f"\n{'='*60}")
    print("Choose upload method:")
    print("  1. Chunked upload (splits file into 5MB chunks)")
    print("  2. URL-based upload (via transfer.sh)")
    print("  3. URL-based upload (provide your own URL)")
    print(f"{'='*60}")

    choice = input(f"\nEnter choice [1-3] (default: {'1' if method == 'chunked' else '2'}): ").strip()

    if not choice:
        choice = '1' if method == 'chunked' else '2'

    result = None

    if choice == '1':
        result = upload_chunked(PDF_PATH)
    elif choice == '2':
        url = upload_to_transfer_sh(PDF_PATH)
        if url:
            print(f"\nNow sending URL to RunPod...")
            result = upload_via_url(url)
    elif choice == '3':
        url = input("Enter the URL where your PDF is hosted: ").strip()
        if url:
            result = upload_via_url(url)
        else:
            print("ERROR: No URL provided")
    else:
        print("Invalid choice")
        return

    # If we got a job ID, optionally check status
    if result and 'id' in result:
        job_id = result['id']
        print(f"\n{'='*60}")
        print(f"Job ID: {job_id}")
        print(f"Status: {result.get('status', 'UNKNOWN')}")
        print(f"{'='*60}")

        check = input("\nCheck job status? [y/N]: ").strip().lower()
        if check == 'y':
            print("\nChecking status...")
            status = check_job_status(job_id)
            if status:
                print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
