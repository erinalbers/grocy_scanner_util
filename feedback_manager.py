import logging
import os
import ctypes
import grocy_client
from typing import Optional
   
class FeedbackManager:
    def __init__(self, grocy_client, config: dict):
        """Initialize feedback mechanisms (beep, LED, etc.)
        
        Args:
            config: Configuration dictionary with feedback settings
        """
        self.sound_enabled = config.get('sound_enabled', True)
        self.sound_dir = config.get('sound_dir', 'sounds')
        self.scanner = False
        self.grocy_client = grocy_client

        # Initialize audio system if sounds are enabled
        if self.sound_enabled:
            try:
                import pygame
                pygame.mixer.init()
                self.pygame = pygame
                logging.info("Audio feedback initialized")
            except ImportError:
                logging.warning("pygame not available, audio feedback disabled")
                self.sound_enabled = False
                self.pygame = None
            except Exception as e:
                logging.error(f"Error initializing audio: {e}")
                self.sound_enabled = False
                self.pygame = None

                # Initialize scanner
        # try:
        #     from scanner_manager import ScannerManager
        #     self.scanner = ScannerManager()
        #     if self.scanner.initialized:
        #         logging.info("Scanner feedback initialized")
        #         # Test the scanner with a short beep
        #         self.scanner.beep(5, 0, 1)
        #     else:
        #         logging.warning("Scanner initialization failed")
        #         self.scanner = None
        # except Exception as e:
        #     logging.error(f"Error initializing scanner manager: {e}")
        #     self.scanner = None
    
    def play_sound(self, sound_type: str) -> None:
        """Play a sound based on the action type
        
        Args:
            sound_type: Type of sound to play (success, error, consume, shopping)
        """
        if not self.sound_enabled or not self.pygame:
            return
            
        sound_file = os.path.join(self.sound_dir, sound_type, "beep.wav")
        
        # Check if the sound file exists
        if not os.path.exists(sound_file):
            logging.warning(f"Sound file not found: {sound_file}")
            # Try to use the default success sound as fallback
            fallback_file = os.path.join(self.sound_dir, "success", "beep.wav")
            if os.path.exists(fallback_file):
                sound_file = fallback_file
            else:
                return
        
        try:
            logging.info(f"Play sound file: {sound_file}")
            sound = self.pygame.mixer.Sound(sound_file)
            sound.play()
        except Exception as e:
            logging.error(f"Error playing sound: {e}")
    
    def success(self, message: Optional[str] = None) -> None:
        """Provide generic success feedback
        
        Args:
            message: Optional message to log
        """
        if self.scanner:
            self.scanner.beep(1, 0, 1)  # 100ms beep
            self.scanner.set_led(2, 20, 0, 1)  # Green LED for 200ms
        self.play_sound('success')
        if message:
            logging.info(message)
    
    def error(self, message: Optional[str] = None) -> None:
        """Provide error feedback
        
        Args:
            message: Optional error message to log
        """
        if self.scanner:
            self.scanner.beep(5, 5, 3)  # 3 short beeps
            self.scanner.set_led(1, 10, 5, 3)  # Flashing red LED
        self.play_sound('error')
        if message:
            logging.info(f"Warning... {message}")

    def scan(self):
        """Provide scan feedback"""
        if self.scanner:
            self.scanner.beep(5, 5, 2)  # Short beep
        self.play_sound("scan")
    
    def consume(self, message: Optional[str] = None) -> None:
        """Provide consume-specific feedback
        
        Args:
            message: Optional message to log
        """
        self.play_sound('consume')
        # self.scanner.beep(1, 0, 3)  # 3 short beeps
        if message:
            logging.info(f"{message}")
    
    def open(self, message: Optional[str] = None) -> None:
        """Provide open-specific feedback
        
        Args:
            message: Optional message to log
        """
        self.play_sound('open')
        if message:
            logging.info(f"{message}")
    
    def shopping(self, message: Optional[str] = None) -> None:
        """Provide shopping-specific feedback
        
        Args:
            message: Optional message to log
        """
        self.play_sound('shopping')
        if message:
            logging.info(f"{message}")
    
    def getinfo(self, message: Optional[str] = None) -> None:
        """Provide product information
        
        Args:
            message: Optional message to log
        """
        if message:
            logging.info(f"{message}")
    
    def unknown_product(self, message: Optional[str] = None) -> None:
        """Provide feedback for unknown products
        
        Args:
            message: Optional message to log
        """
        # Play error sound twice to indicate unknown product
        # self.play_sound('error')
        # import time
        # time.sleep(0.3)
        # self.play_sound('error')

        if message:
            logging.warning(f"{message}")
    
    def product_exists(self, message: Optional[str] = None) -> None:
        """Provide feedback for unknown products
        
        Args:
            message: Optional message to log
        """
        if message:
            logging.warning(f"{message}")
    
    def waiting(self, message: Optional[str] = None) -> None:
        """Indicate system is processing"""
        if message:
            logging.warning(f"Waiting: {message}")
        # Could use a different sound or LED pattern
        pass

    def attributes_updated(self, message: Optional[str] = "Attributes updated:", attributes = []) -> None:
        """Provide feedback for attributes updated

        Args:
            message: Optional message to log
            attributes: List of attribute IDs to look up
        """

        attribute_str = ""

        for attribute in attributes:
            if attribute == "group" and attributes["group"] != False:
                category = self.grocy_client.get_category_by_id(attributes["group"])
                attribute_str += f"{category['name']}, "

            elif attribute == "quantity" and attributes["quantity"] != False:
                quantity_unit = self.grocy_client.get_quantity_unit_by_id(attributes["quantity"])
                attribute_str += f" {quantity_unit['name']}, "

            elif attribute == "location" and attributes["location"] != False:
                location = self.grocy_client.get_location_by_id(attributes["location"])
                attribute_str += f"in the {location['name']}, "

            elif attribute == "store"  and attributes["store"] != False:
                shopping_location = self.grocy_client.get_shopping_locations(attributes["store"])
                attribute_str += f"Store: {shopping_location['name']}, "

            # else:
                # attribute_str += f"{attribute}: {attributes[attribute]}, "
        attribute_str = attribute_str.rstrip(", ")

        if message:
            logging.info(f"{message}{attribute_str}")