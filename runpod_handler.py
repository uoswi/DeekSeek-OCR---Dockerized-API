import runpod
import base64
from io import BytesIO
from PIL import Image
import sys
import os

# Add DeepSeek-OCR to path
sys.path.insert(0, '/app/DeepSeek-OCR')

from transformers import AutoModel, AutoTokenizer
import torch

# Initialize model at startup
MODEL_PATH = os.environ.get("MODEL_PATH", "/app/models/DeepSeek-OCR")
print(f"Loading model from: {MODEL_PATH}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = AutoModel.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
    torch_dtype=torch.bfloat16
).cuda().eval()

print("Model loaded successfully!")

def handler(event):
    """
    RunPod handler for DeepSeek-OCR
    Expected input:
    {
        "input": {
            "image_base64": "base64_encoded_image",
            "prompt": "optional custom prompt"
        }
    }
    """
    try:
        input_data = event.get("input", {})
        image_base64 = input_data.get("image_base64")
        prompt = input_data.get("prompt", "<image>\n<|grounding|>Convert the document to markdown.")
        
        if not image_base64:
            return {"error": "No image_base64 provided"}
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        
        # Save image temporarily
        temp_path = "/tmp/temp_image.jpg"
        image.save(temp_path)
        
        # Process with DeepSeek-OCR
        result = model.infer(
            tokenizer,
            prompt=prompt,
            image_file=temp_path,
            output_path="/tmp",
            base_size=1024,
            image_size=640,
            crop_mode=True
        )
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
