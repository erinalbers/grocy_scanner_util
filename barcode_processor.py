import logging
from typing import Dict, Any, Optional

class BarcodeProcessor:
    def __init__(self, grocy_client, feedback_manager, config):
        """Initialize with dependencies
        
        Args:
            grocy_client: GrocyClient instance
            feedback_manager: FeedbackManager instance
            config: Configuration dictionary
        """
        self.grocy_client = grocy_client
        self.feedback_manager = feedback_manager
        self.config = config
        self.action_mappings = config.get('action_mappings', {})
        self.default_action = config.get('default_action', 'consume')
        self.store = False
        self.quantity = False
        self.group = False
        self.location = False
        
        # Add mode switching support
        self.current_mode = self.default_action
        # Define special barcodes for mode switching
        self.mode_barcodes = {
            'consume': 'consume',
            'finish': 'finish',
            'purchase': 'purchase',
            'shopping': 'shopping',
            'create': 'create',
            'open': 'open',
            'expire': 'expire',
            'clear-scanner' : 'clear-scanner',
        }

    def clear_scanner(self):
        """Clear the scanner by resetting all attributes"""
        self.store = False
        self.location = False
        self.quantity = False
        self.group = False
        self.current_mode = self.default_action

    def get_barcode_attributes(self, barcode: str) -> Dict[str, Any]:
        """Get barcode attributes from the configuration

        Args:
            barcode: The scanned barcode

        Returns:
            Dictionary with barcode attributes
        """
        attributes_updated = False
        mode_changed = False

        attributes = barcode.split('/')
        for attribute in attributes:
                    # Check if this is a mode-switching barcode
            if attribute.lower() in self.mode_barcodes:
                self.current_mode = self.mode_barcodes[attribute.lower()]
                self.feedback_manager.success(f"Mode changed to: {self.current_mode}")
                mode_changed = True
                    
            parts = attribute.split('-',1)
            logging.debug(f"Split into parts: {parts}")

            if len(parts) == 2:
                part_type, part_id = parts
                # Check if the part_id is a valid integer
                if(part_type.upper() == 'ST'):
                    self.store = part_id
                    self.feedback_manager.success(f"Store changed to: {self.store}")
                    attributes_updated = True
                if(part_type.upper() == 'LC'):
                    self.location = part_id
                    self.feedback_manager.success(f"Location changed to: {self.location}")
                    attributes_updated = True
                if(part_type.upper() == 'QT'):
                    self.quantity = part_id
                    self.feedback_manager.success(f"Quantity changed to: {self.quantity}")
                    attributes_updated = True
                if(part_type.upper() == 'GRP'):
                    self.group = part_id
                    self.feedback_manager.success(f"Group changed to: {self.group}")
                    attributes_updated = True

        updated = {
            "group": self.group,
            "quantity": self.quantity,
            "location": self.location,
            "store": self.store,
            "attributes_updated" : attributes_updated,
            "mode_changed" : mode_changed,
            "mode" : self.current_mode,
        }
        logging.info(f"Attributes and modes: {updated}")

        return updated

    def process_barcode(self, barcode: str) -> Dict[str, Any]:
        """Main method to handle a scanned barcode
        
        Args:
            barcode: The scanned barcode
            
        Returns:
            Dictionary with processing results
            
        Raises:
            ProductNotFoundException: If product is not found and can't be handled
        """
        logging.info(f"Processing barcode: {barcode}")
        
        attributes = self.get_barcode_attributes(barcode)
        logging.debug(f"Current Product Attributes: {attributes}")

        if(barcode == 'clear-scanner'):
            self.clear_scanner()
            self.feedback_manager.success(f"Scanner cleared")
            return {
                "action": "clear-scanner",
                "result": {"success": True, "message": f"Scanner cleared"}
            }

        if(attributes['mode_changed'] and attributes['attributes_updated']):
            self.feedback_manager.attributes_updated(f"Mode changed to {self.current_mode}; ", attributes)
            return {
                "action": "mode_attribute_change",
                "mode": self.current_mode,
                "attributes": attributes,
                "result": {"success": True, "message": f"Mode changed to {self.current_mode}; Attributes updated to {attributes}"}
            }
        elif(attributes['mode_changed']):
            self.feedback_manager.success(f"Mode changed to: {self.current_mode}")
            return {
                "action": "mode_change",
                "mode": self.current_mode,
                "result": {"success": True, "message": f"Mode changed to {self.current_mode}"}
            }
        elif(attributes['attributes_updated']):
            self.feedback_manager.attributes_updated("",attributes)
            return {
                "action": "attributes_updated",
                "attributes": attributes,
                "result": {"success": True, "message": f"Attributes updated to {attributes}"}
            }
        
        # For regular barcodes, use the current mode
        actual_barcode = barcode
        action = self.current_mode
        
        try:
            try:
                product = self.grocy_client.get_product_by_barcode(actual_barcode)
                product_exists = True
                logging.debug(f"Product lookup result: {product}")

            except Exception as lookup_error:
                # If this is a "product not found" type of error, handle it gracefully
                product = None
                product_exists = False
                # Only log the error, don't raise it yet
                logging.debug(f"Product lookup failed: {str(lookup_error)}")
            
            # Handle CREATE mode specially
            if action == 'create':
                if not product_exists:
                    # Return info that this needs to go to product creation
                    self.feedback_manager.waiting(f"Creating new product with barcode: {actual_barcode}")
                    result = self.execute_barcode_action(action, actual_barcode)

                    return {
                        "action": "create",
                        "barcode": actual_barcode,
                        "result": {"success": True, "message": f"Ready to create product with barcode: {actual_barcode}"}
                    }
                else:
                    # Product already exists, handle accordingly
                    self.feedback_manager.product_exists(f"Product already exists with barcode: {actual_barcode}")
                    return {
                        "action": "create",
                        "barcode": actual_barcode,
                        "result": {"success": False, "message": f"Product already exists with barcode: {actual_barcode}"}
                    }

            # For other modes, look up the product in Grocy
            if not product_exists:
                # Product not found and we're not in create mode
                error_msg = f"Product not found with that barcode. Please create the product first."
                self.feedback_manager.unknown_product(error_msg)
                return {
                    "action": action,
                    "barcode": actual_barcode,
                    "result": {"success": False, "message": error_msg}
                }
            
            # Check if product has the expected structure
            if not isinstance(product, dict):
                error_msg = f"Invalid product data structure for barcode: {actual_barcode}"
                self.feedback_manager.error(error_msg)
                return {
                    "action": action,
                    "barcode": actual_barcode,
                    "result": {"success": False, "message": error_msg}
                }
            
            # Handle different product data structures
            if 'product' in product and isinstance(product['product'], dict) and 'id' in product['product']:
                product_id = product['product']['id']
                product_data = product['product']

            elif isinstance(product, dict) and 'id' in product:
                product_id = product['id']
                product_data = product
            else:
                error_msg = f"Cannot find product ID in data structure for barcode: {actual_barcode}"
                self.feedback_manager.error(error_msg)
                logging.error(f"Missing product ID in structure: {product}")
                return {
                    "action": action,
                    "barcode": actual_barcode,
                    "result": {"success": False, "message": error_msg}
                }
            
            # Execute the action
            result = self.execute_product_action(action, barcode, product_id, product, 1)
            logging.debug(f"Execute product action result: {result}")

            # Ensure result is a dictionary before returning
            if not isinstance(result, dict):
                logging.warning(f"Converting non-dict result to dict: {result}")
                result = {"data": result, "success": True}
            
            # Ensure the result has a success key
            if "success" not in result:
                result["success"] = True

            return {
                "action": action,
                "product": product_data,
                "result": result
            }

                
        except Exception as e:
            # Let the exception propagate up to be handled by the API
            self.feedback_manager.error(str(e))
            raise

    
    def _parse_barcode(self, barcode: str) -> tuple:
        """Parse barcode to extract action prefix and actual barcode
        
        Args:
            barcode: The scanned barcode
            
        Returns:
            Tuple of (actual_barcode, action)
        """
        # Check for action prefixes
        for prefix, action in self.action_mappings.items():
            if barcode.startswith(prefix):
                return barcode[len(prefix):], action
        
        # No prefix found, use default action
        return barcode, self.default_action
    
    def determine_action(self, barcode: str, product: Optional[Dict] = None) -> str:
        """Determine what action to take based on barcode prefix or config
        
        Args:
            barcode: The scanned barcode
            product: Optional product data
            
        Returns:
            Action to take (consume, shopping, purchase)
        """
        # Extract action from barcode prefix
        for prefix, action in self.action_mappings.items():
            if barcode.startswith(prefix):
                return action
        
        # Use default action if no prefix matched
        return self.default_action
    
    def execute_barcode_action(self, action: str, barcode: str ) -> Dict:
        """Execute the determined action

        Args:
            action: Action to execute (create, external_lookup)
            barcode: Barcode of product to create

        Returns:
            Result of the action

        Raises:
            ValueError: If action is not supported
        """
        result = {}
        if action == 'create':
            result = self.grocy_client.external_lookup(barcode)
            if result:
                logging.debug(f"Looked up barcode ID: {barcode}")
                
                # Use self values if they exist, otherwise fall back to result values
                location = self.location if self.location is not False else result.get("location_id")
                quantity = self.quantity if self.quantity is not False else result.get("qu_id_stock")
                group = self.group if self.group is not False else result.get("product_group_id")
                store = self.store if self.store is not False else result.get("shopping_location_id")

                try:
                    product = self.grocy_client.create_product(result["name"], barcode, result["name"], quantity, location, group, store)
                    prod_id = product.get('created_object_id')
                    name = result.get("name")
                    self.feedback_manager.success(f"Created product ID: {prod_id} with name {name}")
                except Exception as e:
                    logging.error(f"Error in external lookup product creation: {e}")

        else:
            error_msg = f"Unsupported action: {action}"
            self.feedback_manager.error(error_msg)
            raise ValueError(error_msg)

        return result
    
    def get_consume_quantity(self, product: Dict, quantity: float) -> Dict[str, float]:
        """Determine the quantity to consume based on product data

        Args:
            product: Product data

        Returns:
            Quantity to consume
        """
        consume_quantity = quantity
        # Check for quick_consume_amount
        product_data = product.get("product", product)
        quick_consume = product_data.get("quick_consume_amount")
        stock_amount_opened = product.get("stock_amount_opened")
        stock_amount = product.get('stock_amount')
        
        logging.info(f"Consume: {consume_quantity}, Quick Consume: {quick_consume}, Stock Amount Opened: {stock_amount_opened}, Stock Amount: {stock_amount}")

        if(stock_amount > 0):
            if quick_consume < stock_amount_opened:
                consume_quantity = float(quick_consume)  # Consume the normal amount of opened stock
            elif stock_amount_opened != 0:
                consume_quantity = float(stock_amount_opened)  # Consume the rest of the opened amount of stock
            elif quick_consume < stock_amount:
                consume_quantity = float(quick_consume)  # Consume the normal amount of stock
            elif stock_amount > 0:
                consume_quantity = float(stock_amount) # Consume available remaining stock
        else:
            raise ValueError("Nothing left in the inventory to consume.")

        return {
            "consume_quantity": consume_quantity,
            "total_quantity": stock_amount
        }
        
    def get_consume_open_quantity(self, product: Dict, quantity: float) -> Dict[str, float]:
        """Determine the quantity to consume based on product data

        Args:
            product: Product data

        Returns:
            Quantity to consume and total quantity
        """
        # Check for quick_consume_amount
        stock_amount_opened = product.get("stock_amount_opened",0)
        stock_amount = product.get('stock_amount',0)
        
        consume_quantity = stock_amount_opened or stock_amount

        logging.info(f"Consume open: {consume_quantity}, Stock Amount Opened: {stock_amount_opened}, Stock Amount: {stock_amount}")

        if consume_quantity == 0:
            raise ValueError("Nothing left in the inventory to consume.")

        return {
            "consume_quantity": consume_quantity,
            "total_quantity": stock_amount
        }
    

    def get_consume_expired_quantity(self, product: Dict, quantity: float) -> Dict[str, float]:
        """Determine the quantity to consume based on product data

        Args:
            product: Product data

        Returns:
            Quantity to consume
        """
        stock_amount_opened = product.get("stock_amount_opened",0)
        stock_amount = product.get('stock_amount',0)            
        consume_quantity = stock_amount_opened or stock_amount
        
        logging.info(f"Consume expired: {consume_quantity}, Stock Amount Opened: {stock_amount_opened}, Stock Amount: {stock_amount}")

        if consume_quantity == 0:
            raise ValueError("Nothing left in the inventory to consume.")
        
        return {
            "consume_quantity": consume_quantity,
            "total_quantity": stock_amount
        }
    
    def get_purchase_quantity(self, product: Dict, barcode: str, quantity: float) -> Dict[str, float]:
        """Determine the quantity to purchase based on product data

        Args:
            product: Product data

        Returns:
            Quantity to purchase
        """
        # Check for quick_purchase_amount
        product_data = product.get("product", product)
        purchase_quantity = float(product_data.get("quick_purchase_amount",0) or 0)
        logging.info(f"Setting default purchase quantity for product: {purchase_quantity}")
        stock_amount = float(product.get("stock_amount",0) or 0)

        barcodes = product.get("product_barcodes",[])
        for barcode_data in barcodes:
            if barcode_data.get("barcode") == barcode:
                purchase_quantity = float(barcode_data.get("amount",0) or 0)
                logging.info(f"Setting custom purchase quantity for barcode {barcode}: {purchase_quantity}")
                break
            
        logging.info(f"Product Data: {product_data}, Barcodes: {barcodes}")

        # Handle None values safely
        if purchase_quantity == 0 or purchase_quantity is None:
            purchase_quantity = quantity  # Default to 1 if quick_purchase_amount is not set
            
        logging.info(f"Purchase: {purchase_quantity}, Stock Amount: {stock_amount}")

        return {
            "purchase_quantity": purchase_quantity or quantity,
            "total_quantity": stock_amount
        }
    
    def get_shopping_quantity(self, product: Dict, barcode: str, quantity: float) -> Dict[str, float]:
        """Determine the quantity to purchase based on product data

        Args:
            product: Product data

        Returns:
            Quantity to add to shopping list
        """
        # Check for quick_purchase_amount
        product_data = product.get("product", product)
        logging.debug(f"Product: {product}")
        logging.debug(f"Product data: {product_data}")
        qu_conversion_factor_purchase_to_stock = int(product.get("qu_conversion_factor_purchase_to_stock",1) or 1)
        shopping_quantity = quantity * qu_conversion_factor_purchase_to_stock
        
        logging.debug(f"Setting default shopping quantity for product: {shopping_quantity} with conversion {qu_conversion_factor_purchase_to_stock} and quantity {quantity}")
        stock_amount = float(product.get("stock_amount",0) or 0)

        barcodes = product.get("product_barcodes",[])
        for barcode_data in barcodes:
            if barcode_data.get("barcode") == barcode:
                purchase_quantity = float(barcode_data.get("amount",0) or 0)
                logging.info(f"Setting custom shopping quantity for barcode {barcode}: {shopping_quantity}")
                break
            
        logging.info(f"Product Data: {product_data}, Barcodes: {barcodes}")

        # Handle None values safely
        if shopping_quantity == 0 or shopping_quantity is None:
            shopping_quantity = quantity  # Default to 1 if quick_purchase_amount is not set
            
        logging.info(f"Shopping: {shopping_quantity}, Stock Amount: {stock_amount}")

        return {
            "shopping_quantity": shopping_quantity or quantity,
            "total_quantity": stock_amount
        }
    
    def get_open_quantity(self, product: Dict, barcode: str, quantity: float) -> Dict[str, float]:
        """Determine the quantity to purchase based on product data

        Args:
            product: Product data

        Returns:
            Quantity to purchase
        """
        
        # Check for quick_purchase_amount
        product_data = product.get("product", product)
        open_quantity = float(product_data.get("quick_open_amount",0) or 0)
        stock_amount = product.get("stock_amount",0)

        barcodes = product.get("product_barcodes",[])
        for barcode_data in barcodes:
            if barcode_data.get("barcode") == barcode:
                open_quantity = float(barcode_data.get("amount",0) or 0)
                logging.debug(f"Setting custom open quantity for barcode {barcode}: {open_quantity}")
                break

        # Handle None values safely
        if open_quantity == 0 or open_quantity is None:
            open_quantity = quantity  # Default to 1 if quick_purchase_amount is not set

        logging.info(f"Purchase: {open_quantity}, Stock Amount: {stock_amount}")

        return {
            "open_quantity": open_quantity or quantity,
            "total_quantity": stock_amount
        }
    
    def get_quantity_with_unit_type(self, product: Dict, quantity: float) -> str:
        """Determine the quantity to purchase based on product data

        Args:
            product: Product data

        Returns:
            Quantity name text
        """
        stock_quantity_unit_name = product.get('quantity_unit_stock',{}).get('name')
        stock_quantity_unit_name_plural = product.get('quantity_unit_stock',{}).get('name_plural')
        if quantity == 1:
            quantity_unit_type = stock_quantity_unit_name
        else:
            quantity_unit_type = stock_quantity_unit_name_plural
        logging.debug(f"Quantity Unit Type: {quantity_unit_type}")
        return str(round(quantity,1)).rstrip('0').rstrip('.').lstrip("0") + " " + quantity_unit_type

    def execute_product_action(self, action: str, barcode: str, product_id: int, product: Dict, quantity: float) -> Dict:
        """Execute the determined action
        
        Args:
            action: Action to execute (consume, shopping, purchase)
            product_id: ID of product
            quantity: Quantity to use
            
        Returns:
            Result of the action
            
        Raises:
            ValueError: If action is not supported
        """
        result = {}
        
        # try:
        product_data = product.get("product", product)

        if action == 'consume':
            stockcheck = self.get_consume_quantity(product, quantity)
            consume_quantity = stockcheck.get('consume_quantity')
            total_quantity = stockcheck.get('total_quantity')
            result = self.grocy_client.consume_product(product_id, consume_quantity)
            self.feedback_manager.consume(f"Consumed {self.get_quantity_with_unit_type(product,consume_quantity)} of {total_quantity} {product_data['name']}")

        elif action == 'finish':
            stockcheck = self.get_consume_open_quantity(product, quantity)
            consume_quantity = stockcheck.get('consume_quantity')
            total_quantity = stockcheck.get('total_quantity')
            result = self.grocy_client.consume_product(product_id,consume_quantity)
            self.feedback_manager.consume(f"Consumed {self.get_quantity_with_unit_type(product,consume_quantity)} of {total_quantity} {product_data['name']}")

        elif action == 'expire':
            stockcheck = self.get_consume_expired_quantity(product, quantity)
            consume_quantity = stockcheck.get('consume_quantity')
            total_quantity = stockcheck.get('total_quantity')
            result = self.grocy_client.trash_product(product_id,consume_quantity)
            self.feedback_manager.consume(f"Trashed {self.get_quantity_with_unit_type(product,consume_quantity)} of {total_quantity} {product_data['name']}")

        elif action == 'shopping':
            stockcheck = self.get_shopping_quantity(product, barcode, quantity)
            logging.debug(f"Shopping quantity: {stockcheck}")
            shopping_quantity = stockcheck.get('shopping_quantity')
            logging.debug(f"Shopping quantity: {shopping_quantity}")
            result = self.grocy_client.add_to_shopping_list(product_id, shopping_quantity)
            self.feedback_manager.shopping(f"Added {product_data['name']} to shopping list")

        elif action == 'open':
            stockcheck = self.get_open_quantity(product, barcode, quantity)
            open_quantity = stockcheck.get('open_quantity')
            result = self.grocy_client.open_product(product_id, open_quantity)
            self.feedback_manager.open(f"Opened {self.get_quantity_with_unit_type(product,open_quantity)} {product_data['name']}")

        elif action == 'purchase':
            stockcheck = self.get_purchase_quantity(product, barcode, quantity)
            logging.debug(f"Purchase quantity: {stockcheck}")
            purchase_quantity = stockcheck.get('purchase_quantity')
            total_quantity = stockcheck.get('total_quantity')
            logging.debug(f"Purchase quantity: {purchase_quantity}")
            result = self.grocy_client.purchase_product(product_id, purchase_quantity)
            self.feedback_manager.success(f"Added {self.get_quantity_with_unit_type(product,purchase_quantity)} to {total_quantity} {product_data['name']} to inventory")

        else:
            error_msg = f"Unsupported action: {action}"
            self.feedback_manager.error(toggleBreak+error_msg)
            raise ValueError(error_msg)
            
        # Ensure result is a dictionary
        if result is None:
            result = {}
        elif not isinstance(result, dict):
            # logging.warning(f"Converting non-dict result to dict: {result}")
            result = {"data": result}
            
        return result
        
        # except Exception as e:
        #     error_msg = f"Error executing {action} for product ID {product_id}: {str(e)}"
        #     self.feedback_manager.error(error_msg)
        #     return {"success": False, "message": error_msg}
        #     self.feedback_manager.error(error_msg)
        #     raise ValueError(error_msg)
            
        # return result
