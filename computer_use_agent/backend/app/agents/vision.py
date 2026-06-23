import base64
import os
import cv2
import numpy as np
import httpx
from PIL import Image
from app.core.config import settings

class VisionAgent:
    def __init__(self):
        self.screenshots_dir = settings.SCREENSHOTS_DIR
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Pytesseract setup check
        try:
            import pytesseract
            self.ocr_available = True
        except ImportError:
            self.ocr_available = False

    async def analyze_screenshot(self, screenshot_path: str, prompt: str) -> dict:
        """
        Sends the screenshot to a local Vision-Language Model (VLM) via Ollama
        to locate elements, detect layouts, or confirm success/error overlays.
        """
        if not os.path.exists(screenshot_path):
            return {"error": f"Screenshot file not found at {screenshot_path}"}
            
        try:
            # Base64 encode image
            with open(screenshot_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                
            # Send to local Ollama Vision endpoint
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_VISION_MODEL,
                        "prompt": prompt,
                        "images": [encoded_image],
                        "stream": False,
                        "format": "json"
                    }
                )
                
                if response.status_code == 200:
                    import json
                    result = response.json()
                    try:
                        return json.loads(result.get("response", "{}"))
                    except json.JSONDecodeError:
                        return {"raw_response": result.get("response")}
                else:
                    return {"error": f"Ollama VLM returned status code {response.status_code}"}
        except Exception as e:
            # Graceful fallback: VLM not active
            return {
                "warning": "Local VLM offline. Using standard OCR fallback.",
                "fallback_active": True,
                "error_details": str(e)
            }

    def run_ocr(self, screenshot_path: str) -> dict:
        """
        Performs optical character recognition on a local image file.
        Returns extracted text items and their approximate pixel bounding boxes.
        """
        if not os.path.exists(screenshot_path):
            return {"error": "Image path not found."}
            
        if not self.ocr_available:
            return {"warning": "Tesseract OCR python wrapper not installed. Fallback to raw DOM search."}

        try:
            import pytesseract
            image = Image.open(screenshot_path)
            # Perform OCR with detailed word positions
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            ocr_results = []
            n_boxes = len(data['level'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text:
                    ocr_results.append({
                        "text": text,
                        "x": data['left'][i],
                        "y": data['top'][i],
                        "w": data['width'][i],
                        "h": data['height'][i]
                    })
            return {"words": ocr_results, "text": pytesseract.image_to_string(image)}
        except Exception as e:
            return {"error": f"OCR failed: {str(e)}"}

    def draw_detections(self, screenshot_path: str, detections: list, output_filename: str) -> str:
        """
        Annotates screenshots with bounding boxes for dashboard visualization.
        """
        try:
            img = cv2.imread(screenshot_path)
            for det in detections:
                x, y, w, h = det.get('x', 0), det.get('y', 0), det.get('w', 0), det.get('h', 0)
                label = det.get('label', 'element')
                
                # Draw bounding box (White outline, black drop shadow)
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), 3)
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 1.5)
                
                # Draw text background
                cv2.putText(img, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                
            out_path = os.path.join(self.screenshots_dir, output_filename)
            cv2.imwrite(out_path, img)
            return out_path
        except Exception as e:
            print(f"Error drawing annotations: {e}")
            return screenshot_path

vision_agent = VisionAgent()
