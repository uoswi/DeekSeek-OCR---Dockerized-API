#!/usr/bin/env python3
"""
DeepSeek OCR PDF to Markdown - Simple API Client (Windows Compatible)
Sends PDF to RunPod/API endpoint for processing, no local dependencies needed
"""

import os
import sys
import io
import argparse
import json
import base64
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding issues
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)


class Colors:
    """Windows-safe color codes"""
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    RESET = '\033[0m'

    # Windows-safe symbols (ASCII only)
    CHECK = '[OK]'
    CROSS = '[X]'
    ARROW = '-->'
    INFO = '[i]'


def safe_print(message: str):
    """Print message with encoding error handling"""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('ascii', errors='replace').decode('ascii'))


class PDFToMarkdownAPI:
    """Simple API client for PDF to Markdown conversion"""

    def __init__(self, api_url: str, output_dir: str = "output"):
        """
        Initialize API client

        Args:
            api_url: Full API endpoint URL (e.g., https://your-runpod.com/ocr/pdf)
            output_dir: Directory for output files
        """
        self.api_url = api_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        safe_print(f"{Colors.BLUE}API Endpoint: {self.api_url}{Colors.RESET}")

    def convert_pdf(
        self,
        pdf_path: str,
        prompt: str = '<image>\n<|grounding|>Convert the document to markdown.',
        timeout: int = 300
    ) -> dict:
        """
        Send PDF to API for conversion

        Args:
            pdf_path: Path to PDF file
            prompt: OCR prompt
            timeout: Request timeout in seconds

        Returns:
            Dictionary with conversion results
        """
        pdf_path_obj = Path(pdf_path)

        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        safe_print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        safe_print(f"{Colors.CYAN}Converting PDF to Markdown{Colors.RESET}")
        safe_print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
        safe_print(f"{Colors.INFO} Input: {pdf_path}")
        safe_print(f"{Colors.INFO} Size: {pdf_path_obj.stat().st_size / 1024 / 1024:.2f} MB\n")

        try:
            # Read and send PDF file
            safe_print(f"{Colors.YELLOW}Uploading PDF to API...{Colors.RESET}")

            with open(pdf_path, 'rb') as pdf_file:
                files = {
                    'file': (pdf_path_obj.name, pdf_file, 'application/pdf')
                }
                data = {
                    'prompt': prompt
                }

                response = requests.post(
                    self.api_url,
                    files=files,
                    data=data,
                    timeout=timeout
                )

            # Check response
            if response.status_code != 200:
                safe_print(f"{Colors.RED}{Colors.CROSS} API Error (Status {response.status_code}){Colors.RESET}")
                safe_print(f"{Colors.RED}Response: {response.text}{Colors.RESET}")
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}",
                    'response': response.text
                }

            safe_print(f"{Colors.GREEN}{Colors.CHECK} API processing completed{Colors.RESET}")

            # Parse response
            result = response.json()

            # Extract markdown content
            markdown_content = self._extract_markdown(result)

            if not markdown_content:
                safe_print(f"{Colors.YELLOW}Warning: No markdown content found in response{Colors.RESET}")
                markdown_content = json.dumps(result, indent=2)

            # Save markdown file
            output_path = self._save_markdown(markdown_content, pdf_path_obj.stem)

            safe_print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")
            safe_print(f"{Colors.GREEN}{Colors.CHECK} Conversion completed successfully!{Colors.RESET}")
            safe_print(f"{Colors.GREEN}{'='*60}{Colors.RESET}\n")
            safe_print(f"{Colors.CHECK} Output: {output_path}\n")

            return {
                'success': True,
                'output_file': str(output_path),
                'api_response': result
            }

        except requests.exceptions.Timeout:
            safe_print(f"{Colors.RED}{Colors.CROSS} Request timed out after {timeout} seconds{Colors.RESET}")
            return {
                'success': False,
                'error': f"Request timed out after {timeout} seconds"
            }

        except requests.exceptions.ConnectionError as e:
            safe_print(f"{Colors.RED}{Colors.CROSS} Connection error: {e}{Colors.RESET}")
            return {
                'success': False,
                'error': f"Connection error: {e}"
            }

        except Exception as e:
            safe_print(f"{Colors.RED}{Colors.CROSS} Error: {e}{Colors.RESET}")
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_markdown(self, result: dict) -> str:
        """Extract markdown content from API response"""

        if isinstance(result, str):
            return result

        if not isinstance(result, dict):
            return str(result)

        # Try to find markdown in common response fields
        # Handle BatchOCRResponse format
        if "results" in result and isinstance(result["results"], list):
            markdown_parts = []
            for page_result in result["results"]:
                if isinstance(page_result, dict) and "result" in page_result:
                    page_content = page_result["result"]
                    if page_content:
                        markdown_parts.append(page_content)

            if markdown_parts:
                return "\n\n<--- Page Split --->\n\n".join(markdown_parts)

        # Try common field names
        for field in ["markdown", "content", "text", "result", "output", "data"]:
            if field in result:
                return str(result[field])

        # Return whole response as JSON if no standard field found
        return json.dumps(result, indent=2)

    def _save_markdown(self, content: str, base_name: str) -> Path:
        """Save markdown content to file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{base_name}.md"
        output_path = self.output_dir / output_filename

        # Handle duplicate filenames
        counter = 1
        while output_path.exists():
            output_filename = f"{base_name}_{counter}.md"
            output_path = self.output_dir / output_filename
            counter += 1

        # Save with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Convert PDF to Markdown using DeepSeek OCR API (Windows Compatible)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with RunPod
  python DeepSeek_OCR_pdf_to_md_API.py --input document.pdf --api https://your-runpod.com/ocr/pdf

  # Local API server
  python DeepSeek_OCR_pdf_to_md_API.py --input document.pdf --api http://localhost:8000/ocr/pdf

  # Custom output directory
  python DeepSeek_OCR_pdf_to_md_API.py --input document.pdf --api https://your-runpod.com/ocr/pdf --output ./my_output

  # Custom prompt
  python DeepSeek_OCR_pdf_to_md_API.py --input document.pdf --api https://your-runpod.com/ocr/pdf --prompt "<image>\\n<|grounding|>Extract all text."

  # Longer timeout for large PDFs
  python DeepSeek_OCR_pdf_to_md_API.py --input large.pdf --api https://your-runpod.com/ocr/pdf --timeout 600
        """
    )

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input PDF file path'
    )

    parser.add_argument(
        '--api',
        type=str,
        required=True,
        help='API endpoint URL (e.g., https://your-runpod.com/ocr/pdf or http://localhost:8000/ocr/pdf)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory path (default: output)'
    )

    parser.add_argument(
        '--prompt',
        type=str,
        default='<image>\n<|grounding|>Convert the document to markdown.',
        help='Custom OCR prompt'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Request timeout in seconds (default: 300)'
    )

    args = parser.parse_args()

    try:
        # Validate input file
        if not os.path.exists(args.input):
            safe_print(f"{Colors.RED}{Colors.CROSS} Error: Input file not found: {args.input}{Colors.RESET}")
            sys.exit(1)

        if not args.input.lower().endswith('.pdf'):
            safe_print(f"{Colors.RED}{Colors.CROSS} Error: Input file must be a PDF{Colors.RESET}")
            sys.exit(1)

        # Initialize API client
        client = PDFToMarkdownAPI(
            api_url=args.api,
            output_dir=args.output
        )

        # Convert PDF
        result = client.convert_pdf(
            pdf_path=args.input,
            prompt=args.prompt,
            timeout=args.timeout
        )

        # Exit with appropriate code
        if result['success']:
            safe_print(f"{Colors.GREEN}Status: COMPLETED{Colors.RESET}\n")
            sys.exit(0)
        else:
            safe_print(f"{Colors.RED}Status: FAILED{Colors.RESET}")
            safe_print(f"{Colors.RED}Error: {result.get('error', 'Unknown error')}{Colors.RESET}\n")
            sys.exit(1)

    except KeyboardInterrupt:
        safe_print(f"\n{Colors.YELLOW}Process interrupted by user{Colors.RESET}")
        sys.exit(1)

    except Exception as e:
        safe_print(f"\n{Colors.RED}{Colors.CROSS} Error: {e}{Colors.RESET}")
        import traceback
        safe_print(f"\n{Colors.RED}Traceback:{Colors.RESET}")
        safe_print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
