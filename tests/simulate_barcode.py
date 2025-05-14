#!/usr/bin/env python3
"""
Utility script to simulate barcode scanner input for testing.
This creates a virtual input device that emulates keyboard events.

Usage:
  sudo python simulate_barcode.py [barcode]

Example:
  sudo python simulate_barcode.py 12345
  sudo python simulate_barcode.py C-12345  # Consume action
  sudo python simulate_barcode.py P-12345  # Purchase action
"""

import sys
import time
import argparse

try:
    from evdev import UInput, ecodes
except ImportError:
    print("Error: evdev package not installed. Install with: pip install evdev")
    sys.exit(1)


def get_key_code(char):
    """
    Map a character to its key code.
    
    Args:
        char: Character to map
        
    Returns:
        Key code for the character
    """
    # Map of characters to key codes
    char_map = {
        '0': ecodes.KEY_0, '1': ecodes.KEY_1, '2': ecodes.KEY_2,
        '3': ecodes.KEY_3, '4': ecodes.KEY_4, '5': ecodes.KEY_5,
        '6': ecodes.KEY_6, '7': ecodes.KEY_7, '8': ecodes.KEY_8,
        '9': ecodes.KEY_9,
        
        'a': ecodes.KEY_A, 'b': ecodes.KEY_B, 'c': ecodes.KEY_C,
        'd': ecodes.KEY_D, 'e': ecodes.KEY_E, 'f': ecodes.KEY_F,
        'g': ecodes.KEY_G, 'h': ecodes.KEY_H, 'i': ecodes.KEY_I,
        'j': ecodes.KEY_J, 'k': ecodes.KEY_K, 'l': ecodes.KEY_L,
        'm': ecodes.KEY_M, 'n': ecodes.KEY_N, 'o': ecodes.KEY_O,
        'p': ecodes.KEY_P, 'q': ecodes.KEY_Q, 'r': ecodes.KEY_R,
        's': ecodes.KEY_S, 't': ecodes.KEY_T, 'u': ecodes.KEY_U,
        'v': ecodes.KEY_V, 'w': ecodes.KEY_W, 'x': ecodes.KEY_X,
        'y': ecodes.KEY_Y, 'z': ecodes.KEY_Z,
        
        'A': ecodes.KEY_A, 'B': ecodes.KEY_B, 'C': ecodes.KEY_C,
        'D': ecodes.KEY_D, 'E': ecodes.KEY_E, 'F': ecodes.KEY_F,
        'G': ecodes.KEY_G, 'H': ecodes.KEY_H, 'I': ecodes.KEY_I,
        'J': ecodes.KEY_J, 'K': ecodes.KEY_K, 'L': ecodes.KEY_L,
        'M': ecodes.KEY_M, 'N': ecodes.KEY_N, 'O': ecodes.KEY_O,
        'P': ecodes.KEY_P, 'Q': ecodes.KEY_Q, 'R': ecodes.KEY_R,
        'S': ecodes.KEY_S, 'T': ecodes.KEY_T, 'U': ecodes.KEY_U,
        'V': ecodes.KEY_V, 'W': ecodes.KEY_W, 'X': ecodes.KEY_X,
        'Y': ecodes.KEY_Y, 'Z': ecodes.KEY_Z,
        
        '-': ecodes.KEY_MINUS, '_': ecodes.KEY_MINUS,
        '=': ecodes.KEY_EQUAL, '+': ecodes.KEY_EQUAL,
        '[': ecodes.KEY_LEFTBRACE, '{': ecodes.KEY_LEFTBRACE,
        ']': ecodes.KEY_RIGHTBRACE, '}': ecodes.KEY_RIGHTBRACE,
        ';': ecodes.KEY_SEMICOLON, ':': ecodes.KEY_SEMICOLON,
        "'": ecodes.KEY_APOSTROPHE, '"': ecodes.KEY_APOSTROPHE,
        '`': ecodes.KEY_GRAVE, '~': ecodes.KEY_GRAVE,
        '\\': ecodes.KEY_BACKSLASH, '|': ecodes.KEY_BACKSLASH,
        ',': ecodes.KEY_COMMA, '<': ecodes.KEY_COMMA,
        '.': ecodes.KEY_DOT, '>': ecodes.KEY_DOT,
        '/': ecodes.KEY_SLASH, '?': ecodes.KEY_SLASH,
        ' ': ecodes.KEY_SPACE
    }
    
    if char in char_map:
        return char_map[char]
    else:
        print(f"Warning: No key code mapping for character '{char}'")
        return None


def simulate_barcode_scan(barcode, delay=0.05):
    """
    Simulate a barcode scan by generating keyboard events.
    
    Args:
        barcode: Barcode string to simulate
        delay: Delay between key events in seconds
    """
    # Create capabilities dict with all possible keys
    capabilities = {
        ecodes.EV_KEY: list(range(ecodes.KEY_ESC, ecodes.KEY_MICMUTE + 1))
    }
    
    try:
        # Create virtual input device
        ui = UInput(capabilities, name='virtual-barcode-scanner')
        print(f"Created virtual input device: virtual-barcode-scanner")
        time.sleep(1)  # Wait for the device to initialize
        
        print(f"Simulating barcode scan: {barcode}")
        
        # Type each character
        for char in barcode:
            key_code = get_key_code(char)
            if key_code is not None:
                # Press key
                ui.write(ecodes.EV_KEY, key_code, 1)
                ui.syn()
                time.sleep(delay)
                
                # Release key
                ui.write(ecodes.EV_KEY, key_code, 0)
                ui.syn()
                time.sleep(delay)
        
        # Press Enter to finish the barcode
        ui.write(ecodes.EV_KEY, ecodes.KEY_ENTER, 1)
        ui.syn()
        time.sleep(delay)
        ui.write(ecodes.EV_KEY, ecodes.KEY_ENTER, 0)
        ui.syn()
        
        print("Barcode scan completed")
        time.sleep(1)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ui.close()
        print("Virtual input device closed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Simulate barcode scanner input')
    parser.add_argument('barcode', help='Barcode to simulate')
    parser.add_argument('--delay', type=float, default=0.05,
                        help='Delay between key events in seconds (default: 0.05)')
    args = parser.parse_args()
    
    simulate_barcode_scan(args.barcode, args.delay)


if __name__ == "__main__":
    # Check if running as root (required for UInput)
    if os.geteuid() != 0:
        print("Error: This script must be run as root (sudo)")
        sys.exit(1)
    
    main()
