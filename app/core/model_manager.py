import os
from typing import Dict, Optional
from langchain_community.chat_models import ChatLlamaCpp


class ModelManager:
    def __init__(
        self,
        models_dir: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        temperature: float = 0.1,
        verbose: bool = False,
    ):
        self.models_dir = os.path.abspath(models_dir)
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.temperature = temperature
        self.verbose = verbose

        # cache: model_path -> ChatLlamaCpp instance
        self._cache: Dict[str, ChatLlamaCpp] = {}

        if not os.path.isdir(self.models_dir):
            raise ValueError(f"models_dir does not exist or is not a directory: {self.models_dir}")

    def list_available_models(self):
        """Scans the folder for .gguf files."""
        return sorted([f for f in os.listdir(self.models_dir) if f.lower().endswith(".gguf")])

    def _resolve_model_path(self, model_ref: str) -> str:
        """
        model_ref can be:
        - a filename in models_dir (e.g., 'qwen.gguf')
        - an absolute or relative path to a .gguf file
        """
        # If it's already a path to a file, use it
        candidate = os.path.abspath(model_ref)
        if os.path.isfile(candidate) and candidate.lower().endswith(".gguf"):
            return candidate

        # Otherwise treat it as a filename inside models_dir
        candidate = os.path.join(self.models_dir, model_ref)
        candidate = os.path.abspath(candidate)
        if not (os.path.isfile(candidate) and candidate.lower().endswith(".gguf")):
            raise FileNotFoundError(f"GGUF model not found: {model_ref} (resolved: {candidate})")

        return candidate

    def load_model(self, model_ref: str, force_reload: bool = False) -> ChatLlamaCpp:
        """Loads (or reuses) a GGUF model with optimized settings."""
        model_path = self._resolve_model_path(model_ref)

        if not force_reload and model_path in self._cache:
            return self._cache[model_path]

        llm = ChatLlamaCpp(
            model_path=model_path,
            n_ctx=self.n_ctx,
            n_gpu_layers=self.n_gpu_layers,  # safer default; can be overridden
            temperature=self.temperature,
            verbose=self.verbose,
            streaming=False,  # safer for structured outputs in API mode
        )

        self._cache[model_path] = llm
        return llm
