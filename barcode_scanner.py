import evdev
import logging
import threading
import time
import os
from typing import Optional, Callable, Dict, Any


class BarcodeScanner:
    """
    Class to handle barcode scanner input from various connection types.
    Currently supports USB HID mode with evdev.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize scanner connection based on config.
        
        Args:
            config: Dictionary containing scanner configuration
        """
        self.config = config
        self.connection_type = config.get('connection_type', 'usb_hid')
        self.device = None
        self.running = False
        self.listener_thread = None
        self.callback = None
        self.buffer = ""
        self.last_event_time = 0
        self.timeout = 0.5  # seconds to wait before processing buffer

        
        # Initialize the appropriate connection
        if self.connection_type == 'usb_hid':
            self._init_usb_hid()
        elif self.connection_type == 'bluetooth_hid':
            self._init_bluetooth_hid()
        elif self.connection_type == 'spp':
            self._init_spp()
        elif self.connection_type == 'sdk':
            self._init_sdk()
        else:
            raise ValueError(f"Unsupported connection type: {self.connection_type}")
    
    def _init_usb_hid(self):
        """Initialize USB HID connection using evdev."""
        # Check if we're in test mode
        test_mode = self.config.get('test_mode', "False") == "True"
        
        if test_mode:
            logging.info("Running in test mode, skipping physical device check")
            self.device = None
            return
            
        device_path = self.config.get('usb_hid', {}).get('device_path', '')
        
        if device_path:
            try:
                self.device = evdev.InputDevice(device_path)
                logging.info(f"Connected to scanner at {device_path}")
            except Exception as e:
                logging.error(f"Failed to connect to device at {device_path}: {e}")
                raise
        else:
            # Auto-detect barcode scanner
            try:
                devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
                for device in devices:
                    # Look for devices that might be barcode scanners
                    # This is a simple heuristic and might need adjustment
                    if 'scanner' in device.name.lower() or 'barcode' in device.name.lower():
                        self.device = device
                        logging.info(f"Auto-detected scanner: {device.name} at {device.path}")
                        break
                
                if not self.device:
                    logging.error("No barcode scanner found. Please specify device path or use test mode.")
                    raise ValueError("No barcode scanner found")
            except Exception as e:
                logging.error(f"Error accessing input devices: {e}")
                logging.error("No barcode scanner found. Please specify device path or use test mode.")
                raise ValueError("No barcode scanner found")
    
    def _init_bluetooth_hid(self):
        """Initialize Bluetooth HID connection."""
        # Implementation would depend on the specific Bluetooth library
        logging.warning("Bluetooth HID mode not fully implemented")
        pass
    
    def _init_spp(self):
        """Initialize Serial Port Profile connection."""
        # Implementation would use pyserial or similar
        logging.warning("SPP mode not fully implemented")
        pass
    
    def _init_sdk(self):
        """Initialize connection using vendor SDK."""
        # Implementation would depend on vendor SDK
        logging.warning("SDK mode not fully implemented")
        pass
    
    def register_callback(self, callback: Callable[[str], None]):
        """
        Register a callback function to be called when a barcode is scanned.
        
        Args:
            callback: Function that takes a barcode string as argument
        """
        self.callback = callback
    
    def start_listening(self):
        """Start event loop to listen for barcode scans."""
        if self.running:
            logging.warning("Scanner is already listening")
            return
        
        self.running = True
        
        # Check if we're in test mode
        test_mode = self.config.get('test_mode', "False") == "True"
        if test_mode:
            logging.debug("Started test mode listener")
            return
        
        if self.connection_type == 'usb_hid':
            self.listener_thread = threading.Thread(target=self._usb_hid_listener)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            logging.debug("Started USB HID listener")
        elif self.connection_type == 'bluetooth_hid':
            # Similar implementation for bluetooth
            pass
        elif self.connection_type == 'spp':
            # Similar implementation for SPP
            pass
        elif self.connection_type == 'sdk':
            # Similar implementation for SDK
            pass
    
    def stop_listening(self):
        """Clean up and close connection."""
        self.running = False
        
        # Check if we're in test mode
        test_mode = self.config.get('test_mode', "False") == "True"
        if test_mode:
            logging.debug("Stopped test mode listener")
            return
            
        if self.listener_thread:
            self.listener_thread.join(timeout=1.0)
        
        if self.device:
            self.device.close()
            self.device = None
        
        logging.info("Stopped barcode scanner listener")
    
    def _usb_hid_listener(self):
        """Listen for USB HID events in a loop."""
        if not self.device:
            logging.error("No device initialized")
            return
        
        try:
            for event in self.device.read_loop():
                if not self.running:
                    break
                
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:  # Key down events
                    self._process_input_event(event)
        except Exception as e:
            logging.error(f"Error in USB HID listener: {e}")
            self.running = False
    
    def _process_input_event(self, event):
        """
        Process raw input events from scanner.
        
        Args:
            event: Input event from evdev
        """
        # Map evdev key codes to characters
        key_mapping = {
            evdev.ecodes.KEY_0: '0', evdev.ecodes.KEY_1: '1',
            evdev.ecodes.KEY_2: '2', evdev.ecodes.KEY_3: '3',
            evdev.ecodes.KEY_4: '4', evdev.ecodes.KEY_5: '5',
            evdev.ecodes.KEY_6: '6', evdev.ecodes.KEY_7: '7',
            evdev.ecodes.KEY_8: '8', evdev.ecodes.KEY_9: '9',
            evdev.ecodes.KEY_A: 'a', evdev.ecodes.KEY_B: 'b',
            evdev.ecodes.KEY_C: 'c', evdev.ecodes.KEY_D: 'd',
            evdev.ecodes.KEY_E: 'e', evdev.ecodes.KEY_F: 'f',
            evdev.ecodes.KEY_G: 'g', evdev.ecodes.KEY_H: 'h',
            evdev.ecodes.KEY_I: 'i', evdev.ecodes.KEY_J: 'j',
            evdev.ecodes.KEY_K: 'k', evdev.ecodes.KEY_L: 'l',
            evdev.ecodes.KEY_M: 'm', evdev.ecodes.KEY_N: 'n',
            evdev.ecodes.KEY_O: 'o', evdev.ecodes.KEY_P: 'p',
            evdev.ecodes.KEY_Q: 'q', evdev.ecodes.KEY_R: 'r',
            evdev.ecodes.KEY_S: 's', evdev.ecodes.KEY_T: 't',
            evdev.ecodes.KEY_U: 'u', evdev.ecodes.KEY_V: 'v',
            evdev.ecodes.KEY_W: 'w', evdev.ecodes.KEY_X: 'x',
            evdev.ecodes.KEY_Y: 'y', evdev.ecodes.KEY_Z: 'z',
            evdev.ecodes.KEY_MINUS: '-', evdev.ecodes.KEY_EQUAL: '=',
            evdev.ecodes.KEY_LEFTBRACE: '[', evdev.ecodes.KEY_RIGHTBRACE: ']',
            evdev.ecodes.KEY_SEMICOLON: ';', evdev.ecodes.KEY_APOSTROPHE: "'",
            evdev.ecodes.KEY_GRAVE: '`', evdev.ecodes.KEY_BACKSLASH: '\\',
            evdev.ecodes.KEY_COMMA: ',', evdev.ecodes.KEY_DOT: '.',
            evdev.ecodes.KEY_SLASH: '/', evdev.ecodes.KEY_SPACE: ' ',
        }
        
        current_time = time.time()
        
        # If we have a key mapping for this event
        if event.code in key_mapping:
            # Add character to buffer
            self.buffer += key_mapping[event.code]
            self.last_event_time = current_time
        elif event.code == evdev.ecodes.KEY_ENTER:
            # Enter key typically signals end of barcode
            self._decode_barcode(self.buffer)
            self.buffer = ""
        
        # Check if we should process the buffer due to timeout
        if self.buffer and (current_time - self.last_event_time) > self.timeout:
            self._decode_barcode(self.buffer)
            self.buffer = ""
    
    def _decode_barcode(self, raw_input):
        """
        Convert raw scanner input to barcode string and trigger callback.
        
        Args:
            raw_input: Raw string from scanner events
        """
        if not raw_input:
            return
        
        barcode = raw_input.strip()
        logging.debug(f"Decoded barcode: {barcode}")
        
        if self.callback:
            try:
                self.callback(barcode)
            except Exception as e:
                logging.error(f"Error in barcode callback: {e}")
    
    def simulate_scan(self, barcode):
        """
        Simulate a barcode scan in test mode.
        
        Args:
            barcode: The barcode string to simulate
            
        Returns:
            True if successful, False otherwise
        """
        test_mode = self.config.get('test_mode', "False") == "True"

        if not test_mode:
            logging.warning("Ignoring simulated scan - not in test mode")
            return False
            
        logging.info(f"Simulating barcode scan: {barcode}")
        
        if self.callback:
            try:
                self.callback(barcode)
                return True
            except Exception as e:
                logging.error(f"Error in barcode callback: {e}")
                return False
        else:
            logging.warning("No callback registered for simulated scan")
            return False
