import runpod
import base64
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
import sys
import os

# Add DeepSeek-OCR to path
sys.path.insert(0, '/app/DeepSeek-OCR-master/DeepSeek-OCR-vllm')

from pdf2markdown import DeepSeekOCRProcessor
from config import MODEL_PATH

# Initialize processor
processor = DeepSeekOCRProcessor(model_path=MODEL_PATH)

def handler(event):
    """
    RunPod handler for DeepSeek-OCR
    Expected input:
    {
        "input": {
            "file_base64": "base64_encoded_pdf_or_image",
            "file_type": "pdf" or "image",
            "prompt": "optional custom prompt"
        }
    }
    """
    try:
        input_data = event.get("input", {})
        file_base64 = input_data.get("file_base64")
        file_type = input_data.get("file_type", "pdf")
        custom_prompt = input_data.get("prompt", None)
        
        if not file_base64:
            return {"error": "No file_base64 provided"}
        
        # Decode base64 file
        file_bytes = base64.b64decode(file_base64)
        
        if file_type == "pdf":
            # Process PDF
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            results = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                pix = page.get_pixmap(dpi=144)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Process with custom or default prompt
                if custom_prompt:
                    result = processor.process_image(img, prompt=custom_prompt)
                else:
                    result = processor.process_markdown(img)
                
                results.append({
                    "page": page_num + 1,
                    "content": result
                })
            
            pdf_document.close()
            
            return {
                "success": True,
                "results": results,
                "total_pages": len(results)
            }
        
        else:  # image
            img = Image.open(BytesIO(file_bytes))
            
            if custom_prompt:
                result = processor.process_image(img, prompt=custom_prompt)
            else:
                result = processor.process_markdown(img)
            
            return {
                "success": True,
                "result": result
            }
    
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
