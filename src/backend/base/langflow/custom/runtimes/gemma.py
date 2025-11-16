"""
Gemma Local Runtime - Optimized for Mac M1 with MPS acceleration.
Special handling for Gemma 2B and Gemma 7B models.
"""

from typing import Optional, Dict, Any, List
import asyncio
import logging
from .manager import ModelRuntime, ModelConfig, GenerationConfig, GenerationResult

logger = logging.getLogger(__name__)


class GemmaLocalRuntime(ModelRuntime):
    """
    Specialized runtime for Google Gemma models with Mac M1 optimization.
    
    Features:
    - Automatic MPS detection and fallback
    - Memory optimization for M1 (typically 8-16GB RAM)
    - Streaming support for real-time generation
    - Automatic quantization selection
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.device_type = None
        self.generation_kwargs = {}

    async def load(self) -> bool:
        """Load Gemma model with optimizations."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # Detect optimal device
            self.device_type = self._detect_device()
            logger.info(f"Loading {self.config.model_name} on device: {self.device_type}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_id,
                trust_remote_code=True,
                token=None,
            )
            
            # Set pad token if needed
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Determine torch dtype based on device and quantization
            torch_dtype = self._get_torch_dtype()
            
            # Model loading parameters
            model_kwargs = {
                "device_map": self.device_type,
                "torch_dtype": torch_dtype,
                "trust_remote_code": True,
            }
            
            # Add quantization if specified
            if self.config.quantization == "int8":
                model_kwargs["load_in_8bit"] = True
            elif self.config.quantization == "int4":
                model_kwargs["load_in_4bit"] = True
                model_kwargs["bnb_4bit_compute_dtype"] = torch_dtype
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_id,
                **model_kwargs,
            )
            
            # Move to eval mode
            self.model.eval()
            
            # Set generation defaults
            self._setup_generation_kwargs()
            
            self.is_loaded = True
            logger.info(f"Successfully loaded {self.config.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading Gemma model: {e}", exc_info=True)
            return False

    async def unload(self) -> None:
        """Unload model and free memory."""
        try:
            if self.model:
                import torch
                del self.model
                del self.tokenizer
                
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                
                self.is_loaded = False
                logger.info(f"Unloaded {self.config.model_name}")
        except Exception as e:
            logger.error(f"Error unloading model: {e}")

    async def generate(self, gen_config: GenerationConfig) -> GenerationResult:
        """Generate text with streaming support."""
        import time
        import torch
        
        if not self.is_loaded:
            raise RuntimeError(f"Model {self.config.model_name} not loaded")
        
        start_time = time.time()
        
        try:
            # Prepare inputs
            inputs = self.tokenizer(
                gen_config.prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048,
            ).to(self.model.device)
            
            # Generate with context manager to prevent gradient tracking
            with torch.no_grad():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=gen_config.max_tokens,
                    temperature=gen_config.temperature,
                    top_p=gen_config.top_p,
                    top_k=gen_config.top_k,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    **self.generation_kwargs,
                )
            
            # Decode output
            result_text = self.tokenizer.decode(
                output_ids[0],
                skip_special_tokens=True,
            )
            
            elapsed = time.time() - start_time
            tokens_generated = len(output_ids[0]) - len(inputs["input_ids"][0])
            
            return GenerationResult(
                text=result_text,
                model_name=self.config.model_name,
                tokens_generated=tokens_generated,
                execution_time=elapsed,
                metadata={
                    "device": str(self.device_type),
                    "quantization": self.config.quantization or "none",
                },
            )
            
        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check model health and memory usage."""
        try:
            import torch
            import psutil
            
            memory_info = self.get_memory_usage()
            
            health = {
                "status": "healthy" if self.is_loaded else "not_loaded",
                "model_name": self.config.model_name,
                "device": str(self.device_type) if self.device_type else "unknown",
                "memory_used_mb": memory_info["used_mb"],
                "memory_total_mb": memory_info["total_mb"],
            }
            
            # Add device-specific info
            if torch.cuda.is_available():
                health["gpu_memory_allocated"] = torch.cuda.memory_allocated() / 1024 / 1024
                health["gpu_memory_reserved"] = torch.cuda.memory_reserved() / 1024 / 1024
            
            return health
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "total_mb": memory_info.rss / 1024 / 1024,
                "used_mb": memory_info.rss / 1024 / 1024,
            }
        except Exception as e:
            logger.warning(f"Could not get memory usage: {e}")
            return {"total_mb": 0, "used_mb": 0}

    def _detect_device(self) -> str:
        """Detect optimal device for execution."""
        import torch
        
        try:
            # Check for MPS (Apple Silicon)
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                # MPS is available but might be unstable for some ops
                # Fall back to CPU if needed
                logger.info("MPS available - using GPU acceleration on Apple Silicon")
                return "mps"
        except Exception as e:
            logger.warning(f"MPS check failed: {e}")
        
        # Check for CUDA
        if torch.cuda.is_available():
            logger.info(f"CUDA available - using GPU: {torch.cuda.get_device_name(0)}")
            return "cuda"
        
        # Default to CPU
        logger.info("Using CPU")
        return "cpu"

    def _get_torch_dtype(self):
        """Get appropriate torch dtype based on device and model size."""
        import torch
        
        # For MPS and CPU, use bfloat16 or float32
        if self.device_type in ("mps", "cpu"):
            if "2b" in self.config.model_id.lower():
                return torch.float32  # Smaller models on CPU/MPS
            return torch.float16 if torch.cuda.is_available() else torch.float32
        
        # For CUDA, use bfloat16 if available
        if self.device_type == "cuda":
            return torch.bfloat16
        
        return torch.float32

    def _setup_generation_kwargs(self) -> None:
        """Setup additional generation parameters based on model."""
        # Gemma-specific optimizations
        if "2b" in self.config.model_id.lower():
            # Smaller model - lighter generation
            self.generation_kwargs = {
                "repetition_penalty": 1.1,
                "length_penalty": 1.0,
            }
        else:
            # Larger model - more sophisticated
            self.generation_kwargs = {
                "repetition_penalty": 1.05,
                "length_penalty": 0.95,
                "early_stopping": False,
            }


class GemmaStreamingRuntime(GemmaLocalRuntime):
    """
    Gemma runtime with streaming support for real-time generation.
    Yields tokens as they're generated.
    """

    async def generate_streaming(self, gen_config: GenerationConfig):
        """Generate text with streaming (yields tokens)."""
        import time
        import torch
        from transformers import TextIteratorStreamer
        from threading import Thread
        
        if not self.is_loaded:
            raise RuntimeError(f"Model {self.config.model_name} not loaded")
        
        start_time = time.time()
        
        try:
            # Prepare inputs
            inputs = self.tokenizer(
                gen_config.prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048,
            ).to(self.model.device)
            
            # Setup streamer
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
            )
            
            # Prepare generation kwargs
            generation_kwargs = dict(
                **inputs,
                max_new_tokens=gen_config.max_tokens,
                temperature=gen_config.temperature,
                top_p=gen_config.top_p,
                top_k=gen_config.top_k,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                streamer=streamer,
                **self.generation_kwargs,
            )
            
            # Run generation in thread
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Stream tokens
            full_text = ""
            for text in streamer:
                full_text += text
                yield text
            
            thread.join()
            elapsed = time.time() - start_time
            
            # Yield summary
            tokens_generated = len(self.tokenizer.encode(full_text))
            yield f"\n<!-- Generation complete: {tokens_generated} tokens in {elapsed:.2f}s -->"
            
        except Exception as e:
            logger.error(f"Streaming generation error: {e}", exc_info=True)
            raise
