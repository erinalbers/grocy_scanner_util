import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from barcode_processor import BarcodeProcessor


class TestBarcodeProcessor(unittest.TestCase):
    """Test cases for the BarcodeProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_grocy = MagicMock()
        self.config = {
            'actions': {
                'default': 'lookup',
                'prefixes': {
                    'C-': 'consume',
                    'P-': 'purchase',
                    'S-': 'shopping'
                }
            }
        }
        self.processor = BarcodeProcessor(self.mock_grocy, self.config)
        
        # Mock product data
        self.mock_product = {
            'product': {
                'id': 123,
                'name': 'Test Product'
            }
        }
    
    def test_determine_action(self):
        """Test determining action from barcode prefixes."""
        # Test consume prefix
        action, barcode = self.processor.determine_action('C-12345')
        self.assertEqual(action, 'consume')
        self.assertEqual(barcode, '12345')
        
        # Test purchase prefix
        action, barcode = self.processor.determine_action('P-12345')
        self.assertEqual(action, 'purchase')
        self.assertEqual(barcode, '12345')
        
        # Test shopping prefix
        action, barcode = self.processor.determine_action('S-12345')
        self.assertEqual(action, 'shopping')
        self.assertEqual(barcode, '12345')
        
        # Test default action (no prefix)
        action, barcode = self.processor.determine_action('12345')
        self.assertEqual(action, 'lookup')
        self.assertEqual(barcode, '12345')
    
    def test_process_barcode_product_not_found(self):
        """Test processing a barcode when product is not found."""
        # Mock grocy client to return None (product not found)
        self.mock_grocy.get_product_by_barcode.return_value = None
        
        # Process barcode
        result = self.processor.process_barcode('12345')
        
        # Verify grocy client was called
        self.mock_grocy.get_product_by_barcode.assert_called_once_with('12345')
        
        # Verify result
        self.assertEqual(result['barcode'], '12345')
        self.assertEqual(result['clean_barcode'], '12345')
        self.assertEqual(result['action'], 'lookup')
        self.assertIsNone(result['product'])
        self.assertFalse(result['result']['success'])
        self.assertIn('Product not found', result['result']['message'])
    
    def test_process_barcode_consume(self):
        """Test processing a consume action barcode."""
        # Mock grocy client to return a product
        self.mock_grocy.get_product_by_barcode.return_value = self.mock_product
        self.mock_grocy.consume_product.return_value = {'success': True}
        
        # Process barcode with consume prefix
        result = self.processor.process_barcode('C-12345')
        
        # Verify grocy client was called correctly
        self.mock_grocy.get_product_by_barcode.assert_called_once_with('12345')
        self.mock_grocy.consume_product.assert_called_once_with(123, 1)
        
        # Verify result
        self.assertEqual(result['barcode'], 'C-12345')
        self.assertEqual(result['clean_barcode'], '12345')
        self.assertEqual(result['action'], 'consume')
        self.assertEqual(result['product'], self.mock_product)
        self.assertTrue(result['result']['success'])
        self.assertIn('Consumed', result['result']['message'])
    
    def test_process_barcode_purchase(self):
        """Test processing a purchase action barcode."""
        # Mock grocy client to return a product
        self.mock_grocy.get_product_by_barcode.return_value = self.mock_product
        self.mock_grocy.purchase_product.return_value = {'success': True}
        
        # Process barcode with purchase prefix
        result = self.processor.process_barcode('P-12345')
        
        # Verify grocy client was called correctly
        self.mock_grocy.get_product_by_barcode.assert_called_once_with('12345')
        self.mock_grocy.purchase_product.assert_called_once_with(123, 1)
        
        # Verify result
        self.assertEqual(result['barcode'], 'P-12345')
        self.assertEqual(result['clean_barcode'], '12345')
        self.assertEqual(result['action'], 'purchase')
        self.assertEqual(result['product'], self.mock_product)
        self.assertTrue(result['result']['success'])
        self.assertIn('Purchased', result['result']['message'])
    
    def test_process_barcode_shopping(self):
        """Test processing a shopping list action barcode."""
        # Mock grocy client to return a product
        self.mock_grocy.get_product_by_barcode.return_value = self.mock_product
        self.mock_grocy.add_to_shopping_list.return_value = {'success': True}
        
        # Process barcode with shopping prefix
        result = self.processor.process_barcode('S-12345')
        
        # Verify grocy client was called correctly
        self.mock_grocy.get_product_by_barcode.assert_called_once_with('12345')
        self.mock_grocy.add_to_shopping_list.assert_called_once_with(123, 1)
        
        # Verify result
        self.assertEqual(result['barcode'], 'S-12345')
        self.assertEqual(result['clean_barcode'], '12345')
        self.assertEqual(result['action'], 'shopping')
        self.assertEqual(result['product'], self.mock_product)
        self.assertTrue(result['result']['success'])
        self.assertIn('Added', result['result']['message'])
    
    def test_execute_action_unknown(self):
        """Test executing an unknown action."""
        # Execute unknown action
        result = self.processor.execute_action('unknown', '12345', self.mock_product)
        
        # Verify result
        self.assertFalse(result['success'])
        self.assertIn('Unknown action', result['message'])
    
    def test_execute_action_exception(self):
        """Test handling exceptions during action execution."""
        # Mock grocy client to raise an exception
        self.mock_grocy.consume_product.side_effect = Exception("API Error")
        
        # Execute action that will raise exception
        result = self.processor.execute_action('consume', '12345', self.mock_product)
        
        # Verify result
        self.assertFalse(result['success'])
        self.assertIn('Error', result['message'])


if __name__ == '__main__':
    unittest.main()
