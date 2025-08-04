"""Tests for WindowController module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from mactoro.window_controller import WindowController


class TestWindowController:
    """Test cases for WindowController class."""

    @pytest.fixture
    def controller(self):
        """Create a WindowController instance for testing."""
        return WindowController()

    @pytest.fixture
    def mock_window_list(self):
        """Mock window list data."""
        return [
            {
                "kCGWindowNumber": 123,
                "kCGWindowOwnerName": "TestApp",
                "kCGWindowName": "Test Window",
                "kCGWindowBounds": {
                    "X": 100,
                    "Y": 200,
                    "Width": 800,
                    "Height": 600
                }
            },
            {
                "kCGWindowNumber": 456,
                "kCGWindowOwnerName": "AnotherApp",
                "kCGWindowName": "Another Window",
                "kCGWindowBounds": {
                    "X": 200,
                    "Y": 300,
                    "Width": 1024,
                    "Height": 768
                }
            }
        ]

    @patch('Quartz.CGWindowListCopyWindowInfo')
    def test_list_windows(self, mock_cg_window_list, controller, mock_window_list):
        """Test listing windows."""
        mock_cg_window_list.return_value = mock_window_list
        
        windows = controller.list_windows()
        
        assert len(windows) == 2
        assert windows[0]["app_name"] == "TestApp"
        assert windows[0]["window_name"] == "Test Window"
        assert windows[0]["window_id"] == 123
        assert windows[1]["app_name"] == "AnotherApp"
        assert windows[1]["window_name"] == "Another Window"
        assert windows[1]["window_id"] == 456

    @patch('Quartz.CGWindowListCopyWindowInfo')
    def test_find_window_by_name(self, mock_cg_window_list, controller, mock_window_list):
        """Test finding window by name."""
        mock_cg_window_list.return_value = mock_window_list
        
        # Test exact match
        window = controller.find_window("Test Window")
        assert window is not None
        assert window["window_name"] == "Test Window"
        
        # Test partial match
        window = controller.find_window("Test")
        assert window is not None
        assert window["window_name"] == "Test Window"
        
        # Test no match
        window = controller.find_window("Nonexistent Window")
        assert window is None

    @patch('Quartz.CGWindowListCopyWindowInfo')
    def test_find_window_by_id(self, mock_cg_window_list, controller, mock_window_list):
        """Test finding window by ID."""
        mock_cg_window_list.return_value = mock_window_list
        
        window = controller.find_window_by_id(123)
        assert window is not None
        assert window["window_id"] == 123
        assert window["window_name"] == "Test Window"
        
        window = controller.find_window_by_id(999)
        assert window is None

    @patch('pyautogui.click')
    @patch('Quartz.CGWindowListCopyWindowInfo')
    def test_execute_click_action(self, mock_cg_window_list, mock_click, controller, mock_window_list):
        """Test executing click action."""
        mock_cg_window_list.return_value = mock_window_list
        
        # Test absolute click
        action = {
            "type": "click",
            "x": 500,
            "y": 400
        }
        controller.execute_action(action, None)
        mock_click.assert_called_once_with(500, 400)
        
        # Test window-relative click
        mock_click.reset_mock()
        action = {
            "type": "click",
            "x": 50,
            "y": 50,
            "relative_to": "window"
        }
        window_info = controller.find_window("Test Window")
        controller.execute_action(action, window_info)
        mock_click.assert_called_once_with(150, 250)  # 100 + 50, 200 + 50

    @patch('pyautogui.typewrite')
    def test_execute_type_action(self, mock_typewrite, controller):
        """Test executing type action."""
        action = {
            "type": "type",
            "text": "Hello, World!",
            "interval": 0.05
        }
        controller.execute_action(action, None)
        mock_typewrite.assert_called_once_with("Hello, World!", interval=0.05)

    @patch('pyautogui.hotkey')
    def test_execute_hotkey_action(self, mock_hotkey, controller):
        """Test executing hotkey action."""
        action = {
            "type": "hotkey",
            "keys": ["cmd", "c"]
        }
        controller.execute_action(action, None)
        mock_hotkey.assert_called_once_with("cmd", "c")

    @patch('time.sleep')
    def test_execute_wait_action(self, mock_sleep, controller):
        """Test executing wait action."""
        action = {
            "type": "wait",
            "seconds": 2.5
        }
        controller.execute_action(action, None)
        mock_sleep.assert_called_once_with(2.5)

    def test_execute_invalid_action(self, controller):
        """Test executing invalid action type."""
        action = {
            "type": "invalid_action"
        }
        with pytest.raises(ValueError, match="Unknown action type"):
            controller.execute_action(action, None)

    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.load')
    def test_load_config(self, mock_json_load, mock_open, controller):
        """Test loading configuration from file."""
        mock_config = {
            "actions": [
                {"type": "click", "x": 100, "y": 200}
            ]
        }
        mock_json_load.return_value = mock_config
        
        config = controller.load_config("test_config.json")
        assert config == mock_config
        mock_open.assert_called_once_with("test_config.json", 'r')

    @patch('pyautogui.pixel')
    @patch('time.time')
    def test_wait_for_color(self, mock_time, mock_pixel, controller):
        """Test waiting for color at position."""
        # Mock time to simulate timeout
        mock_time.side_effect = [0, 1, 2, 3]
        
        # Mock pixel to return matching color on third check
        mock_pixel.side_effect = [
            (255, 0, 0),  # Wrong color
            (255, 0, 0),  # Wrong color
            (0, 255, 0),  # Correct color
        ]
        
        action = {
            "type": "wait_for_color",
            "x": 100,
            "y": 200,
            "color": [0, 255, 0],
            "timeout": 5,
            "tolerance": 10
        }
        
        # Should succeed on third check
        controller.execute_action(action, None)
        assert mock_pixel.call_count == 3