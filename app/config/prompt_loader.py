import json
import os
from typing import Dict, List, Any
from pathlib import Path

class PromptLoader:
    """Utility class to load and cache prompt configurations from JSON files."""
    
    def __init__(self, config_path: str | None = None):
        if config_path is None:
            # Default to prompts.json in the same directory as this file
            current_dir = Path(__file__).parent
            config_path = str(current_dir / "prompts.json")
        
        self.config_path = Path(config_path)
        self._config_cache = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file with caching."""
        if self._config_cache is None:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in configuration file: {e}")
        
        return self._config_cache
    
    def get_system_prompt(self) -> str:
        """Get the system prompt from configuration."""
        config = self.load_config()
        return config.get("system_prompt", "")
    
    def get_conversation_examples(self) -> List[Dict[str, str]]:
        """Get conversation examples from configuration."""
        config = self.load_config()
        return config.get("conversation_examples", [])
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration from configuration."""
        config = self.load_config()
        return config.get("api_config", {})
    
    def build_messages(self, user_message: str) -> List[Dict[str, str]]:
        """Build the complete messages array for the API request."""
        messages = []
        
        # Add system prompt
        system_prompt = self.get_system_prompt()
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add conversation examples
        examples = self.get_conversation_examples()
        messages.extend(examples)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def reload_config(self):
        """Force reload of configuration (useful for development)."""
        self._config_cache = None
        return self.load_config()

# Global instance for easy access
prompt_loader = PromptLoader() 