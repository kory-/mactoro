"""Tests for CLI module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from mactoro.cli import main, window, action, coordinate


class TestCLI:
    """Test cases for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_main_command(self, runner):
        """Test main command shows help."""
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'Mactoro - macOS automation tool' in result.output

    @patch('mactoro.window_controller.WindowController.list_windows')
    def test_window_list_command(self, mock_list_windows, runner):
        """Test window list command."""
        mock_list_windows.return_value = [
            {
                "window_id": 123,
                "app_name": "TestApp",
                "window_name": "Test Window",
                "bounds": {"X": 100, "Y": 200, "Width": 800, "Height": 600}
            }
        ]
        
        result = runner.invoke(window, ['list'])
        assert result.exit_code == 0
        assert "TestApp" in result.output
        assert "Test Window" in result.output
        assert "123" in result.output

    @patch('mactoro.window_controller.WindowController.find_window')
    @patch('mactoro.window_controller.WindowController.run_config')
    def test_action_run_command(self, mock_run_config, mock_find_window, runner):
        """Test action run command."""
        mock_find_window.return_value = {"window_id": 123}
        
        with runner.isolated_filesystem():
            # Create a test config file
            with open('test_config.json', 'w') as f:
                f.write('{"actions": []}')
            
            result = runner.invoke(action, ['run', '--window', 'TestWindow', '--config', 'test_config.json'])
            assert result.exit_code == 0
            mock_find_window.assert_called_once_with("TestWindow")
            mock_run_config.assert_called_once()

    @patch('mactoro.window_controller.WindowController.find_window')
    @patch('mactoro.action_recorder.ActionRecorder.start_recording')
    @patch('mactoro.action_recorder.ActionRecorder.stop_recording')
    @patch('mactoro.action_recorder.ActionRecorder.save_recording')
    @patch('builtins.input', return_value='')
    def test_action_record_command(self, mock_input, mock_save, mock_stop, mock_start, mock_find_window, runner):
        """Test action record command."""
        mock_find_window.return_value = {"window_id": 123, "window_name": "Test Window"}
        
        result = runner.invoke(action, ['record', '--window', 'TestWindow', '--output', 'recording.json'])
        assert result.exit_code == 0
        mock_find_window.assert_called_once_with("TestWindow")
        mock_start.assert_called_once()
        mock_stop.assert_called_once()
        mock_save.assert_called_once_with('recording.json')

    @patch('mactoro.coordinate_helper.CoordinateRecorder.record_coordinates')
    def test_coordinate_record_command(self, mock_record, runner):
        """Test coordinate record command."""
        mock_record.return_value = [
            {"name": "button", "x": 100, "y": 200, "color": [255, 0, 0]}
        ]
        
        result = runner.invoke(coordinate, ['record'])
        assert result.exit_code == 0
        mock_record.assert_called_once()

    @patch('mactoro.coordinate_helper.ScreenshotAnalyzer.capture_screenshot')
    def test_coordinate_capture_command(self, mock_capture, runner):
        """Test coordinate capture command."""
        result = runner.invoke(coordinate, ['capture', '--output', 'screenshot.png'])
        assert result.exit_code == 0
        mock_capture.assert_called_once()

    @patch('mactoro.coordinate_helper.ScreenshotAnalyzer.analyze_screenshot')
    @patch('PIL.Image.open')
    def test_coordinate_analyze_command(self, mock_image_open, mock_analyze, runner):
        """Test coordinate analyze command."""
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        
        with runner.isolated_filesystem():
            # Create a dummy image file
            with open('test_image.png', 'wb') as f:
                f.write(b'dummy')
            
            result = runner.invoke(coordinate, ['analyze', '--image', 'test_image.png'])
            assert result.exit_code == 0
            mock_analyze.assert_called_once_with(mock_image)

    def test_action_run_missing_config(self, runner):
        """Test action run command with missing config file."""
        result = runner.invoke(action, ['run', '--window', 'TestWindow', '--config', 'nonexistent.json'])
        assert result.exit_code != 0
        assert 'Error' in result.output

    def test_window_specific_option(self, runner):
        """Test window-specific options."""
        result = runner.invoke(window, ['--help'])
        assert result.exit_code == 0
        assert 'list' in result.output

    @patch('json.dump')
    @patch('builtins.open', new_callable=MagicMock)
    def test_generate_config_command(self, mock_open, mock_json_dump, runner):
        """Test generate-config command."""
        with runner.isolated_filesystem():
            # Create a test coordinates file
            coords_data = [
                {"name": "button1", "x": 100, "y": 200},
                {"name": "button2", "x": 300, "y": 400}
            ]
            with open('coords.json', 'w') as f:
                import json
                json.dump(coords_data, f)
            
            result = runner.invoke(main, ['generate-config', '--coordinates', 'coords.json', '--output', 'config.json'])
            assert result.exit_code == 0
            assert mock_json_dump.called