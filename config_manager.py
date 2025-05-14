import os
import logging
import yaml
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Class to manage configuration loading and access.
    """
    
    def __init__(self, config_file: str):
        """
        Load configuration from file.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = {}
        
        # Load configuration
        self._load_config()
        
        # Override with environment variables
        self._apply_env_overrides()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            if not os.path.exists(self.config_file):
                logging.error(f"Configuration file not found: {self.config_file}")
                raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
            
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logging.info(f"Loaded configuration from {self.config_file}")
        
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            raise
    
    def _apply_env_overrides(self):
        """Override configuration with environment variables."""
        # Grocy API settings
        if 'GROCY_API_URL' in os.environ:
            self.config.setdefault('grocy', {})['api_url'] = os.environ['GROCY_API_URL']
        
        if 'GROCY_API_KEY' in os.environ:
            self.config.setdefault('grocy', {})['api_key'] = os.environ['GROCY_API_KEY']
        
        if 'APPEND_NEW_PRODUCT_TEXT' in os.environ:
            self.config.setdefault('grocy', {})['append_new_text'] = os.environ['APPEND_NEW_PRODUCT_TEXT']
        
        if 'PREPEND_NEW_PRODUCT_TEXT' in os.environ:
            self.config.setdefault('grocy', {})['prepend_new_text'] = os.environ['PREPEND_NEW_PRODUCT_TEXT']

        if 'DEFAULT_BEST_BEFORE_DAYS' in os.environ:
            self.config.setdefault('grocy', {})['default_best_before_days'] = os.environ['DEFAULT_BEST_BEFORE_DAYS']
        
        # Scanner settings
        if 'SCANNER_CONNECTION_TYPE' in os.environ:
            self.config.setdefault('scanner', {})['connection_type'] = os.environ['SCANNER_CONNECTION_TYPE']
        
        # Logging settings
        if 'LOG_LEVEL' in os.environ:
            self.config.setdefault('logging', {})['level'] = os.environ['LOG_LEVEL']
            
        # Scanner settings
        if 'TEST_MODE' in os.environ:
            test_mode = os.environ['TEST_MODE'].lower() == 'true'
            self.config.setdefault('scanner', {})['test_mode'] = test_mode
            logging.info(f"Test mode enabled: {test_mode}")
    
    def get_scanner_config(self) -> Dict[str, Any]:
        """
        Return scanner-specific configuration.
        
        Returns:
            Scanner configuration dictionary
        """
        return self.config.get('scanner', {})
    
    def get_grocy_config(self) -> Dict[str, Any]:
        """
        Return Grocy API configuration.
        
        Returns:
            Dictionary with api_url and api_key
        """
        grocy_config = self.config.get('grocy', {})
        
        # Ensure required fields are present
        if 'api_url' not in grocy_config:
            logging.error("Grocy API URL not configured")
            raise ValueError("Grocy API URL not configured")
        
        if 'api_key' not in grocy_config:
            logging.error("Grocy API key not configured")
            raise ValueError("Grocy API key not configured")
        
        return grocy_config
    
    def get_action_mappings(self) -> Dict[str, Any]:
        """
        Return mappings for barcode prefixes to actions.
        
        Returns:
            Action mappings dictionary
        """
        return self.config.get('actions', {})
    
    def get_feedback_config(self) -> Dict[str, Any]:
        """
        Return feedback configuration.
        
        Returns:
            Feedback configuration dictionary
        """
        return self.config.get('feedback', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Return logging configuration.
        
        Returns:
            Logging configuration dictionary
        """
        return self.config.get('logging', {})
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        Return the complete configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self.config
