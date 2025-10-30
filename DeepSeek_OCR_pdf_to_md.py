#!/usr/bin/env python3
"""
DeepSeek OCR PDF to Markdown Converter - Windows Compatible
Converts PDF files to Markdown format using DeepSeek OCR model locally
"""

import os
import sys
import io
import re
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Fix Windows console encoding issues
if sys.platform == 'win32':
    # Force UTF-8 encoding for stdout/stderr on Windows
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import fitz  # PyMuPDF
from PIL import Image
import torch

# Configure CUDA if available
if torch.version.cuda == '11.8':
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda-11.8/bin/ptxas"
os.environ['VLLM_USE_V1'] = '0'

# Import DeepSeek OCR components
try:
    from vllm import LLM, SamplingParams
    from vllm.model_executor.models.registry import ModelRegistry
    from deepseek_ocr import DeepseekOCRForCausalLM
    from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
    from process.image_process import DeepseekOCRProcessor
    DEEPSEEK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: DeepSeek OCR dependencies not available: {e}")
    DEEPSEEK_AVAILABLE = False


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
        # Fallback to ASCII if UTF-8 fails
        print(message.encode('ascii', errors='replace').decode('ascii'))


class PDFToMarkdownConverter:
    """Convert PDF to Markdown using DeepSeek OCR"""

    def __init__(
        self,
        model_path: str,
        output_dir: str = "output",
        dpi: int = 144,
        max_concurrency: int = 1,
        crop_mode: bool = True
    ):
        """
        Initialize the PDF to Markdown converter

        Args:
            model_path: Path to DeepSeek OCR model
            output_dir: Directory for output files
            dpi: DPI for PDF to image conversion
            max_concurrency: Maximum concurrent processing
            crop_mode: Enable cropping mode for image processing
        """
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.dpi = dpi
        self.max_concurrency = max_concurrency
        self.crop_mode = crop_mode

        # Create images subdirectory
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)

        # Initialize model
        if DEEPSEEK_AVAILABLE:
            self._init_model()
        else:
            raise ImportError("DeepSeek OCR dependencies are not available")

    def _init_model(self):
        """Initialize the DeepSeek OCR model"""
        safe_print(f"{Colors.BLUE}Loading DeepSeek OCR model from: {self.model_path}{Colors.RESET}")

        # Register model
        ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

        # Initialize LLM
        self.llm = LLM(
            model=self.model_path,
            hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
            block_size=256,
            enforce_eager=False,
            trust_remote_code=True,
            max_model_len=8192,
            swap_space=0,
            max_num_seqs=self.max_concurrency,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            disable_mm_preprocessor_cache=True
        )

        # Configure sampling parameters
        logits_processors = [
            NoRepeatNGramLogitsProcessor(
                ngram_size=20,
                window_size=50,
                whitelist_token_ids={128821, 128822}
            )
        ]

        self.sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            logits_processors=logits_processors,
            skip_special_tokens=False,
            include_stop_str_in_output=True,
        )

        safe_print(f"{Colors.GREEN}{Colors.CHECK} Model loaded successfully{Colors.RESET}")

    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF to high-quality images

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PIL Image objects
        """
        safe_print(f"{Colors.YELLOW}Converting PDF to images (DPI: {self.dpi})...{Colors.RESET}")

        images = []
        pdf_document = fitz.open(pdf_path)

        zoom = self.dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)

            Image.MAX_IMAGE_PIXELS = None
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            images.append(img)

        pdf_document.close()
        safe_print(f"{Colors.GREEN}{Colors.CHECK} Converted {len(images)} pages to images{Colors.RESET}")
        return images

    def process_images(self, images: List[Image.Image], prompt: str) -> List[str]:
        """
        Process images with DeepSeek OCR

        Args:
            images: List of PIL images
            prompt: OCR prompt

        Returns:
            List of OCR results
        """
        safe_print(f"{Colors.BLUE}Processing {len(images)} images with DeepSeek OCR...{Colors.RESET}")

        # Prepare batch inputs
        batch_inputs = []
        processor = DeepseekOCRProcessor()

        for image in images:
            cache_item = {
                "prompt": prompt,
                "multi_modal_data": {
                    "image": processor.tokenize_with_images(
                        images=[image],
                        bos=True,
                        eos=True,
                        cropping=self.crop_mode
                    )
                },
            }
            batch_inputs.append(cache_item)

        # Run batch inference
        outputs_list = self.llm.generate(batch_inputs, sampling_params=self.sampling_params)

        # Extract results
        results = []
        for output in outputs_list:
            content = output.outputs[0].text

            # Handle end of sentence marker
            if '<|end_of_sentence|>' in content:
                content = content.replace('<|end_of_sentence|>', '')

            results.append(content)

        safe_print(f"{Colors.GREEN}{Colors.CHECK} Processed {len(results)} pages{Colors.RESET}")
        return results

    def extract_images_from_content(self, content: str, page_num: int) -> str:
        """
        Extract embedded images from OCR content

        Args:
            content: OCR result content
            page_num: Current page number

        Returns:
            Cleaned content with image references
        """
        # Pattern for image references
        pattern = r'(<\|ref\|>image<\|/ref\|><\|det\|>(.*?)<\|/det\|>)'
        matches = re.findall(pattern, content, re.DOTALL)

        # Replace image markers with markdown image syntax
        for idx, match in enumerate(matches):
            image_ref = f"![](images/{page_num}_{idx}.jpg)"
            content = content.replace(match[0], image_ref)

        return content

    def clean_content(self, content: str) -> str:
        """
        Clean OCR content by removing markers

        Args:
            content: Raw OCR content

        Returns:
            Cleaned content
        """
        # Remove all ref and det markers
        pattern = r'(<\|ref\|>.*?<\|/ref\|><\|det\|>.*?<\|/det\|>)'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Clean up LaTeX symbols
        content = content.replace('\\coloneqq', ':=')
        content = content.replace('\\eqqcolon', '=:')

        # Clean up excessive newlines
        content = content.replace('\n\n\n\n', '\n\n')
        content = content.replace('\n\n\n', '\n\n')

        return content.strip()

    def save_markdown_file(
        self,
        contents: str,
        pdf_name: str,
        auto_clean: bool = True
    ) -> str:
        """
        Save markdown content to file

        Args:
            contents: Markdown content
            pdf_name: Original PDF filename
            auto_clean: Whether to auto-clean the content

        Returns:
            Path to saved markdown file
        """
        # Generate output filename
        base_name = Path(pdf_name).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if auto_clean:
            output_filename = f"{base_name}_cleaned.md"
        else:
            output_filename = f"{base_name}_raw.md"

        output_path = self.output_dir / output_filename

        # Save with UTF-8 encoding
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(contents)

            safe_print(f"{Colors.GREEN}{Colors.CHECK} Saved markdown: {output_path}{Colors.RESET}")
            return str(output_path)

        except Exception as e:
            safe_print(f"{Colors.RED}{Colors.CROSS} Error saving file: {e}{Colors.RESET}")
            raise

    def convert(
        self,
        pdf_path: str,
        prompt: str = "<image>\n<|grounding|>Convert the document to markdown.",
        auto_clean: bool = True,
        save_raw: bool = False
    ) -> dict:
        """
        Convert PDF to Markdown

        Args:
            pdf_path: Path to PDF file
            prompt: OCR prompt
            auto_clean: Whether to clean the output
            save_raw: Whether to save raw OCR output

        Returns:
            Dictionary with conversion results
        """
        safe_print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        safe_print(f"{Colors.CYAN}Starting PDF to Markdown Conversion{Colors.RESET}")
        safe_print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
        safe_print(f"{Colors.INFO} Input PDF: {pdf_path}")
        safe_print(f"{Colors.INFO} Output directory: {self.output_dir}\n")

        # Convert PDF to images
        images = self.pdf_to_images(pdf_path)

        # Process with OCR
        ocr_results = self.process_images(images, prompt)

        # Build markdown content
        markdown_pages = []
        cleaned_pages = []

        for page_num, content in enumerate(ocr_results):
            # Extract images if any
            content_with_images = self.extract_images_from_content(content, page_num)

            # Add page separator
            page_content = f"{content_with_images}\n\n<--- Page {page_num + 1} --->\n\n"
            markdown_pages.append(page_content)

            # Cleaned version
            if auto_clean:
                cleaned_content = self.clean_content(content)
                cleaned_pages.append(f"{cleaned_content}\n\n<--- Page {page_num + 1} --->\n\n")

        # Combine all pages
        full_markdown = "".join(markdown_pages)
        full_cleaned = "".join(cleaned_pages) if auto_clean else full_markdown

        # Save files
        results = {}

        if save_raw:
            raw_path = self.save_markdown_file(full_markdown, pdf_path, auto_clean=False)
            results['raw_markdown'] = raw_path

        cleaned_path = self.save_markdown_file(full_cleaned, pdf_path, auto_clean=auto_clean)
        results['cleaned_markdown'] = cleaned_path
        results['total_pages'] = len(images)

        safe_print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")
        safe_print(f"{Colors.GREEN}Conversion completed successfully!{Colors.RESET}")
        safe_print(f"{Colors.GREEN}{'='*60}{Colors.RESET}\n")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Convert PDF to Markdown using DeepSeek OCR (Windows Compatible)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python DeepSeek_OCR_pdf_to_md.py --input document.pdf

  # Custom output directory
  python DeepSeek_OCR_pdf_to_md.py --input document.pdf --output ./my_output

  # Save both raw and cleaned versions
  python DeepSeek_OCR_pdf_to_md.py --input document.pdf --save-raw

  # Custom prompt
  python DeepSeek_OCR_pdf_to_md.py --input document.pdf --prompt "<image>\\n<|grounding|>Extract all text."
        """
    )

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input PDF file path'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory path (default: output)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=os.environ.get('MODEL_PATH', 'deepseek-ai/deepseek-ocr'),
        help='Path to DeepSeek OCR model (default: from MODEL_PATH env or deepseek-ai/deepseek-ocr)'
    )

    parser.add_argument(
        '--prompt',
        type=str,
        default='<image>\n<|grounding|>Convert the document to markdown.',
        help='Custom OCR prompt'
    )

    parser.add_argument(
        '--dpi',
        type=int,
        default=144,
        help='DPI for PDF to image conversion (default: 144)'
    )

    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Disable automatic cleaning of output'
    )

    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='Save raw OCR output in addition to cleaned version'
    )

    parser.add_argument(
        '--max-concurrency',
        type=int,
        default=1,
        help='Maximum concurrent processing (default: 1)'
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

        # Initialize converter
        converter = PDFToMarkdownConverter(
            model_path=args.model,
            output_dir=args.output,
            dpi=args.dpi,
            max_concurrency=args.max_concurrency
        )

        # Convert PDF
        results = converter.convert(
            pdf_path=args.input,
            prompt=args.prompt,
            auto_clean=not args.no_clean,
            save_raw=args.save_raw
        )

        # Print summary
        safe_print(f"\n{Colors.INFO} Summary:")
        safe_print(f"  - Total pages processed: {results['total_pages']}")
        safe_print(f"  - Output file: {results['cleaned_markdown']}")
        if 'raw_markdown' in results:
            safe_print(f"  - Raw output: {results['raw_markdown']}")

        safe_print(f"\n{Colors.GREEN}Status: COMPLETED{Colors.RESET}\n")

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
