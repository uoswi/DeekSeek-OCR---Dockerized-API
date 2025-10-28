#!/usr/bin/env python3
"""
Test script for RunPod Serverless Endpoint
Sends a PDF to your RunPod endpoint and gets back markdown
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path

# IMPORTANT: Replace with your RunPod endpoint URL
# Get this from RunPod dashboard -> Your Endpoint -> "API" tab
RUNPOD_ENDPOINT_URL = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "YOUR_API_KEY_HERE")


def send_pdf_to_runpod(pdf_path: str, prompt: str = None) -> dict:
    """
    Send a PDF to RunPod serverless endpoint

    Args:
        pdf_path: Path to the PDF file
        prompt: Optional custom prompt (defaults to markdown conversion)

    Returns:
        Response dict from RunPod
    """
    if not prompt:
        prompt = "<image>\n<|grounding|>Convert the document to markdown."

    # Read and encode the PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    # Prepare the RunPod request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }

    payload = {
        "input": {
            "pdf_base64": pdf_base64,
            "prompt": prompt
        }
    }

    print(f"📤 Sending PDF to RunPod: {pdf_path}")
    print(f"   File size: {len(pdf_bytes):,} bytes")

    # Send request
    response = requests.post(
        RUNPOD_ENDPOINT_URL,
        headers=headers,
        json=payload,
        timeout=600  # 10 minutes timeout for large PDFs
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


def extract_markdown_from_response(response: dict) -> str:
    """
    Extract markdown content from RunPod response

    Args:
        response: Response dict from RunPod

    Returns:
        Markdown content as string
    """
    if not response:
        return None

    # RunPod wraps the handler response in {"output": ...}
    if "output" in response:
        output = response["output"]

        # Check if successful
        if isinstance(output, dict) and output.get("success"):
            # Multi-page PDF
            if "results" in output:
                markdown_parts = []
                for page_result in output["results"]:
                    if "result" in page_result:
                        markdown_parts.append(page_result["result"])
                return "\n\n<--- Page Split --->\n\n".join(markdown_parts)

            # Single page
            elif "result" in output:
                return output["result"]

        # Error case
        elif isinstance(output, dict) and "error" in output:
            print(f"❌ Handler Error: {output['error']}")
            if "traceback" in output:
                print(f"Traceback: {output['traceback']}")
            return None

    # Fallback: return the whole response as JSON
    return json.dumps(response, indent=2)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_runpod_endpoint.py <path_to_pdf>")
        print("\nBefore running, set these environment variables:")
        print("  export RUNPOD_API_KEY='your_api_key_here'")
        print("\nAnd update RUNPOD_ENDPOINT_URL in this script")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)

    # Check configuration
    if "YOUR_ENDPOINT_ID" in RUNPOD_ENDPOINT_URL:
        print("❌ Error: Please update RUNPOD_ENDPOINT_URL in the script!")
        print("   Get your endpoint URL from RunPod dashboard -> Your Endpoint -> API tab")
        sys.exit(1)

    if RUNPOD_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ Error: Please set your RUNPOD_API_KEY!")
        print("   export RUNPOD_API_KEY='your_api_key_here'")
        sys.exit(1)

    # Send to RunPod
    response = send_pdf_to_runpod(pdf_path)

    if not response:
        sys.exit(1)

    # Extract markdown
    markdown = extract_markdown_from_response(response)

    if markdown:
        # Save to file
        pdf_path_obj = Path(pdf_path)
        markdown_path = pdf_path_obj.with_name(f"{pdf_path_obj.stem}-MD.md")

        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"\n📄 Markdown saved to: {markdown_path}")
        print(f"   Size: {len(markdown):,} characters")
    else:
        print("❌ Failed to extract markdown from response")
        sys.exit(1)


if __name__ == "__main__":
    main()
