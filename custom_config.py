# Custom configuration for DeepSeek-OCR vLLM
# This file replaces the original config.py during Docker build
# Modify the PROMPT value below to change the default prompt used by the OCR service

# TODO: change modes
# Tiny: base_size = 512, image_size = 512, crop_mode = False
# Small: base_size = 640, image_size = 640, crop_mode = False
# Base: base_size = 1024, image_size = 1024, crop_mode = False
# Large: base_size = 1280, image_size = 1280, crop_mode = False
# Gundam: base_size = 1024, image_size = 640, crop_mode = True

BASE_SIZE = 1280
IMAGE_SIZE = 1280
CROP_MODE = False
MIN_CROPS= 2
MAX_CROPS= 9 # max:9; Increased for better chart/graph recognition
MAX_CONCURRENCY = 100 # If you have limited GPU memory, lower the concurrency count.
NUM_WORKERS = 64 # image pre-process (resize/padding) workers 
PRINT_NUM_VIS_TOKENS = False
SKIP_REPEAT = True
MODEL_PATH = 'deepseek-ai/DeepSeek-OCR' # change to your model path

# TODO: change INPUT_PATH
# .pdf: run_dpsk_ocr_pdf.py; 
# .jpg, .png, .jpeg: run_dpsk_ocr_image.py; 
# Omnidocbench images path: run_dpsk_ocr_eval_batch.py

INPUT_PATH = '' 
OUTPUT_PATH = ''

# CUSTOMIZABLE PROMPT - Modify this line to change the default prompt
# The API will still accept custom prompts via the prompt parameter
PROMPT = """<image>
<|grounding|>Convert this document to markdown with the following requirements:
1. For charts, graphs, flowcharts, and diagrams: Describe the visual structure and extract all visible data points, labels, and values
2. For tables: Preserve exact numerical values as shown. Use empty cells or 'N/A' where no data exists. Do not calculate or infer missing values
3. For pie charts: List all segments with their labels and percentages
4. Maintain document structure including headings, lists, and paragraphs
5. Extract all text content accurately including titles, captions, and annotations"""
# PROMPT = '<image>\nFree OCR.'
# TODO commonly used prompts
# document: <image>\n<|grounding|>Convert the document to markdown.
# other image: <image>\n<|grounding|>OCR this image.
# without layouts: <image>\nFree OCR.
# figures in document: <image>\nParse the figure.
# general: <image>\nDescribe this image in detail.
# rec: <image>\nLocate <|ref|>xxxx<|/ref|> in the image.
# '先天下之忧而忧'
# .......

from transformers import AutoTokenizer

TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)