#!/usr/bin/env python3
"""
Simple REST API for testing the barcode scanner in test mode.
This allows simulating barcode scans via HTTP requests.
"""

import os
import sys
import logging
import argparse
from flask import Flask, request, jsonify

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from barcode_scanner import BarcodeScanner
from grocy_client import GrocyClient
from barcode_processor import BarcodeProcessor
from feedback_manager import FeedbackManager

# Initialize Flask app
app = Flask(__name__)

# Global variables for components
scanner = None
processor = None
feedback = None


@app.route('/api/scan', methods=['POST'])
def simulate_scan():
    """
    Simulate a barcode scan via API.
    
    POST /api/scan
    {
        "barcode": "12345"
    }
    """
    if not request.json or 'barcode' not in request.json:
        return jsonify({'error': 'Missing barcode parameter'}), 400
    
    barcode = request.json['barcode']
    
    if not scanner:
        return jsonify({'error': 'Scanner not initialized'}), 500
    
    # Simulate the scan
    success = scanner.simulate_scan(barcode)
    
    if success:
        return jsonify({'status': 'success', 'message': f'Processed barcode: {barcode}'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Failed to process barcode'}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the status of the barcode scanner application."""
    if not scanner or not processor or not feedback:
        return jsonify({'status': 'error', 'message': 'Components not initialized'}), 500
    
    return jsonify({
        'status': 'ok',
        'scanner': {
            'running': scanner.running,
            'test_mode': scanner.config.get('test_mode', False)
        },
        'grocy': {
            'api_url': processor.grocy_client.api_url
        }
    }), 200


def initialize_components(config_file):
    """Initialize application components."""
    global scanner, processor, feedback
    
    try:
        # Load configuration
        config_manager = ConfigManager(config_file)
        config = config_manager.get_full_config()
        
        # Ensure test mode is enabled
        if not config.get('scanner', {}).get('test_mode', False):
            config.setdefault('scanner', {})['test_mode'] = True
            logging.warning("Forcing test mode to be enabled")
        
        # Initialize Grocy client
        grocy_config = config_manager.get_grocy_config()
        grocy_client = GrocyClient(
            api_url=grocy_config['api_url'],
            api_key=grocy_config['api_key']
        )
        
        # Initialize feedback manager first
        feedback = FeedbackManager(config)
        
        # Initialize processor with all required parameters
        processor = BarcodeProcessor(grocy_client, feedback, config)
        
        # Initialize scanner
        scanner_config = config_manager.get_scanner_config()
        scanner = BarcodeScanner(scanner_config)
        
        # Register callback
        def on_barcode_scanned(barcode):
            logging.info(f"Processing barcode: {barcode}")
            try:
                feedback.waiting()
                result = processor.process_barcode(barcode)
                
                if result.get('result', {}).get('success', False):
                    feedback.success(result.get('result', {}).get('message'))
                else:
                    feedback.error(result.get('result', {}).get('message'))
                
                return True
            except Exception as e:
                logging.error(f"Error processing barcode: {e}")
                feedback.error(str(e))
                return False
        
        scanner.register_callback(on_barcode_scanned)
        scanner.start_listening()
        
        logging.info("Components initialized successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to initialize components: {e}")
        return False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Barcode Scanner Test API')
    parser.add_argument(
        '-c', '--config',
        default=os.environ.get('CONFIG_FILE', '/app/config/config.yml'),
        help='Path to configuration file'
    )
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=int(os.environ.get('API_PORT', 5000)),
        help='Port to run the API server on'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    return parser.parse_args()


if __name__ == '__main__':
    # Parse arguments
    args = parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize components
    if initialize_components(args.config):
        # Run the Flask app
        app.run(host='0.0.0.0', port=args.port, debug=args.debug)
    else:
        logging.error("Failed to initialize components, exiting")
        sys.exit(1)
