"""
Configuration Management Module
"""
import os
import yaml
from typing import Dict, Any

class Config:
    """Configuration Manager"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value with dot-separated path
        
        Args:
            key_path: Configuration path, e.g., "model.api_url"
            default: Default value
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
        
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration"""
        return self.config.get('model', {})
        
    def get_video_config(self) -> Dict[str, Any]:
        """Get video processing configuration"""
        return self.config.get('video', {})
        
    def get_image_config(self) -> Dict[str, Any]:
        """Get image processing configuration"""
        return self.config.get('image', {})
        
    def get_judgment_config(self) -> Dict[str, Any]:
        """Get judgment configuration"""
        return self.config.get('judgment', {})
        
    def get_output_dirs(self) -> Dict[str, str]:
        """Get output directory configuration"""
        return self.config.get('output_dirs', {})
        
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get('logging', {})
        
    def ensure_output_dirs(self, base_dir: str) -> Dict[str, str]:
        """
        Ensure output directories exist
        
        Args:
            base_dir: Base directory
            
        Returns:
            Dictionary of created directory paths
        """
        dirs = self.get_output_dirs()
        created_dirs = {}
        
        for name, subdir in dirs.items():
            dir_path = os.path.join(base_dir, subdir)
            os.makedirs(dir_path, exist_ok=True)
            created_dirs[name] = dir_path
            
        return created_dirs