import requests
import logging
from typing import Dict, List, Optional, Any

class GrocyClient:
    def __init__(self, config: Dict[str, Any]):
        """Initialize connection to Grocy API
        
        Args:
            api_url: Base URL for Grocy API (e.g., http://grocy:80/api)
            api_key: API key for authentication
        """
        self.config = config
        self.api_url = config.get('api_url')
        self.headers = {
            "GROCY-API-KEY": config.get('api_key'),
            "Content-Type": "application/json"
        }
        logging.debug(f"Initialized GrocyClient with API URL: {self.api_url}")

    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make a request to the Grocy API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., /stock/products/by-barcode/{barcode})
            data: Request data for POST/PUT requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Return response data if available
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Response: {e.response.text}")
            raise
    
    def get_product_by_barcode(self, barcode: str) -> Dict:
        """Look up product in Grocy by barcode
        
        Args:
            barcode: Barcode to look up
            
        Returns:
            Product data as dictionary
            
        Raises:
            ProductNotFoundException: If product is not found
        """
        try:
            result = self._make_request("GET", f"/stock/products/by-barcode/{barcode}")
            # Log the raw result for debugging
            logging.debug(f"Raw product lookup result: {result}")
            
            # Ensure we're returning a dictionary with the expected structure
            if isinstance(result, list):
                if len(result) > 0:
                    # Convert to expected dictionary format
                    return {"product": result[0]}
                else:
                    # Define ProductNotFoundException locally to avoid circular import
                    class ProductNotFoundException(Exception):
                        pass
                    raise ProductNotFoundException(f"Product not found for barcode: {barcode}")
            
            # If it's a dictionary but doesn't have the expected structure
            if isinstance(result, dict) and 'product' not in result:
                # Try to adapt the structure
                return {"product": result}
                
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "No product with barcode" in e.response.text:
                # Define ProductNotFoundException locally to avoid circular import
                class ProductNotFoundException(Exception):
                    pass
                raise ProductNotFoundException(f"Product not found for barcode: {barcode}")
            raise
    
    def external_lookup(self, barcode: str) -> Dict:
        """Look up product in Grocy by barcode
        
        Args:
            barcode: Barcode to look up
            
        Returns:
            Product data
            
        Raises:
            ProductNotFoundException: If product is not found
        """
        try:
            lookup = self._make_request("GET", f"/stock/barcodes/external-lookup/{barcode}")
            logging.debug(f"Response received for product lookup: {lookup}")
            return lookup
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and "No product with barcode" in e.response.text:
                # Define ProductNotFoundException locally to avoid circular import
                class ProductNotFoundException(Exception):
                    pass
                raise ProductNotFoundException(f"Product not found for barcode: {barcode}")
            raise
    
    def create_product(self, name: str, barcode: str, description: str = "", quantity_unit_id: int = 1, location_id: Optional[int] = None,
                      category_id: Optional[int] = None, shopping_location_id: Optional[int] = None) -> Dict:
        """Create a new product in Grocy
        
        Args:
            name: Product name
            barcode: Product barcode
            description: Product description
            quantity_unit_id: ID of quantity unit
            location_id: ID of location
            category_id: ID of category
            
        Returns:
            Created product data
        """
        # First create the product
        append_new_text = self.config.get('append_new_text', "")
        prepend_new_text = self.config.get('prepend_new_text', "")
        default_best_before_days = self.config.get('default_best_before_days', "")
        
        product_data = {
            "name": prepend_new_text + name + append_new_text,
            "description": description,
            "location_id": location_id,
            "qu_id_stock": quantity_unit_id,
            "qu_id_purchase": quantity_unit_id,
            # "qu_factor_purchase_to_stock": 1,
            "default_best_before_days" : default_best_before_days,
        }
        logging.debug(f"Product data for creation: {product_data}")

        if category_id:
            product_data["product_group_id"] = category_id

        if shopping_location_id:
            product_data["shopping_location_id"] = shopping_location_id
            
        product = self._make_request("POST", "/objects/products", product_data)
        logging.debug(f"Response received for product create: {product}")

        # Then associate the barcode with the product
        if barcode:
            barcode_data = {
                "product_id": product["created_object_id"],
                "barcode": barcode
            }
            self._make_request("POST", "/objects/product_barcodes", barcode_data)
            
        return product
    
    def add_to_shopping_list(self, product_id: int, quantity: float = 1, list_id: int = 1) -> Dict:
        """Add item to shopping list
        
        Args:
            product_id: ID of product to add
            quantity: Quantity to add
            list_id: ID of shopping list
            
        Returns:
            Created shopping list item data
        """
        data = {
            "product_id": product_id,
            "shopping_list_id": list_id,
            "amount": quantity
        }
        return self._make_request("POST", "/objects/shopping_list", data)
    
    def purchase_product(self, product_id: int, quantity: float = 1) -> Dict:
        """Mark product as purchased
        
        Args:
            product_id: ID of product to purchase
            quantity: Quantity to purchase
            
        Returns:
            Response data
        """
        data = {
            "amount": quantity,
            "transaction_type": "purchase"
        }
        return self._make_request("POST", f"/stock/products/{product_id}/add", data)
    
    def consume_product(self, product_id: int, quantity: float = 1) -> Dict:
        """Mark product as consumed
        
        Args:
            product_id: ID of product to consume
            quantity: Quantity to consume
            
        Returns:
            Response data
        """
        data = {
            "amount": quantity,
            "transaction_type": "consume",
            "spoiled": False
        }
        return self._make_request("POST", f"/stock/products/{product_id}/consume", data)
    
    def trash_product(self, product_id: int, quantity: float = 1) -> Dict:
        """Mark product as consumed, spoiled
        
        Args:
            product_id: ID of product to consume
            quantity: Quantity to consume
            
        Returns:
            Response data
        """
        data = {
            "amount": quantity,
            # "transaction_type": "consume",
            "spoiled": True
        }
        return self._make_request("POST", f"/stock/products/{product_id}/consume", data)
    
    
    def open_product(self, product_id: int, quantity: float = 1) -> Dict:
        """Mark product as consumed
        
        Args:
            product_id: ID of product to consume
            quantity: Quantity to consume
            
        Returns:
            Response data
        """
        data = {
            "amount": quantity,
        }
        return self._make_request("POST", f"/stock/products/{product_id}/open", data)
    
    def get_locations(self) -> List[Dict]:
        """Get all locations from Grocy
        
        Returns:
            List of locations
        """
        return self._make_request("GET", "/objects/locations")
    
    def get_categories(self) -> List[Dict]:
        """Get all product categories from Grocy
        
        Returns:
            List of categories
        """
        return self._make_request("GET", "/objects/product_groups")
    
    def get_quantity_units(self) -> List[Dict]:
        """Get all quantity units from Grocy
        
        Returns:
            List of quantity units
        """
        return self._make_request("GET", "/objects/quantity_units")
    
    def get_shopping_locations(self) -> List[Dict]:
        """Get all quantity units from Grocy
        
        Returns:
            List of quantity units
        """
        return self._make_request("GET", "/objects/shopping_locations")
    
    def get_location_by_id(self, item_id) -> Dict:
        """Get all locations from Grocy
        
        Returns:
            List of locations
        """
        return self._make_request("GET", "/objects/locations/"+item_id)
    
    def get_category_by_id(self, item_id) -> Dict:
        """Get all product categories from Grocy
        
        Returns:
            List of categories
        """
        return self._make_request("GET", "/objects/product_groups/"+item_id)
    
    def get_quantity_unit_by_id(self, item_id) -> Dict:
        """Get all quantity units from Grocy
        
        Returns:
            List of quantity units
        """
        return self._make_request("GET", "/objects/quantity_units/"+item_id)
    
    def get_shopping_location_by_id(self, item_id) -> Dict:
        """Get all quantity units from Grocy
        
        Returns:
            List of quantity units
        """
        return self._make_request("GET", "/objects/shopping_locations/"+item_id)
    
    def get_quantity_unit_conversions(self, item_id: int) -> List[Dict[str, Any]]:
        """Get quantity unit conversions for a product."""
        logging.info("/objects/quantity_unit_conversions?query[]product_id="+str(item_id))
        return self._make_request("GET", f"/objects/quantity_unit_conversions?query%5B%5D=product_id%3D{str(item_id)}")

        # try:
        #     response = requests.get(
        #         f"{self.api_url}/objects/quantity_unit_conversions", 
        #         headers=self.headers,
        #         params={"query[]": f"product_id={product_id}"}
        #     )
        #     response.raise_for_status()
        #     conversions = response.json()
        #     logger.debug(f"Quantity unit conversions for product {product_id}: {json.dumps(conversions, indent=2)}")
        #     return conversions
        # except Exception as e:
        #     logger.error(f"Failed to get quantity unit conversions for product {product_id}: {e}")
        #     return []