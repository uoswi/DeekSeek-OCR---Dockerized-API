#!/usr/bin/env python3
"""
PDF to Markdown Processor for RunPod Serverless Endpoints

This script processes PDFs using your RunPod serverless endpoint instead of a local API.
It scans the /data folder for PDF files and converts them to Markdown format.
"""

import os
import sys
import base64
import json
import logging
import requests
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_processor_runpod.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    RESET = '\033[0m'


class RunPodPDFProcessor:
    """Processor for converting PDF files to Markdown using RunPod Serverless Endpoint"""

    def __init__(self,
                 runpod_endpoint_url: str,
                 runpod_api_key: str,
                 data_folder: str = "data"):
        """
        Initialize the RunPod PDF processor

        Args:
            runpod_endpoint_url: Your RunPod endpoint URL (e.g., https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync)
            runpod_api_key: Your RunPod API key
            data_folder: Path to the folder containing PDF files
        """
        self.runpod_endpoint_url = runpod_endpoint_url
        self.runpod_api_key = runpod_api_key
        self.data_folder = Path(data_folder)
        self.data_folder.mkdir(exist_ok=True)

        logger.info(f"Initialized RunPod processor with endpoint: {runpod_endpoint_url}")

    def _send_to_runpod(self, pdf_path: str, prompt: str = None) -> Optional[dict]:
        """
        Send PDF to RunPod serverless endpoint

        Args:
            pdf_path: Path to the PDF file
            prompt: Optional custom prompt

        Returns:
            Response dict from RunPod or None if failed
        """
        if not prompt:
            prompt = "<image>\n<|grounding|>Convert the document to markdown."

        try:
            # Read and encode PDF
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

            logger.info(f"Sending PDF to RunPod: {pdf_path} ({len(pdf_bytes):,} bytes)")

            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.runpod_api_key}"
            }

            payload = {
                "input": {
                    "pdf_base64": pdf_base64,
                    "prompt": prompt
                }
            }

            # Send request (use runsync for synchronous response)
            response = requests.post(
                self.runpod_endpoint_url,
                headers=headers,
                json=payload,
                timeout=600  # 10 minutes
            )

            if response.status_code == 200:
                logger.info("Successfully received response from RunPod")
                return response.json()
            else:
                logger.error(f"RunPod request failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error sending to RunPod: {str(e)}")
            return None

    def _extract_markdown(self, response: dict) -> Optional[str]:
        """
        Extract markdown content from RunPod response

        Args:
            response: Response dict from RunPod

        Returns:
            Markdown content as string or None if extraction failed
        """
        if not response:
            return None

        try:
            # RunPod wraps handler response in {"output": ...}
            if "output" in response:
                output = response["output"]

                # Check for handler errors
                if isinstance(output, dict) and "error" in output:
                    logger.error(f"Handler error: {output['error']}")
                    if "traceback" in output:
                        logger.error(f"Traceback: {output['traceback']}")
                    return None

                # Check if successful
                if isinstance(output, dict) and output.get("success"):
                    # Multi-page PDF response
                    if "results" in output and isinstance(output["results"], list):
                        markdown_parts = []
                        for page_result in output["results"]:
                            if "result" in page_result:
                                markdown_parts.append(page_result["result"])

                        if markdown_parts:
                            return "\n\n<--- Page Split --->\n\n".join(markdown_parts)

                    # Single page or single result
                    elif "result" in output:
                        return output["result"]

            logger.error("Could not extract markdown from response")
            logger.debug(f"Response structure: {json.dumps(response, indent=2)[:500]}")
            return None

        except Exception as e:
            logger.error(f"Error extracting markdown: {str(e)}")
            return None

    def convert_pdf_to_markdown(self, pdf_path: str) -> Optional[str]:
        """
        Convert a single PDF file to Markdown using RunPod

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Path to the generated Markdown file, or None if conversion failed
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")

            # Send to RunPod
            response = self._send_to_runpod(pdf_path)

            if not response:
                logger.error(f"Failed to get response from RunPod for {pdf_path}")
                return None

            # Extract markdown
            markdown_content = self._extract_markdown(response)

            if not markdown_content:
                logger.error(f"Failed to extract markdown content for {pdf_path}")
                return None

            # Save markdown file with -MD suffix
            pdf_path_obj = Path(pdf_path)
            markdown_path = pdf_path_obj.with_name(f"{pdf_path_obj.stem}-MD.md")

            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"Successfully saved markdown to: {markdown_path}")
            return str(markdown_path)

        except Exception as e:
            logger.error(f"Error converting {pdf_path}: {str(e)}")
            return None

    def scan_and_process_all_pdfs(self):
        """
        Scan the data folder for PDF files and convert all of them

        Returns:
            List of paths to generated Markdown files
        """
        # Find all PDF files
        pdf_files = list(self.data_folder.glob("*.pdf"))

        if not pdf_files:
            logger.info(f"No PDF files found in {self.data_folder}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files to process")

        markdown_files = []
        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"\n{Colors.BLUE}[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}{Colors.RESET}")
            markdown_file = self.convert_pdf_to_markdown(str(pdf_file))
            if markdown_file:
                markdown_files.append(markdown_file)
                print(f"{Colors.GREEN}✅ Saved: {markdown_file}{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ Failed to process {pdf_file.name}{Colors.RESET}")

        return markdown_files


def main():
    """Main function"""
    print(f"{Colors.BLUE}PDF to Markdown Processor (RunPod Serverless){Colors.RESET}\n")

    # Get configuration from environment variables
    runpod_endpoint_url = os.environ.get("RUNPOD_ENDPOINT_URL")
    runpod_api_key = os.environ.get("RUNPOD_API_KEY")

    if not runpod_endpoint_url:
        print(f"{Colors.RED}Error: RUNPOD_ENDPOINT_URL not set!{Colors.RESET}")
        print("\nSet it like this:")
        print("  export RUNPOD_ENDPOINT_URL='https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync'")
        print("\nGet your endpoint URL from:")
        print("  RunPod Dashboard -> Your Endpoint -> API tab -> Copy the endpoint URL")
        sys.exit(1)

    if not runpod_api_key:
        print(f"{Colors.RED}Error: RUNPOD_API_KEY not set!{Colors.RESET}")
        print("\nSet it like this:")
        print("  export RUNPOD_API_KEY='your_api_key_here'")
        print("\nGet your API key from:")
        print("  RunPod Dashboard -> Settings -> API Keys")
        sys.exit(1)

    try:
        processor = RunPodPDFProcessor(
            runpod_endpoint_url=runpod_endpoint_url,
            runpod_api_key=runpod_api_key,
            data_folder="data"
        )

        markdown_files = processor.scan_and_process_all_pdfs()

        if markdown_files:
            print(f"\n{Colors.GREEN}✅ Successfully converted {len(markdown_files)} PDF files!{Colors.RESET}")
            for md_file in markdown_files:
                print(f"   📄 {md_file}")
        else:
            print(f"\n{Colors.YELLOW}⚠️  No PDF files were processed{Colors.RESET}")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
