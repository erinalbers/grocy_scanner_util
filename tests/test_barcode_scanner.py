import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import threading
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock evdev before importing BarcodeScanner
sys.modules['evdev'] = MagicMock()
from barcode_scanner import BarcodeScanner


class TestBarcodeScanner(unittest.TestCase):
    """Test cases for the BarcodeScanner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample configuration
        self.config = {
            'connection_type': 'usb_hid',
            'usb_hid': {
                'device_path': '/dev/input/event0'
            }
        }
        
        # Mock evdev
        self.evdev_patcher = patch.dict('sys.modules', {'evdev': MagicMock()})
        self.mock_evdev = self.evdev_patcher.start()
        
        # Create mock device
        self.mock_device = MagicMock()
        self.mock_device.name = 'Test Barcode Scanner'
        self.mock_device.path = '/dev/input/event0'
        
        # Setup evdev.InputDevice to return our mock device
        import evdev
        evdev.InputDevice.return_value = self.mock_device
        
        # Setup evdev.list_devices to return a list with our mock device path
        evdev.list_devices.return_value = ['/dev/input/event0']
        
        # Setup evdev.ecodes
        evdev.ecodes.EV_KEY = 1
        evdev.ecodes.KEY_A = 30
        evdev.ecodes.KEY_B = 48
        evdev.ecodes.KEY_C = 46
        evdev.ecodes.KEY_1 = 2
        evdev.ecodes.KEY_2 = 3
        evdev.ecodes.KEY_3 = 4
        evdev.ecodes.KEY_ENTER = 28
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.evdev_patcher.stop()
    
    def test_initialization_with_device_path(self):
        """Test initialization with specific device path."""
        # Create scanner
        scanner = BarcodeScanner(self.config)
        
        # Verify device was initialized
        import evdev
        evdev.InputDevice.assert_called_once_with('/dev/input/event0')
        self.assertEqual(scanner.device, self.mock_device)
    
    def test_initialization_auto_detect(self):
        """Test initialization with auto-detection."""
        # Modify config to use auto-detection
        config = self.config.copy()
        config['usb_hid'] = {'device_path': ''}
        
        # Setup device name to include 'scanner'
        self.mock_device.name = 'USB Barcode Scanner'
        
        # Create scanner
        scanner = BarcodeScanner(config)
        
        # Verify device was auto-detected
        import evdev
        evdev.list_devices.assert_called_once()
        self.assertEqual(scanner.device, self.mock_device)
    
    def test_initialization_no_device_found(self):
        """Test initialization when no device is found."""
        # Modify config to use auto-detection
        config = self.config.copy()
        config['usb_hid'] = {'device_path': ''}
        
        # Setup empty device list
        import evdev
        evdev.list_devices.return_value = []
        
        # Verify exception is raised
        with self.assertRaises(ValueError):
            BarcodeScanner(config)
    
    def test_initialization_invalid_connection_type(self):
        """Test initialization with invalid connection type."""
        # Modify config to use invalid connection type
        config = self.config.copy()
        config['connection_type'] = 'invalid'
        
        # Verify exception is raised
        with self.assertRaises(ValueError):
            BarcodeScanner(config)
    
    def test_start_stop_listening(self):
        """Test starting and stopping the listener."""
        # Create scanner
        scanner = BarcodeScanner(self.config)
        
        # Start listening
        scanner.start_listening()
        
        # Verify thread was started
        self.assertTrue(scanner.running)
        self.assertIsNotNone(scanner.listener_thread)
        
        # Stop listening
        scanner.stop_listening()
        
        # Verify thread was stopped
        self.assertFalse(scanner.running)
        self.mock_device.close.assert_called_once()
    
    def test_register_callback(self):
        """Test registering a callback function."""
        # Create scanner
        scanner = BarcodeScanner(self.config)
        
        # Create mock callback
        mock_callback = MagicMock()
        
        # Register callback
        scanner.register_callback(mock_callback)
        
        # Verify callback was registered
        self.assertEqual(scanner.callback, mock_callback)
    
    def test_process_input_event(self):
        """Test processing input events."""
        # Create scanner
        scanner = BarcodeScanner(self.config)
        
        # Create mock callback
        mock_callback = MagicMock()
        scanner.register_callback(mock_callback)
        
        # Create mock events
        import evdev
        
        # Create events for "abc123" followed by ENTER
        events = [
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_A, value=1),
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_B, value=1),
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_C, value=1),
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_1, value=1),
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_2, value=1),
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_3, value=1),
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_ENTER, value=1)
        ]
        
        # Process each event
        for event in events:
            scanner._process_input_event(event)
        
        # Verify callback was called with correct barcode
        mock_callback.assert_called_once_with('abc123')
    
    def test_timeout_processing(self):
        """Test barcode processing due to timeout."""
        # Create scanner with short timeout
        scanner = BarcodeScanner(self.config)
        scanner.timeout = 0.1  # 100ms timeout
        
        # Create mock callback
        mock_callback = MagicMock()
        scanner.register_callback(mock_callback)
        
        # Create mock events
        import evdev
        
        # Create events for "abc"
        events = [
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_A, value=1),
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_B, value=1),
            MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_C, value=1)
        ]
        
        # Process each event
        for event in events:
            scanner._process_input_event(event)
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Process one more event to trigger timeout check
        scanner._process_input_event(events[0])
        
        # Verify callback was called with correct barcode
        self.assertEqual(mock_callback.call_count, 1)
        mock_callback.assert_called_with('abc')
    
    def test_callback_exception_handling(self):
        """Test handling exceptions in callback."""
        # Create scanner
        scanner = BarcodeScanner(self.config)
        
        # Create mock callback that raises exception
        mock_callback = MagicMock(side_effect=Exception("Callback error"))
        scanner.register_callback(mock_callback)
        
        # Create mock event
        import evdev
        event = MagicMock(type=evdev.ecodes.EV_KEY, code=evdev.ecodes.KEY_ENTER, value=1)
        
        # Set buffer to simulate previous input
        scanner.buffer = "test"
        
        # Process event (should not raise exception)
        try:
            scanner._process_input_event(event)
        except Exception:
            self.fail("_process_input_event() raised Exception unexpectedly!")
        
        # Verify callback was called
        mock_callback.assert_called_once_with('test')


if __name__ == '__main__':
    unittest.main()
