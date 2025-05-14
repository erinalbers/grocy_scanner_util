import logging
import os
import ctypes
from typing import Optional, Callable

class ScannerManager:
    def __init__(self):
        """Initialize the scanner interface"""
        try:
            # Load the shared library
            self.lib = ctypes.CDLL('/app/scanner_lib/cmd/linux/libscanner_cmd_x86_64-unknown-linux-gnu.so')
            
            # Define function signatures for the commands you'll actually use
            self.lib.inateck_scanner_cmd_set_bee.restype = ctypes.c_char_p
            self.lib.inateck_scanner_cmd_set_bee.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
            
            self.lib.inateck_scanner_cmd_set_led.restype = ctypes.c_char_p
            self.lib.inateck_scanner_cmd_set_led.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
            
            self.lib.inateck_scanner_cmd_open_all_code.restype = ctypes.c_char_p
            self.lib.inateck_scanner_cmd_open_all_code.argtypes = []
            
            # For USB connections, we can assume the scanner is already connected
            logging.info("Initializing USB scanner...")
            
            # Enable all barcode types
            result = self.lib.inateck_scanner_cmd_open_all_code()
            if result:
                logging.warning(f"Warning when enabling barcode types: {result.decode('utf-8')}")
            
            self.initialized = True
            logging.info("Scanner initialized successfully")
                
        except Exception as e:
            logging.error(f"Error initializing scanner: {e}")
            self.initialized = False
            self.lib = None
    
    def beep(self, voice_time: int = 10, silent_time: int = 0, count: int = 1):
        if not self.initialized:
            return False
            
        try:
            result = self.lib.inateck_scanner_cmd_set_bee(voice_time, silent_time, count)
            # Check if result is a string (JSON response)
            if result:
                try:
                    result_str = result.decode('utf-8')
                    import json
                    response = json.loads(result_str)
                    logging.info(f"Triggering beep: {response}")

                    # Check status in JSON response
                    if response.get("status") == 0:
                        return True
                    else:
                        logging.error(f"Beep error: {result_str}")
                        return False
                except Exception as e:
                    logging.error(f"Error parsing beep response: {e}")
                    return False
            else:
                # NULL result might indicate success
                return True
        except Exception as e:
            logging.error(f"Error triggering beep: {e}")
            return False

    
    def set_led(self, color: int = 1, light_time: int = 10, dark_time: int = 0, count: int = 1):
        if not self.initialized:
            return False
            
        try:
            result = self.lib.inateck_scanner_cmd_set_led(color, light_time, dark_time, count)

            # Check if result is a string (JSON response)
            if result:
                try:
                    
                    result_str = result.decode('utf-8')
                    import json
                    response = json.loads(result_str)
                    logging.info(f"Triggering LED: {response}")

                    # Check status in JSON response
                    if response.get("status") == 0:
                        return True
                    else:
                        logging.error(f"LED error: {result_str}")
                        return False
                except Exception as e:
                    logging.error(f"Error parsing LED response: {e}")
                    return False
            else:
                # NULL result might indicate success
                return True
        except Exception as e:
            logging.error(f"Error controlling LED: {e}")
            return False


    
    def get_version(self):
        """Get scanner firmware version
        
        Returns:
            str: Version string or None if error
        """
        if not self.initialized:
            return None
            
        try:
            result = self.lib.inateck_scanner_cmd_get_version()
            if result:
                return result.decode('utf-8')
            return "Unknown"
        except Exception as e:
            logging.error(f"Error getting version: {e}")
            return None
