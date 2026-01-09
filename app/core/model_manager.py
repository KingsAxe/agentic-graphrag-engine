import os
from langchain_community.chat_models import ChatLlamaCpp

class ModelManager:
    def __init__(self, models_dir: str):
        self.models_dir = models_dir

    def list_available_models(self):
        """Scans the folder for .gguf files."""
        return [f for f in os.listdir(self.models_dir) if f.endswith(".gguf")]

    def load_model(self, model_filename: str):
        """Loads a specific GGUF model with optimized settings."""
        model_path = os.path.join(self.models_dir, model_filename)
        
        # Performance tuning: 
        # n_gpu_layers=-1 offloads all to GPU if available.
        # n_ctx=4096 gives enough 'memory' for long PDF chunks.
        return ChatLlamaCpp(
            model_path=model_path,
            n_ctx=4096,
            n_gpu_layers=-1, 
            temperature=0.1,
            verbose=False,
            streaming=True
        )