import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import requests
from config_manager import ConfigManager

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grocy_client import GrocyClient


class TestGrocyClient(unittest.TestCase):
    """Test cases for the GrocyClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use patch to mock requests
        self.requests_patcher = patch('grocy_client.requests')
        self.mock_requests = self.requests_patcher.start()
        
        # Mock successful response for initialization
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'version': '1.0.0'}
        mock_response.content = b'{"version": "1.0.0"}'
        self.mock_requests.request.return_value = mock_response
        
        config_manager = ConfigManager(self.config_file)

        # Create client
        grocy_config = config_manager.get_grocy_config()

        self.client = GrocyClient(grocy_config)
        
        # Reset mock to clear initialization call
        self.mock_requests.reset_mock()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.requests_patcher.stop()
    
    def test_initialization(self):
        """Test client initialization."""
        # Re-create client to test initialization
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'version': '1.0.0'}
        mock_response.content = b'{"version": "1.0.0"}'
        self.mock_requests.request.return_value = mock_response
        
        client = GrocyClient('http://grocy-test.local/api', 'test-api-key')
        
        # Verify request was made with correct parameters
        self.mock_requests.request.assert_called_once_with(
            method='GET',
            url='http://grocy-test.local/api/system/info',
            headers={'GROCY-API-KEY': 'test-api-key', 'Content-Type': 'application/json'},
            params=None,
            json=None
        )
    
    def test_initialization_failure(self):
        """Test client initialization failure."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        self.mock_requests.request.return_value = mock_response
        
        # Verify initialization failure
        with self.assertRaises(requests.exceptions.HTTPError):
            GrocyClient('http://grocy-test.local/api', 'test-api-key')
    
    def test_get_product_by_barcode_found(self):
        """Test getting a product by barcode when it exists."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'product': {'id': 123, 'name': 'Test Product'}}
        mock_response.content = b'{"product": {"id": 123, "name": "Test Product"}}'
        self.mock_requests.request.return_value = mock_response
        
        # Call method
        result = self.client.get_product_by_barcode('12345')
        
        # Verify request was made with correct parameters
        self.mock_requests.request.assert_called_once_with(
            method='GET',
            url='http://grocy-test.local/api/stock/products/by-barcode/12345',
            headers={'GROCY-API-KEY': 'test-api-key', 'Content-Type': 'application/json'},
            params=None,
            json=None
        )
        
        # Verify result
        self.assertEqual(result['product']['id'], 123)
        self.assertEqual(result['product']['name'], 'Test Product')
    
    def test_get_product_by_barcode_not_found(self):
        """Test getting a product by barcode when it doesn't exist."""
        # Mock 400 response for barcode not found
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_response.status_code = 400
        self.mock_requests.request.return_value = mock_response
        self.mock_requests.exceptions.HTTPError = requests.exceptions.HTTPError
        
        # Call method
        result = self.client.get_product_by_barcode('12345')
        
        # Verify request was made with correct parameters
        self.mock_requests.request.assert_called_once_with(
            method='GET',
            url='http://grocy-test.local/api/stock/products/by-barcode/12345',
            headers={'GROCY-API-KEY': 'test-api-key', 'Content-Type': 'application/json'},
            params=None,
            json=None
        )
        
        # Verify result
        self.assertIsNone(result)
    
    def test_add_to_shopping_list(self):
        """Test adding a product to the shopping list."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'id': 456}
        mock_response.content = b'{"id": 456}'
        self.mock_requests.request.return_value = mock_response
        
        # Call method
        result = self.client.add_to_shopping_list(123, 2, 1)
        
        # Verify request was made with correct parameters
        self.mock_requests.request.assert_called_once_with(
            method='POST',
            url='http://grocy-test.local/api/stock/shoppinglist/add-product',
            headers={'GROCY-API-KEY': 'test-api-key', 'Content-Type': 'application/json'},
            params=None,
            json={'product_id': 123, 'product_amount': 2, 'shopping_list_id': 1}
        )
        
        # Verify result
        self.assertEqual(result['id'], 456)
    
    def test_purchase_product(self):
        """Test purchasing a product."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'id': 789}
        mock_response.content = b'{"id": 789}'
        self.mock_requests.request.return_value = mock_response
        
        # Call method
        result = self.client.purchase_product(123, 3)
        
        # Verify request was made with correct parameters
        self.mock_requests.request.assert_called_once_with(
            method='POST',
            url='http://grocy-test.local/api/stock/products/123/add',
            headers={'GROCY-API-KEY': 'test-api-key', 'Content-Type': 'application/json'},
            params=None,
            json={'amount': 3, 'transaction_type': 'purchase'}
        )
        
        # Verify result
        self.assertEqual(result['id'], 789)
    
    def test_consume_product(self):
        """Test consuming a product."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'id': 321}
        mock_response.content = b'{"id": 321}'
        self.mock_requests.request.return_value = mock_response
        
        # Call method
        result = self.client.consume_product(123, 1)
        
        # Verify request was made with correct parameters
        self.mock_requests.request.assert_called_once_with(
            method='POST',
            url='http://grocy-test.local/api/stock/products/123/consume',
            headers={'GROCY-API-KEY': 'test-api-key', 'Content-Type': 'application/json'},
            params=None,
            json={'amount': 1, 'transaction_type': 'consume'}
        )
        
        # Verify result
        self.assertEqual(result['id'], 321)
    
    def test_get_stock_entries(self):
        """Test getting stock entries."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{'product_id': 123, 'amount': 5}]
        mock_response.content = b'[{"product_id": 123, "amount": 5}]'
        self.mock_requests.request.return_value = mock_response
        
        # Call method
        result = self.client.get_stock_entries()
        
        # Verify request was made with correct parameters
        self.mock_requests.request.assert_called_once_with(
            method='GET',
            url='http://grocy-test.local/api/stock',
            headers={'GROCY-API-KEY': 'test-api-key', 'Content-Type': 'application/json'},
            params=None,
            json=None
        )
        
        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['product_id'], 123)
        self.assertEqual(result[0]['amount'], 5)


if __name__ == '__main__':
    unittest.main()
