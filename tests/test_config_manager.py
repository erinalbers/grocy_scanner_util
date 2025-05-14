import unittest
from unittest.mock import patch, mock_open
import sys
import os
import yaml

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for the ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample configuration
        self.sample_config = {
            'scanner': {
                'connection_type': 'usb_hid',
                'usb_hid': {
                    'device_path': '/dev/input/event0'
                }
            },
            'grocy': {
                'api_url': 'http://grocy-test.local/api',
                'api_key': 'test-api-key'
            },
            'actions': {
                'default': 'lookup',
                'prefixes': {
                    'C-': 'consume',
                    'P-': 'purchase'
                }
            },
            'feedback': {
                'audio': True,
                'visual': False
            },
            'logging': {
                'level': 'INFO',
                'file': '/app/logs/barcode_scanner.log'
            }
        }
        
        # Convert to YAML for mock file
        self.sample_yaml = yaml.dump(self.sample_config)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config(self, mock_file, mock_exists):
        """Test loading configuration from file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.sample_yaml
        
        # Create config manager
        config_manager = ConfigManager('/app/config/config.yml')
        
        # Verify file was opened
        mock_file.assert_called_once_with('/app/config/config.yml', 'r')
        
        # Verify config was loaded correctly
        self.assertEqual(config_manager.get_scanner_config()['connection_type'], 'usb_hid')
        self.assertEqual(config_manager.get_grocy_config()['api_url'], 'http://grocy-test.local/api')
        self.assertEqual(config_manager.get_grocy_config()['api_key'], 'test-api-key')
        self.assertEqual(config_manager.get_action_mappings()['default'], 'lookup')
        self.assertEqual(config_manager.get_feedback_config()['audio'], True)
        self.assertEqual(config_manager.get_logging_config()['level'], 'INFO')
    
    @patch('os.path.exists')
    def test_file_not_found(self, mock_exists):
        """Test handling of missing configuration file."""
        # Setup mock
        mock_exists.return_value = False
        
        # Verify exception is raised
        with self.assertRaises(FileNotFoundError):
            ConfigManager('/app/config/nonexistent.yml')
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch.dict('os.environ', {
        'GROCY_API_URL': 'http://grocy-override.local/api',
        'GROCY_API_KEY': 'override-api-key',
        'SCANNER_CONNECTION_TYPE': 'bluetooth_hid',
        'LOG_LEVEL': 'DEBUG'
    })
    def test_env_overrides(self, mock_file, mock_exists):
        """Test environment variable overrides."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.sample_yaml
        
        # Create config manager
        config_manager = ConfigManager('/app/config/config.yml')
        
        # Verify environment variables override file config
        self.assertEqual(config_manager.get_scanner_config()['connection_type'], 'bluetooth_hid')
        self.assertEqual(config_manager.get_grocy_config()['api_url'], 'http://grocy-override.local/api')
        self.assertEqual(config_manager.get_grocy_config()['api_key'], 'override-api-key')
        self.assertEqual(config_manager.get_logging_config()['level'], 'DEBUG')
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_missing_grocy_config(self, mock_file, mock_exists):
        """Test handling of missing Grocy configuration."""
        # Setup mocks
        mock_exists.return_value = True
        
        # Create config with missing Grocy API URL
        incomplete_config = self.sample_config.copy()
        del incomplete_config['grocy']['api_url']
        mock_file.return_value.read.return_value = yaml.dump(incomplete_config)
        
        # Create config manager and verify exception
        config_manager = ConfigManager('/app/config/config.yml')
        with self.assertRaises(ValueError):
            config_manager.get_grocy_config()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_full_config(self, mock_file, mock_exists):
        """Test getting the full configuration."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.sample_yaml
        
        # Create config manager
        config_manager = ConfigManager('/app/config/config.yml')
        
        # Verify full config
        full_config = config_manager.get_full_config()
        self.assertEqual(full_config['scanner']['connection_type'], 'usb_hid')
        self.assertEqual(full_config['grocy']['api_url'], 'http://grocy-test.local/api')
        self.assertEqual(full_config['actions']['default'], 'lookup')


if __name__ == '__main__':
    unittest.main()
