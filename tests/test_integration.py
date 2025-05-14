import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies
sys.modules['evdev'] = MagicMock()
sys.modules['pygame'] = MagicMock()

from config_manager import ConfigManager
from barcode_scanner import BarcodeScanner
from grocy_client import GrocyClient
from barcode_processor import BarcodeProcessor
from feedback_manager import FeedbackManager
from main import BarcodeApp


class TestIntegration(unittest.TestCase):
    """Integration tests for the barcode scanner application."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample configuration
        self.config = {
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
                    'P-': 'purchase',
                    'S-': 'shopping'
                }
            },
            'feedback': {
                'audio': True,
                'visual': True
            },
            'logging': {
                'level': 'INFO',
                'file': '/app/logs/barcode_scanner.log'
            }
        }
        
        # Create temp config file
        self.config_file = '/tmp/barcode_test_config.yml'
        with open(self.config_file, 'w') as f:
            import yaml
            yaml.dump(self.config, f)
        
        # Setup patches
        self.patches = []
        
        # Patch ConfigManager to use our config
        config_patch = patch('config_manager.ConfigManager.get_full_config')
        mock_config = config_patch.start()
        mock_config.return_value = self.config
        self.patches.append(config_patch)
        
        # Patch GrocyClient to avoid API calls
        grocy_patch = patch('grocy_client.GrocyClient._make_request')
        mock_grocy = grocy_patch.start()
        mock_grocy.return_value = {'version': '1.0.0'}
        self.patches.append(grocy_patch)
        
        # Patch BarcodeScanner to avoid device access
        scanner_patch = patch('barcode_scanner.BarcodeScanner._init_usb_hid')
        mock_scanner = scanner_patch.start()
        self.patches.append(scanner_patch)
        
        # Patch FeedbackManager to avoid audio/visual output
        feedback_patch = patch('feedback_manager.FeedbackManager._init_audio')
        mock_feedback = feedback_patch.start()
        self.patches.append(feedback_patch)
        
        # Patch logging
        logging_patch = patch('logging.basicConfig')
        mock_logging = logging_patch.start()
        self.patches.append(logging_patch)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop all patches
        for p in self.patches:
            p.stop()
        
        # Remove temp config file
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    @patch('grocy_client.GrocyClient.get_product_by_barcode')
    @patch('grocy_client.GrocyClient.consume_product')
    def test_consume_workflow(self, mock_consume, mock_get_product):
        """Test the complete consume workflow."""
        # Setup mock product response
        mock_product = {
            'product': {
                'id': 123,
                'name': 'Test Product'
            }
        }
        mock_get_product.return_value = mock_product
        
        # Setup mock consume response
        mock_consume.return_value = {'success': True}
        
        # Create components
        config_manager = ConfigManager(self.config_file)
        grocy_client = GrocyClient('http://grocy-test.local/api', 'test-api-key')
        processor = BarcodeProcessor(grocy_client, config_manager.get_full_config())
        
        # Process a consume barcode
        result = processor.process_barcode('C-12345')
        
        # Verify product was looked up
        mock_get_product.assert_called_once_with('12345')
        
        # Verify product was consumed
        mock_consume.assert_called_once_with(123, 1)
        
        # Verify result
        self.assertEqual(result['barcode'], 'C-12345')
        self.assertEqual(result['clean_barcode'], '12345')
        self.assertEqual(result['action'], 'consume')
        self.assertEqual(result['product'], mock_product)
        self.assertTrue(result['result']['success'])
    
    @patch('grocy_client.GrocyClient.get_product_by_barcode')
    @patch('grocy_client.GrocyClient.purchase_product')
    def test_purchase_workflow(self, mock_purchase, mock_get_product):
        """Test the complete purchase workflow."""
        # Setup mock product response
        mock_product = {
            'product': {
                'id': 123,
                'name': 'Test Product'
            }
        }
        mock_get_product.return_value = mock_product
        
        # Setup mock purchase response
        mock_purchase.return_value = {'success': True}
        
        # Create components
        config_manager = ConfigManager(self.config_file)
        grocy_client = GrocyClient('http://grocy-test.local/api', 'test-api-key')
        processor = BarcodeProcessor(grocy_client, config_manager.get_full_config())
        
        # Process a purchase barcode
        result = processor.process_barcode('P-12345')
        
        # Verify product was looked up
        mock_get_product.assert_called_once_with('12345')
        
        # Verify product was purchased
        mock_purchase.assert_called_once_with(123, 1)
        
        # Verify result
        self.assertEqual(result['barcode'], 'P-12345')
        self.assertEqual(result['clean_barcode'], '12345')
        self.assertEqual(result['action'], 'purchase')
        self.assertEqual(result['product'], mock_product)
        self.assertTrue(result['result']['success'])
    
    @patch('grocy_client.GrocyClient.get_product_by_barcode')
    def test_product_not_found(self, mock_get_product):
        """Test handling of product not found."""
        # Setup mock product response (not found)
        mock_get_product.return_value = None
        
        # Create components
        config_manager = ConfigManager(self.config_file)
        grocy_client = GrocyClient('http://grocy-test.local/api', 'test-api-key')
        processor = BarcodeProcessor(grocy_client, config_manager.get_full_config())
        
        # Process a barcode
        result = processor.process_barcode('12345')
        
        # Verify product was looked up
        mock_get_product.assert_called_once_with('12345')
        
        # Verify result
        self.assertEqual(result['barcode'], '12345')
        self.assertEqual(result['clean_barcode'], '12345')
        self.assertEqual(result['action'], 'lookup')
        self.assertIsNone(result['product'])
        self.assertFalse(result['result']['success'])
        self.assertIn('Product not found', result['result']['message'])
    
    @patch('barcode_scanner.BarcodeScanner.start_listening')
    @patch('barcode_scanner.BarcodeScanner.register_callback')
    @patch('signal.pause')
    def test_app_initialization(self, mock_pause, mock_register, mock_start):
        """Test application initialization and run."""
        # Create app
        app = BarcodeApp(self.config_file)
        
        # Run app
        app.run()
        
        # Verify scanner was started
        mock_register.assert_called_once()
        mock_start.assert_called_once()
        mock_pause.assert_called_once()
    
    @patch('barcode_scanner.BarcodeScanner.start_listening')
    @patch('barcode_scanner.BarcodeScanner.register_callback')
    @patch('grocy_client.GrocyClient.get_product_by_barcode')
    @patch('feedback_manager.FeedbackManager.success')
    @patch('feedback_manager.FeedbackManager.waiting')
    def test_barcode_callback(self, mock_waiting, mock_success, mock_get_product, mock_register, mock_start):
        """Test the barcode callback flow."""
        # Setup mock product response
        mock_product = {
            'product': {
                'id': 123,
                'name': 'Test Product'
            }
        }
        mock_get_product.return_value = mock_product
        
        # Create app
        app = BarcodeApp(self.config_file)
        
        # Capture the callback function
        callback_func = mock_register.call_args[0][0]
        
        # Call the callback with a barcode
        callback_func('12345')
        
        # Verify feedback and product lookup
        mock_waiting.assert_called_once()
        mock_get_product.assert_called_once_with('12345')
        mock_success.assert_called_once()


if __name__ == '__main__':
    unittest.main()
