import os
import torch
from app.core.config import settings

# Lazy loading of Transformers to keep import times low and prevent crashes if CUDA is absent
HAS_HF = False
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TextIteratorStreamer
    HAS_HF = True
except ImportError:
    pass

class ModelService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_id = settings.HF_MODEL_ID
        self.device = "cuda" if torch.cuda.is_available() and settings.USE_GPU else "cpu"
        
        # In actual test/dev, we will load on-demand to speed up server boot times
        self.loaded = False

    def load_model(self):
        if self.loaded:
            return
        if not HAS_HF:
            print("[Warning] Transformers or bitsandbytes is not installed. LLM Service will run in simulation mode.")
            self.loaded = True
            return

        try:
            print(f"Initializing local Hugging Face model: {self.model_id} on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            
            if self.device == "cuda" and settings.LOAD_IN_4BIT:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    quantization_config=quantization_config,
                    device_map="auto"
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    device_map="auto" if self.device == "cuda" else None
                )
                if self.device == "cpu":
                    self.model = self.model.to("cpu")
            
            self.loaded = True
            print("Hugging Face model loaded successfully!")
        except Exception as e:
            print(f"[Error] Failed to load Hugging Face model: {e}. Falling back to simulation.")
            self.loaded = True

    async def generate(self, prompt: str, max_new_tokens: int = 512) -> str:
        """
        Runs local inference on the loaded Hugging Face model.
        Falls back to mock answers if loading fails or model is in simulation mode.
        """
        self.load_model()
        
        if not self.model or not self.tokenizer:
            # Fallback mock execution
            return self._mock_response(prompt)

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.2,
                top_p=0.9
            )
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove prompt prefix
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):]
            return generated_text.strip()
        except Exception as e:
            print(f"HF Generation failed: {e}")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """
        Mock responses that resemble planning JSON structures for testing.
        """
        prompt_lower = prompt.lower()
        if "plan" in prompt_lower:
            return """
            [
              {"step": 1, "agent": "BROWSER", "action": "NAVIGATE", "details": {"url": "https://google.com"}, "description": "Go to Google"}
            ]
            """
        return "Task complete."

model_service = ModelService()
