#!/usr/bin/env python3

import os
import sys
import logging
import signal
import argparse
from typing import Dict, Any

from config_manager import ConfigManager
from barcode_scanner import BarcodeScanner
from grocy_client import GrocyClient
from barcode_processor import BarcodeProcessor
from feedback_manager import FeedbackManager


class BarcodeApp:
    """
    Main application class for the barcode scanner system.
    """
    
    def __init__(self, config_file: str):
        """
        Initialize the application.
        
        Args:
            config_file: Path to configuration file
        """
        # Setup logging early with basic configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logging.info("Initializing Barcode Scanner Application")
        
        # Load configuration
        self.config = ConfigManager(config_file)
        
        # Configure logging based on config
        self._configure_logging()
        
        # Initialize components
        try:
            # Initialize Grocy client
            grocy_config = self.config.get_grocy_config()
            self.grocy = GrocyClient(
                grocy_config
            )
            
            # Initialize feedback manager
            self.feedback = FeedbackManager(self.grocy, self.config.get_full_config())

            # Initialize barcode processor
            self.processor = BarcodeProcessor(
                grocy_client=self.grocy,
                feedback_manager=self.feedback,  # This was missing
                config=self.config.get_full_config()
            )

            
            # Initialize barcode scanner
            scanner_config = self.config.get_scanner_config()
            self.scanner = BarcodeScanner(scanner_config)
            self.scanner.register_callback(self.on_barcode_scanned)
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._handle_exit)
            signal.signal(signal.SIGTERM, self._handle_exit)
            
            logging.info("Application initialized successfully, ready to "+ scanner_config.get('default_action', 'consume'))
            
        except Exception as e:
            logging.error(f"Failed to initialize application: {e}")
            raise
    
    def _configure_logging(self):
        """Configure logging based on configuration."""
        log_config = self.config.get_logging_config()
        
        log_level = log_config.get('level', 'INFO').upper()
        log_file = log_config.get('file')
        log_share = log_config.get('share')
        max_size = log_config.get('max_size_mb', 10) * 1024 * 1024
        backup_count = log_config.get('backup_count', 5)
        
        # Set log level
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        # Add file handler if configured
        if log_file:
            try:
                # Ensure directory exists
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                # Add rotating file handler
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_size,
                    backupCount=backup_count
                )
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(levelname)s::%(message)s'
                ))
                logging.getLogger().addHandler(file_handler)
                logging.debug(f"Logging to file: {log_file}")
            
            except Exception as e:
                logging.error(f"Failed to configure file logging: {e}")
    
    def run(self):
        """Main application loop."""
        logging.debug("Starting barcode scanner")
        
        try:
            self.scanner.start_listening()
            
            # Keep the main thread alive
            # logging.info("Application running. Press Ctrl+C to exit.")
            signal.pause()
            
        except KeyboardInterrupt:
            logging.info("Application interrupted")
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def on_barcode_scanned(self, barcode: str):
        """
        Callback for when barcode is scanned.
        
        Args:
            barcode: The scanned barcode
        """
        logging.info(f"Barcode scanned: {barcode}")
        
        try:
            self.feedback.waiting()
            result = self.processor.process_barcode(barcode)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                logging.error(f"Invalid result type: {type(result)}, value: {result}")
                self.feedback.error("Invalid result from barcode processing")
                return
                
            # Handle mode change
            if result.get('action') == 'mode_change' or result.get('action') == 'mode_attribute_change':
                # self.feedback.success(f"Mode changed to: {result.get('mode')}")
                return
            
            if result.get('action') == 'attributes_updated' or result.get('action') == 'mode_attribute_change':
                # self.feedback.success(f"Attributes changed to: {result.get('attributes', {})}")
                return

                
            # Handle create action
            if result.get('action') == 'create':
                # For now, just log that we need to create a product
                logging.debug(f"Need to create product with barcode: {result.get('barcode')}")
                # self.feedback.success(f"Creating new product with barcode: {result.get('barcode')}")
                return
            
            # Ensure result has a 'result' key that is a dictionary
            if 'result' not in result or not isinstance(result.get('result'), dict):
                logging.error(f"Missing or invalid 'result' key in: {result}")
                # self.feedback.error("Invalid result structure from barcode processing")
                return
                
            if result.get('result', {}).get('success', False):
                message = result.get('result', {}).get('message', "Operation successful")
                # self.feedback.success(message)
            else:
                message = result.get('result', {}).get('message', "Operation failed")
                self.feedback.error(message)
            
        except Exception as e:
            logging.error(f"Error processing barcode: {e}")
            self.feedback.error(str(e))
    
    def cleanup(self):
        """Clean up resources before exiting."""
        logging.info("Cleaning up resources")
        
        if hasattr(self, 'scanner'):
            self.scanner.stop_listening()
        
        logging.info("Cleanup complete")
    
    def _handle_exit(self, signum, frame):
        """
        Handle exit signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logging.info(f"Received signal {signum}, exiting")
        self.cleanup()
        sys.exit(0)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Barcode Scanner Application')
    parser.add_argument(
        '-c', '--config',
        default=os.environ.get('CONFIG_FILE', '/app/config/config.yml'),
        help='Path to configuration file'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    app = BarcodeApp(args.config)
    app.run()
