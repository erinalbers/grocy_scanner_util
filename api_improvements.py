from flask import Flask, request, jsonify
import logging

# Custom exception for product not found
class ProductNotFoundException(Exception):
    pass

# The routes below are meant to be imported and used with an existing Flask app
# They are not meant to be executed directly in this file

def register_routes(app, processor, grocy_client):
    """Register the API routes with the provided Flask app
    
    Args:
        app: Flask application instance
        processor: BarcodeProcessor instance
        grocy_client: GrocyClient instance
    """
    
    # Improved scan endpoint with better error handling
    @app.route('/api/scan', methods=['POST'])
    def scan_barcode():
        try:
            # Parse JSON data
            data = request.json
            logging.info(f"Response received for barcode scan: {data}")
            barcode = data.get('barcode')
        except Exception as e:
            logging.error(f"Error processing barcode scan response: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
        
        if not barcode:
            return jsonify({"status": "error", "message": "No barcode provided"}), 400
        
        try:
            result = processor.process_barcode(barcode)
            return jsonify({
                "status": "success", 
                "message": f"Processed barcode: {barcode}",
                "action": result.get("action"),
                "product": result.get("product")
            })
        except ProductNotFoundException as e:
            # Return a specific status for unknown products
            return jsonify({
                "status": "unknown_product", 
                "barcode": barcode,
                "message": str(e)
            }), 404
        except Exception as e:
            logging.error(f"Error processing barcode (api_improvements.py): {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    # New endpoint for creating products
    @app.route('/api/products', methods=['POST'])
    def create_product():
        data = request.json
        
        required_fields = ['barcode', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
        
        try:
            # Extract product details
            barcode = data.get('barcode')
            name = data.get('name')
            description = data.get('description', '')
            quantity_unit_id = data.get('quantity_unit_id', 1)  # Default unit
            location_id = data.get('location_id')
            category_id = data.get('category_id')
            
            # Create product in Grocy
            result = grocy_client.create_product(
                name=name,
                description=description,
                barcode=barcode,
                quantity_unit_id=quantity_unit_id,
                location_id=location_id,
                category_id=category_id
            )
            
            # Return the created product details
            return jsonify({
                "status": "success", 
                "message": f"Product created: {name}",
                "product_id": result.get('id'),
                "barcode": barcode
            })
        except Exception as e:
            logging.error(f"Error creating product: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    # Endpoint to get all available locations and categories for product creation
    @app.route('/api/product-metadata', methods=['GET'])
    def get_product_metadata():
        try:
            locations = grocy_client.get_locations()
            categories = grocy_client.get_categories()
            quantity_units = grocy_client.get_quantity_units()
            
            return jsonify({
                "status": "success",
                "locations": locations,
                "categories": categories,
                "quantity_units": quantity_units
            })
        except Exception as e:
            logging.error(f"Error fetching product metadata: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
