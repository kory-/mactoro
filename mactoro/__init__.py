"""Mactoro - A powerful macOS automation tool"""

__version__ = "0.1.0"
__author__ = "Shimono"
__email__ = "momo0907@gmail.com"

# Use lazy imports to avoid unnecessary warnings
def __getattr__(name):
    if name == 'WindowController':
        from .window_controller import WindowController
        return WindowController
    elif name == 'ActionRecorder':
        from .action_recorder import ActionRecorder
        return ActionRecorder
    elif name == 'CoordinateRecorder':
        from .coordinate_helper import CoordinateRecorder
        return CoordinateRecorder
    elif name == 'ScreenshotAnalyzer':
        from .coordinate_helper import ScreenshotAnalyzer
        return ScreenshotAnalyzer
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['WindowController', 'ActionRecorder', 'CoordinateRecorder', 'ScreenshotAnalyzer']