import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pygame before importing FeedbackManager
sys.modules['pygame'] = MagicMock()
from feedback_manager import FeedbackManager


class TestFeedbackManager(unittest.TestCase):
    """Test cases for the FeedbackManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample configuration
        self.config = {
            'feedback': {
                'audio': True,
                'visual': True,
                'audio_success': '/app/sounds/success.wav',
                'audio_error': '/app/sounds/error.wav',
                'audio_waiting': '/app/sounds/waiting.wav'
            }
        }
        
        # Patch os.path.exists to return True for sound files
        self.path_exists_patcher = patch('os.path.exists')
        self.mock_path_exists = self.path_exists_patcher.start()
        self.mock_path_exists.return_value = True
        
        # Patch pygame.mixer
        self.pygame_patcher = patch.dict('sys.modules', {'pygame': MagicMock()})
        self.mock_pygame = self.pygame_patcher.start()
        
        # Set AUDIO_AVAILABLE to True
        self.audio_available_patcher = patch('feedback_manager.AUDIO_AVAILABLE', True)
        self.mock_audio_available = self.audio_available_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.path_exists_patcher.stop()
        self.pygame_patcher.stop()
        self.audio_available_patcher.stop()
    
    def test_initialization(self):
        """Test feedback manager initialization."""
        # Create feedback manager
        feedback_manager = FeedbackManager(self.config)
        
        # Verify audio and visual are enabled
        self.assertTrue(feedback_manager.audio_enabled)
        self.assertTrue(feedback_manager.visual_enabled)
        
        # Verify pygame.mixer.init was called
        import pygame
        pygame.mixer.init.assert_called_once()
    
    def test_initialization_audio_disabled(self):
        """Test initialization with audio disabled."""
        # Modify config to disable audio
        config = self.config.copy()
        config['feedback']['audio'] = False
        
        # Create feedback manager
        feedback_manager = FeedbackManager(config)
        
        # Verify audio is disabled
        self.assertFalse(feedback_manager.audio_enabled)
        self.assertTrue(feedback_manager.visual_enabled)
        
        # Verify pygame.mixer.init was not called
        import pygame
        pygame.mixer.init.assert_not_called()
    
    def test_initialization_visual_disabled(self):
        """Test initialization with visual feedback disabled."""
        # Modify config to disable visual
        config = self.config.copy()
        config['feedback']['visual'] = False
        
        # Create feedback manager
        feedback_manager = FeedbackManager(config)
        
        # Verify visual is disabled
        self.assertTrue(feedback_manager.audio_enabled)
        self.assertFalse(feedback_manager.visual_enabled)
    
    @patch('feedback_manager.pygame')
    def test_success_feedback(self, mock_pygame):
        """Test success feedback."""
        # Setup mock sound
        mock_sound = MagicMock()
        mock_pygame.mixer.Sound.return_value = mock_sound
        
        # Create feedback manager
        feedback_manager = FeedbackManager(self.config)
        
        # Mock sounds dictionary
        feedback_manager.sounds = {'success': mock_sound}
        
        # Call success method
        feedback_manager.success("Test success")
        
        # Verify sound was played
        mock_sound.play.assert_called_once()
    
    @patch('feedback_manager.pygame')
    def test_error_feedback(self, mock_pygame):
        """Test error feedback."""
        # Setup mock sound
        mock_sound = MagicMock()
        mock_pygame.mixer.Sound.return_value = mock_sound
        
        # Create feedback manager
        feedback_manager = FeedbackManager(self.config)
        
        # Mock sounds dictionary
        feedback_manager.sounds = {'error': mock_sound}
        
        # Call error method
        feedback_manager.error("Test error")
        
        # Verify sound was played
        mock_sound.play.assert_called_once()
    
    @patch('feedback_manager.pygame')
    def test_waiting_feedback(self, mock_pygame):
        """Test waiting feedback."""
        # Setup mock sound
        mock_sound = MagicMock()
        mock_pygame.mixer.Sound.return_value = mock_sound
        
        # Create feedback manager
        feedback_manager = FeedbackManager(self.config)
        
        # Mock sounds dictionary
        feedback_manager.sounds = {'waiting': mock_sound}
        
        # Call waiting method
        feedback_manager.waiting()
        
        # Verify sound was played
        mock_sound.play.assert_called_once()
    
    @patch('feedback_manager.pygame')
    def test_sound_file_not_found(self, mock_pygame):
        """Test handling of missing sound files."""
        # Setup path.exists to return False
        self.mock_path_exists.return_value = False
        
        # Create feedback manager
        feedback_manager = FeedbackManager(self.config)
        
        # Verify no sounds were loaded
        self.assertEqual(len(feedback_manager.sounds), 0)
    
    @patch('feedback_manager.pygame')
    def test_sound_load_exception(self, mock_pygame):
        """Test handling exceptions when loading sounds."""
        # Setup pygame.mixer.Sound to raise exception
        mock_pygame.mixer.Sound.side_effect = Exception("Sound load error")
        
        # Create feedback manager
        feedback_manager = FeedbackManager(self.config)
        
        # Verify no sounds were loaded
        self.assertEqual(len(feedback_manager.sounds), 0)
    
    @patch('feedback_manager.pygame')
    def test_play_sound_exception(self, mock_pygame):
        """Test handling exceptions when playing sounds."""
        # Setup mock sound that raises exception when played
        mock_sound = MagicMock()
        mock_sound.play.side_effect = Exception("Sound play error")
        
        # Create feedback manager
        feedback_manager = FeedbackManager(self.config)
        
        # Mock sounds dictionary
        feedback_manager.sounds = {'success': mock_sound}
        
        # Call success method (should not raise exception)
        try:
            feedback_manager.success("Test success")
        except Exception:
            self.fail("success() raised Exception unexpectedly!")


if __name__ == '__main__':
    unittest.main()
