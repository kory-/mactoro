"""Tests for ActionRecorder module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from mactoro.action_recorder import ActionRecorder


class TestActionRecorder:
    """Test cases for ActionRecorder class."""

    @pytest.fixture
    def recorder(self):
        """Create an ActionRecorder instance for testing."""
        return ActionRecorder()

    def test_initialization(self, recorder):
        """Test ActionRecorder initialization."""
        assert recorder.actions == []
        assert recorder.recording is False
        assert recorder.listener is None
        assert recorder.window_info is None
        assert recorder.start_time is None

    def test_add_action(self, recorder):
        """Test adding actions."""
        action = {"type": "click", "x": 100, "y": 200}
        recorder.add_action(action)
        assert len(recorder.actions) == 1
        assert recorder.actions[0] == action

    def test_merge_similar_actions_type(self, recorder):
        """Test merging similar type actions."""
        recorder.merge_similar_actions = True
        recorder.add_action({"type": "type", "text": "Hello"})
        recorder.add_action({"type": "type", "text": " World"})
        
        assert len(recorder.actions) == 1
        assert recorder.actions[0]["text"] == "Hello World"

    def test_merge_similar_actions_disabled(self, recorder):
        """Test that merging doesn't happen when disabled."""
        recorder.merge_similar_actions = False
        recorder.add_action({"type": "type", "text": "Hello"})
        recorder.add_action({"type": "type", "text": " World"})
        
        assert len(recorder.actions) == 2
        assert recorder.actions[0]["text"] == "Hello"
        assert recorder.actions[1]["text"] == " World"

    @patch('time.time')
    def test_on_click(self, mock_time, recorder):
        """Test recording click events."""
        mock_time.return_value = 100.0
        recorder.recording = True
        recorder.start_time = 95.0
        recorder.window_info = {"bounds": {"X": 50, "Y": 50}}
        
        recorder.on_click(150, 200, None, True)
        
        assert len(recorder.actions) == 1
        action = recorder.actions[0]
        assert action["type"] == "click"
        assert action["x"] == 100  # 150 - 50 (window relative)
        assert action["y"] == 150  # 200 - 50 (window relative)
        assert action["relative_to"] == "window"
        assert action["timestamp"] == 5.0

    @patch('time.time')
    def test_on_key_press(self, mock_time, recorder):
        """Test recording key press events."""
        mock_time.return_value = 100.0
        recorder.recording = True
        recorder.start_time = 95.0
        
        # Test regular character
        mock_key = Mock()
        mock_key.char = 'a'
        recorder.on_key_press(mock_key)
        
        assert len(recorder.actions) == 1
        assert recorder.actions[0]["type"] == "type"
        assert recorder.actions[0]["text"] == "a"
        
        # Test special key (should be ignored)
        mock_key.char = None
        recorder.on_key_press(mock_key)
        assert len(recorder.actions) == 1  # No new action added

    @patch('pynput.mouse.Listener')
    @patch('pynput.keyboard.Listener')
    @patch('time.time')
    def test_start_recording(self, mock_time, mock_keyboard_listener, mock_mouse_listener, recorder):
        """Test starting recording."""
        mock_time.return_value = 100.0
        mock_window = {"window_id": 123}
        
        recorder.start_recording(mock_window)
        
        assert recorder.recording is True
        assert recorder.window_info == mock_window
        assert recorder.start_time == 100.0
        assert recorder.actions == []
        mock_mouse_listener.assert_called_once()
        mock_keyboard_listener.assert_called_once()

    def test_stop_recording(self, recorder):
        """Test stopping recording."""
        # Mock listeners
        mock_mouse_listener = Mock()
        mock_keyboard_listener = Mock()
        recorder.listener = (mock_mouse_listener, mock_keyboard_listener)
        recorder.recording = True
        
        recorder.stop_recording()
        
        assert recorder.recording is False
        mock_mouse_listener.stop.assert_called_once()
        mock_keyboard_listener.stop.assert_called_once()

    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.dump')
    def test_save_recording(self, mock_json_dump, mock_open, recorder):
        """Test saving recording to file."""
        recorder.actions = [
            {"type": "click", "x": 100, "y": 200},
            {"type": "type", "text": "test"}
        ]
        
        recorder.save_recording("test_recording.json")
        
        mock_open.assert_called_once_with("test_recording.json", 'w')
        expected_config = {
            "settings": {
                "default_wait": 0.5,
                "screenshot_on_error": True
            },
            "actions": recorder.actions
        }
        mock_json_dump.assert_called_once()
        assert mock_json_dump.call_args[0][0] == expected_config

    def test_clear_recording(self, recorder):
        """Test clearing recorded actions."""
        recorder.actions = [{"type": "click", "x": 100, "y": 200}]
        recorder.recording = True
        
        recorder.clear()
        
        assert recorder.actions == []
        assert recorder.recording is False

    @patch('time.time')
    def test_on_move_recording(self, mock_time, recorder):
        """Test recording mouse move events."""
        mock_time.return_value = 100.0
        recorder.recording = True
        recorder.record_mouse_move = True
        recorder.start_time = 95.0
        recorder.window_info = {"bounds": {"X": 0, "Y": 0}}
        
        recorder.on_move(150, 200)
        
        assert len(recorder.actions) == 1
        action = recorder.actions[0]
        assert action["type"] == "move"
        assert action["x"] == 150
        assert action["y"] == 200

    def test_on_move_not_recording(self, recorder):
        """Test that mouse moves are not recorded when disabled."""
        recorder.recording = True
        recorder.record_mouse_move = False
        
        recorder.on_move(150, 200)
        
        assert len(recorder.actions) == 0