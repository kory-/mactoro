#!/usr/bin/env python3
import click
import json
import time
import sys
import os
from datetime import datetime
import pyautogui
import Quartz
import AppKit
from typing import Dict, List, Any, Optional, Tuple
import threading
import signal
from pynput import keyboard
# Remove coordinate_helper import - use lazy import when needed

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0
# macOS specific settings for better drag support
pyautogui.DARWIN_CATCH_UP_TIME = 0.01

class WindowController:
    def __init__(self):
        self.running = True
        self.recorded_coordinates = {}
        self.current_window = None
        self.debug = False
        self.screenshot_on_error = True
        self.action_history = []
        self.keyboard_listener = None
        self.target_window = None
        self.window_focused = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n\nInterrupted")
        self.running = False
        sys.exit(0)
    
    def _on_key_press(self, key):
        """Keyboard event handler"""
        try:
            if key == keyboard.Key.esc:
                print("\n\nESC key pressed - interrupting process")
                self.running = False
                return False  # Stop listener
        except AttributeError:
            pass
    
    def list_windows(self) -> List[Dict[str, Any]]:
        """Get list of currently open windows"""
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID
        )
        
        window_list = []
        for window in windows:
            owner_name = window.get('kCGWindowOwnerName', 'Unknown')
            window_name = window.get('kCGWindowName', '<no name>')
            window_number = window.get('kCGWindowNumber', '?')
            pid = window.get('kCGWindowOwnerPID', '?')
            
            bounds = window.get('kCGWindowBounds')
            if bounds:
                x = int(bounds.get('X', 0))
                y = int(bounds.get('Y', 0))
                width = int(bounds.get('Width', 0))
                height = int(bounds.get('Height', 0))
                bounds_info = {'x': x, 'y': y, 'width': width, 'height': height}
            else:
                bounds_info = None
            
            window_info = {
                'owner_name': owner_name,
                'window_name': window_name,
                'window_id': window_number,
                'pid': pid,
                'bounds': bounds_info
            }
            
            window_list.append(window_info)
        
        return window_list
    
    def find_window(self, window_name: str = None, window_id: int = None) -> Optional[Dict[str, Any]]:
        """Search for window with specified name or ID"""
        windows = self.list_windows()
        
        # Search by ID
        if window_id:
            for window in windows:
                if window['window_id'] == window_id:
                    return window
        
        # Search by name (prioritize exact match)
        if window_name:
            # Try exact match first
            for window in windows:
                if window_name.lower() == window['owner_name'].lower() or \
                   window_name.lower() == window['window_name'].lower():
                    return window
            
            # Try partial match
            for window in windows:
                if window_name.lower() in window['owner_name'].lower() or \
                   window_name.lower() in window['window_name'].lower():
                    return window
        
        return None
    
    def take_window_screenshot(self, window: Dict[str, Any] = None, filename: str = None) -> str:
        """Take screenshot of specific window or entire screen"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{timestamp}.png"
        
        if window and window.get('bounds'):
            # Take screenshot of specific window
            bounds = window['bounds']
            x = int(bounds['x'])
            y = int(bounds['y']) 
            width = int(bounds['width'])
            height = int(bounds['height'])
            
            # Take screenshot of the window region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot.save(filename)
            if self.debug:
                print(f"Window screenshot saved: {filename} (region: {x},{y} {width}x{height})")
        else:
            # Take full screen screenshot if no window specified
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            if self.debug:
                print(f"Full screen screenshot saved: {filename}")
        
        return filename
    
    def focus_window(self, window: Dict[str, Any]) -> bool:
        """Move focus to specified window"""
        try:
            pid = window['pid']
            
            app = AppKit.NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
            if app:
                app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
                # Don't wait here as JSON's default_wait will be used
                return True
        except Exception as e:
            if self.debug:
                print(f"Window focus error: {e}")
        return False
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_coordinates(self, coord_path: str) -> Dict[str, Dict[str, Any]]:
        """Load coordinate definition file"""
        with open(coord_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            coordinates = {}
            for point in data.get('recorded_points', []):
                coordinates[point['name']] = point
            return coordinates
    
    def resolve_coordinates(self, action: Dict[str, Any]) -> Tuple[int, int]:
        """Resolve coordinates from action"""
        if 'coordinate' in action:
            coord_name = action['coordinate']
            if coord_name in self.recorded_coordinates:
                coord = self.recorded_coordinates[coord_name]
                x, y = coord['x'], coord['y']
                
                if coord.get('window_relative') and self.current_window:
                    bounds = self.current_window['bounds']
                    x += bounds['x']
                    y += bounds['y']
                
                return x, y
            else:
                raise ValueError(f"Coordinate '{coord_name}' not found")
        
        x = action.get('x', 0)
        y = action.get('y', 0)
        
        if action.get('relative_to') == 'window' and self.current_window:
            bounds = self.current_window['bounds']
            x += bounds['x']
            y += bounds['y']
        
        return x, y
    
    def wait_for_condition(self, condition: Dict[str, Any], timeout: float = 10) -> bool:
        """Wait until condition is met"""
        start_time = time.time()
        condition_type = condition['type']
        
        while time.time() - start_time < timeout:
            if not self.running:
                return False
            
            if condition_type == 'color_match':
                x, y = self.resolve_coordinates(condition)
                expected_color = condition['color']
                tolerance = condition.get('tolerance', 10)
                
                screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
                actual_color = list(screenshot.getpixel((0, 0)))
                
                if all(abs(a - e) <= tolerance for a, e in zip(actual_color, expected_color)):
                    return True
            
            elif condition_type == 'window_exists':
                window_name = condition['window_name']
                if self.find_window(window_name):
                    return True
            
            elif condition_type == 'image_exists':
                pass
            
            elif condition_type == 'time_elapsed':
                elapsed = condition['seconds']
                if time.time() - start_time >= elapsed:
                    return True
            
            time.sleep(0.01)  # Shorter polling interval
        
        return False
    
    def execute_action(self, action: Dict[str, Any]) -> Any:
        """Execute a single action"""
        if not self.running:
            return None
        
        action_type = action['type']
        
        # Get timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if self.debug:
            print(f"Executing: {action_type} - {action}")
        
        result = None
        
        try:
            if action_type == 'click':
                x, y = self.resolve_coordinates(action)
                pyautogui.click(x, y)
                # Build action info
                action_info = f"Click: ({x}, {y})"
                if 'comment' in action:
                    action_info += f" - {action['comment']}"
            
            elif action_type == 'double_click':
                x, y = self.resolve_coordinates(action)
                pyautogui.doubleClick(x, y)
                # Build action info
                action_info = f"Double click: ({x}, {y})"
                if 'comment' in action:
                    action_info += f" - {action['comment']}"
            
            elif action_type == 'right_click':
                x, y = self.resolve_coordinates(action)
                pyautogui.rightClick(x, y)
                # Build action info
                action_info = f"Right click: ({x}, {y})"
                if 'comment' in action:
                    action_info += f" - {action['comment']}"
            
            elif action_type == 'type':
                text = action['text']
                interval = action.get('interval', 0)
                pyautogui.typewrite(text, interval=interval)
            
            elif action_type == 'hotkey':
                keys = action['keys']
                pyautogui.hotkey(*keys)
            
            elif action_type == 'drag':
                # For drag operations, we need to handle start and end coordinates separately
                # Create temporary action objects for coordinate resolution
                start_action = {'x': action.get('start_x', 0), 'y': action.get('start_y', 0)}
                if action.get('relative_to') == 'window':
                    start_action['relative_to'] = 'window'
                
                start_x, start_y = self.resolve_coordinates(start_action)
                
                # Resolve end coordinates
                end_action = {'x': action.get('end_x', start_x + 100), 'y': action.get('end_y', start_y)}
                if action.get('relative_to') == 'window':
                    end_action['relative_to'] = 'window'
                    
                end_x, end_y = self.resolve_coordinates(end_action)
                
                duration = action.get('duration', 1.0)
                button = action.get('button', 'left')  # Default to left button
                comment = action.get('comment', '')
                
                action_info = f"Drag from ({start_x:.0f}, {start_y:.0f}) to ({end_x:.0f}, {end_y:.0f})"
                if comment:
                    action_info += f" - {comment}"
                    
                print(f"[{timestamp}] {action_info} (wait: {action.get('wait', 0)} seconds)")
                
                if self.debug:
                    print(f"[DEBUG] Drag: ({start_x}, {start_y}) → ({end_x}, {end_y}), {duration}s")
                    
                # Quick validation only
                if self.target_window and action.get('window_relative') and action.get('start_y', start_y) < 50:
                    print("  ⚠️  WARNING: Drag near window top!")
                
                # Ensure window is active before drag (only if needed)
                if self.current_window and not self.window_focused:
                    self.focus_window(self.current_window)
                    time.sleep(0.1)  # Minimal delay for focus
                    self.window_focused = True
                
                # Scale delays based on duration
                move_duration = min(0.1, duration * 0.1)  # 10% of duration, max 0.1s
                delay = min(0.05, duration * 0.05)  # 5% of duration, max 0.05s
                
                # Move to start position
                pyautogui.moveTo(start_x, start_y, duration=move_duration)
                time.sleep(delay)
                
                # Click to ensure focus on element
                pyautogui.click(start_x, start_y, button=button)
                time.sleep(delay)
                
                # Perform drag
                try:
                    pyautogui.dragTo(end_x, end_y, duration=duration, button=button)
                except Exception as e:
                    print(f"  dragTo failed: {e}, using fallback...")
                    pyautogui.mouseDown(start_x, start_y, button=button)
                    time.sleep(delay)
                    pyautogui.moveTo(end_x, end_y, duration=duration)
                    time.sleep(delay)
                    pyautogui.mouseUp(end_x, end_y, button=button)
                
                print(f"  Drag completed")
            
            elif action_type == 'scroll':
                clicks = action.get('clicks', 1)
                x, y = self.resolve_coordinates(action) if 'x' in action else pyautogui.position()
                pyautogui.scroll(clicks, x=x, y=y)
            
            elif action_type == 'wait':
                seconds = action.get('seconds', 1)
                action_info = f"Wait {seconds} seconds"
                if 'comment' in action:
                    action_info += f" - {action['comment']}"
                time.sleep(seconds)
            
            elif action_type == 'wait_for_color':
                timeout = action.get('timeout', 10)
                self.wait_for_condition(action, timeout)
            
            elif action_type == 'wait_for_window':
                window_name = action['window_name']
                timeout = action.get('timeout', 10)
                self.wait_for_condition({'type': 'window_exists', 'window_name': window_name}, timeout)
            
            elif action_type == 'screenshot':
                filename = action.get('filename', f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                screenshot = pyautogui.screenshot()
                screenshot.save(filename)
                print(f"Screenshot saved: {filename}")
            
            elif action_type == 'log':
                message = action.get('message', '')
                print(f"[LOG] {message}")
            
            elif action_type == 'loop':
                max_iterations = action.get('max_iterations', 10)
                actions = action.get('actions', [])
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Loop started (max {max_iterations} times)")
                
                for i in range(max_iterations):
                    if not self.running:
                        break
                    if i % 10 == 0 or self.debug:  # Show progress every 10 iterations or in debug mode
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Loop {i + 1}/{max_iterations}")
                    for sub_action in actions:
                        self.execute_action(sub_action)
            
            elif action_type == 'loop_until':
                condition = action['condition']
                timeout = action.get('timeout', 30)
                actions = action.get('actions', [])
                start_time = time.time()
                
                while not self.wait_for_condition(condition, 0.1):
                    if not self.running or time.time() - start_time > timeout:
                        break
                    for sub_action in actions:
                        self.execute_action(sub_action)
            
            elif action_type == 'conditional':
                condition = action['condition']
                if self.wait_for_condition(condition, 0.1):
                    for sub_action in action.get('if_true', []):
                        self.execute_action(sub_action)
                else:
                    for sub_action in action.get('if_false', []):
                        self.execute_action(sub_action)
            
            elif action_type == 'exit_if':
                condition = action['condition']
                if self.wait_for_condition(condition, 0.1):
                    exit_code = action.get('exit_code', 0)
                    message = action.get('message', 'Exit condition met')
                    print(f"\n{message}")
                    sys.exit(exit_code)
            
            elif action_type == 'click_on_color':
                color = action['color']
                tolerance = action.get('tolerance', 10)
                search_region = action.get('search_region')
                
                if search_region:
                    screenshot = pyautogui.screenshot(region=tuple(search_region))
                    offset_x, offset_y = search_region[0], search_region[1]
                else:
                    screenshot = pyautogui.screenshot()
                    offset_x, offset_y = 0, 0
                
                width, height = screenshot.size
                found = False
                
                for y in range(height):
                    for x in range(width):
                        pixel_color = list(screenshot.getpixel((x, y)))
                        if all(abs(p - c) <= tolerance for p, c in zip(pixel_color, color)):
                            pyautogui.click(x + offset_x, y + offset_y)
                            found = True
                            break
                    if found:
                        break
                
                if not found and self.debug:
                    print(f"Color {color} not found")
            
            # Add wait info
            wait_info = ""
            wait_time = action.get('wait', None)
            if wait_time is not None:
                if wait_time > 0:
                    wait_info = f" (wait: {wait_time} seconds)"
                    time.sleep(wait_time)
                else:
                    wait_info = " (wait: 0 seconds)"
            elif hasattr(self, '_default_wait') and self._default_wait > 0:
                wait_info = f" (default_wait: {self._default_wait} seconds)"
            
            # Final output (only if action exists)
            if 'action_info' in locals():
                print(f"[{timestamp}] {action_info}{wait_info}")
            elif 'comment' in action and action_type not in ['click', 'double_click', 'right_click']:
                # For non-click actions with comments
                print(f"[{timestamp}] {action['comment']}{wait_info}")
            
            self.action_history.append({
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'result': result
            })
            
        except Exception as e:
            print(f"Action error: {action_type} - {e}")
            if self.screenshot_on_error:
                error_screenshot = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.take_window_screenshot(self.target_window, error_screenshot)
                print(f"Error screenshot saved: {error_screenshot}")
                if self.target_window:
                    print(f"  Window: {self.target_window.get('owner_name', 'Unknown')} - {self.target_window.get('window_name', 'Unknown')}")
            raise
        
        return result
    
    def run_automation(self, window_name: str = None, window_id: int = None, 
                      config_path: str = None, coordinates_path: str = None,
                      debug: bool = False):
        """Execute automation"""
        self.debug = debug
        
        # Start ESC key monitoring listener
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()
        print("Press ESC to interrupt")
        
        if window_name or window_id:
            self.current_window = self.find_window(window_name, window_id)
            if not self.current_window:
                print(f"Window not found")
                self.keyboard_listener.stop()
                sys.exit(1)
            
            # Set target window for screenshot on error
            self.target_window = self.current_window
            
            print(f"Target window: {self.current_window['owner_name']} - {self.current_window['window_name']}")
            bounds = self.current_window.get('bounds')
            if bounds:
                print(f"Window position: ({bounds['x']}, {bounds['y']}) Size: {bounds['width']}x{bounds['height']}")
            
            if not self.focus_window(self.current_window):
                print("Could not focus on window")
        
        if coordinates_path and os.path.exists(coordinates_path):
            self.recorded_coordinates = self.load_coordinates(coordinates_path)
            print(f"Loaded coordinate definitions: {len(self.recorded_coordinates)} items")
        
        config = self.load_config(config_path)
        
        settings = config.get('settings', {})
        self.screenshot_on_error = settings.get('screenshot_on_error', True)
        default_wait = settings.get('default_wait', 0)
        max_runtime = settings.get('max_runtime', 3600)
        
        # Save default_wait as instance variable
        self._default_wait = default_wait
        
        pyautogui.PAUSE = default_wait
        
        actions = config.get('actions', [])
        
        print(f"\ndefault_wait: {default_wait} seconds")
        print(f"Executing {len(actions)} actions...")
        
        start_time = time.time()
        
        try:
            for i, action in enumerate(actions):
                if not self.running:
                    break
                
                if time.time() - start_time > max_runtime:
                    print(f"\nExceeded maximum runtime ({max_runtime} seconds)")
                    break
                
                if self.debug:
                    print(f"\nAction {i + 1}/{len(actions)}")
                
                self.execute_action(action)
            
            if self.running:
                print(f"\nCompleted: Executed {len(self.action_history)} actions")
            else:
                print(f"\nInterrupted: Executed {len(self.action_history)} actions")
            
        except Exception as e:
            print(f"\nError occurred: {e}")
            sys.exit(1)
        finally:
            # Stop listener
            if self.keyboard_listener and self.keyboard_listener.is_alive():
                self.keyboard_listener.stop()


def list_windows_cli():
    """Display list of currently open windows"""
    controller = WindowController()
    windows = controller.list_windows()
    
    print(f"\nCurrently open windows: {len(windows)}\n")
    print(f"{'ID':<8} {'PID':<8} {'Application':<20} {'Window Title':<30} {'Position and Size'}")
    print("-" * 100)
    
    for window in windows:
        window_id = window['window_id']
        pid = window['pid']
        owner = window['owner_name'][:20]
        title = window['window_name'][:30]
        
        bounds = window['bounds']
        if bounds:
            position = f"({bounds['x']}, {bounds['y']}) {bounds['width']}x{bounds['height']}"
        else:
            position = "N/A"
        
        print(f"{window_id:<8} {pid:<8} {owner:<20} {title:<30} {position}")

def record_cli(window, fullscreen, output):
    """Coordinate recording mode"""
    from .coordinate_helper import CoordinateRecorder
    recorder = CoordinateRecorder(
        window_name=window,
        fullscreen=fullscreen
    )
    recorder.run_interactive_mode()

def run_cli(window, window_id, config, coordinates, debug):
    """Execute automation based on configuration file"""
    if not window and not window_id:
        print("Error: Please specify --window or --window-id")
        sys.exit(1)
    
    controller = WindowController()
    controller.run_automation(
        window_name=window,
        window_id=window_id,
        config_path=config,
        coordinates_path=coordinates,
        debug=debug
    )

def capture_cli(window, analyze):
    """Take a screenshot"""
    from .coordinate_helper import ScreenshotAnalyzer
    analyzer = ScreenshotAnalyzer(window_name=window)
    filename = analyzer.capture_screenshot()
    
    if filename and analyze:
        analyzer.analyze_with_gui(filename)

def analyze_cli(image):
    """Analyze screenshot"""
    if not os.path.exists(image):
        print(f"Error: Image file '{image}' not found")
        sys.exit(1)
    
    from .coordinate_helper import ScreenshotAnalyzer
    analyzer = ScreenshotAnalyzer()
    analyzer.analyze_with_gui(image)

def generate_config_cli(coordinates, output):
    """Generate configuration file template from coordinate definitions"""
    with open(coordinates, 'r', encoding='utf-8') as f:
        coord_data = json.load(f)
    
    config = {
        "settings": {
            "default_wait": 0,
            "screenshot_on_error": True,
            "max_runtime": 3600
        },
        "actions": []
    }
    
    for point in coord_data.get('recorded_points', []):
        config['actions'].append({
            "type": "click",
            "coordinate": point['name'],
            "wait": 1,
            "comment": f"Coordinate: ({point['x']}, {point['y']}) - Color: RGB{point['color']}"
        })
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"Generated configuration file: {output}")

