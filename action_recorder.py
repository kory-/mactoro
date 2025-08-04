#!/usr/bin/env python3
import json
import time
import sys
import os
from datetime import datetime
import threading
import signal
import click
from typing import Dict, List, Any, Optional, Tuple
import Quartz
import AppKit
from pynput import mouse, keyboard
import pyautogui

class ActionRecorder:
    def __init__(self, window_name: Optional[str] = None, window_id: Optional[int] = None):
        self.window_name = window_name
        self.window_id = window_id
        self.target_window = None
        self.actions = []
        self.recording = False
        self.start_time = None
        self.last_action_time = None
        self.current_keys = set()
        self.mouse_pressed = False
        self.drag_start = None
        
        # Recording settings
        self.record_mouse_move = False
        self.min_wait_time = 0.1
        self.merge_similar_actions = True
        
        # Search for window
        if window_id:
            self.target_window = self._find_window_by_id(window_id)
            if not self.target_window:
                print(f"Window ID '{window_id}' not found")
                sys.exit(1)
            else:
                self.window_name = self.target_window.get('kCGWindowOwnerName', 'Unknown')
                bounds = self._get_window_bounds()
                print(f"Target window: {self.window_name} (ID: {window_id})")
                print(f"Window position: ({bounds[0]}, {bounds[1]}) Size: {bounds[2]}x{bounds[3]}")
                # Move focus to window
                self._focus_window()
        elif window_name:
            self.target_window = self._find_window(window_name)
            if not self.target_window:
                print(f"Window '{window_name}' not found")
                sys.exit(1)
            else:
                bounds = self._get_window_bounds()
                window_id = self.target_window.get('kCGWindowNumber', 0)
                print(f"対象ウィンドウ: {window_name} (ID: {window_id})")
                print(f"Window position: ({bounds[0]}, {bounds[1]}) Size: {bounds[2]}x{bounds[3]}")
                # Move focus to window
                self._focus_window()
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n\nRecording interrupted")
        self.stop_recording()
        sys.exit(0)
    
    def _find_window(self, window_name: str) -> Optional[Dict[str, Any]]:
        """Search for window with specified name"""
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID
        )
        
        print(f"\nSearching for available windows...")
        found_windows = []
        
        for window in windows:
            owner_name = window.get('kCGWindowOwnerName', '')
            window_title = window.get('kCGWindowName', '')
            
            # Display main windows for debugging
            if owner_name and (window_title or owner_name not in ['Window Server', 'Dock']):
                if window_name.lower() in owner_name.lower() or \
                   (window_title and window_name.lower() in window_title.lower()):
                    found_windows.append(window)
                    print(f"  ✓ Found: {owner_name} - {window_title or '(No title)'}")
        
        if found_windows:
            # Return the first window found
            return found_windows[0]
        
        # If not found, display list of available windows
        print(f"\n'{window_name}' not found. Available windows:")
        count = 0
        for window in windows:
            owner_name = window.get('kCGWindowOwnerName', '')
            window_title = window.get('kCGWindowName', '')
            if owner_name and owner_name not in ['Window Server', 'Dock', 'SystemUIServer', 'Control Center']:
                print(f"  - {owner_name}: {window_title or '(No title)'}")
                count += 1
                if count >= 10:  # Display up to 10 items
                    print("  ...")
                    break
        
        return None
    
    def _find_window_by_id(self, window_id: int) -> Optional[Dict[str, Any]]:
        """Search for window with specified ID"""
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID
        )
        
        for window in windows:
            if window.get('kCGWindowNumber') == window_id:
                return window
        return None
    
    def _get_window_bounds(self) -> Tuple[int, int, int, int]:
        """Get window position and size"""
        if self.target_window:
            bounds = self.target_window.get('kCGWindowBounds')
            x = int(bounds.get('X', 0))
            y = int(bounds.get('Y', 0))
            width = int(bounds.get('Width', 0))
            height = int(bounds.get('Height', 0))
            
            # Debug: Display actual values
            if hasattr(self, 'debug_bounds') and self.debug_bounds:
                print(f"[DEBUG] Window bounds: X={x}, Y={y}, Width={width}, Height={height}")
            
            return (x, y, width, height)
        return (0, 0, 0, 0)
    
    def _get_relative_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Calculate window relative coordinates"""
        if self.target_window:
            bounds = self._get_window_bounds()
            return x - bounds[0], y - bounds[1]
        return x, y
    
    def _focus_window(self):
        """Move focus to target window"""
        if not self.target_window:
            return
        
        try:
            pid = self.target_window.get('kCGWindowOwnerPID')
            if pid:
                app = AppKit.NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
                if app:
                    app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
                    time.sleep(0.5)
        except Exception as e:
            print(f"Window focus error: {e}")
    
    def _calculate_wait_time(self) -> float:
        """Calculate wait time from previous action"""
        if self.last_action_time is None:
            return 0
        
        wait_time = time.time() - self.last_action_time
        return max(wait_time, self.min_wait_time)
    
    def _add_action(self, action: Dict[str, Any]):
        """Record action"""
        if not self.recording:
            return
        
        # Calculate and add wait time
        if self.last_action_time:
            wait_time = self._calculate_wait_time()
            if wait_time > self.min_wait_time:
                action['wait'] = round(wait_time, 2)
        
        # Add timestamp
        action['timestamp'] = datetime.now().isoformat()
        
        # Add action
        self.actions.append(action)
        self.last_action_time = time.time()
        
        # Log output
        action_type = action['type']
        if action_type == 'click':
            x, y = action.get('x', 0), action.get('y', 0)
            if action.get('window_relative'):
                abs_x, abs_y = action.get('absolute_x', 0), action.get('absolute_y', 0)
                print(f"[Recording] Click: Window relative({x}, {y}) Screen absolute({abs_x}, {abs_y})")
            else:
                print(f"[Recording] Click: ({x}, {y})")
        elif action_type == 'type':
            text = action.get('text', '')
            print(f"[Recording] Text input: {text[:20]}{'...' if len(text) > 20 else ''}")
        elif action_type == 'hotkey':
            keys = action.get('keys', [])
            print(f"[Recording] Hotkey: {'+'.join(keys)}")
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Mouse click event handler"""
        if not self.recording:
            return
        
        if pressed:
            self.mouse_pressed = True
            self.drag_start = (x, y)
            
            # Display debug information (only on first click)
            if len(self.actions) == 0 and self.target_window:
                bounds = self._get_window_bounds()
                print(f"\n[DEBUG] First click:")
                print(f"  Absolute coordinates: ({x}, {y})")
                print(f"  Window position: ({bounds[0]}, {bounds[1]})")
                print(f"  Expected relative coordinates: ({x - bounds[0]}, {y - bounds[1]})")
                rel_x, rel_y = self._get_relative_coordinates(x, y)
                print(f"  Calculated relative coordinates: ({rel_x}, {rel_y})")
                print()
        else:
            self.mouse_pressed = False
            
            # Determine drag operation
            if self.drag_start and (abs(x - self.drag_start[0]) > 5 or abs(y - self.drag_start[1]) > 5):
                # Drag operation
                action = {
                    'type': 'drag',
                    'start_x': self.drag_start[0],
                    'start_y': self.drag_start[1],
                    'end_x': x,
                    'end_y': y,
                    'duration': 1.0
                }
                
                if self.target_window:
                    rel_start_x, rel_start_y = self._get_relative_coordinates(self.drag_start[0], self.drag_start[1])
                    rel_end_x, rel_end_y = self._get_relative_coordinates(x, y)
                    action.update({
                        'start_x': rel_start_x,
                        'start_y': rel_start_y,
                        'end_x': rel_end_x,
                        'end_y': rel_end_y,
                        'relative_to': 'window',
                        'window_relative': True,
                        'absolute_start_x': self.drag_start[0],
                        'absolute_start_y': self.drag_start[1],
                        'absolute_end_x': x,
                        'absolute_end_y': y
                    })
                
                self._add_action(action)
            else:
                # Click operation
                action = {'type': 'click'}
                
                if button == mouse.Button.right:
                    action['type'] = 'right_click'
                elif button == mouse.Button.middle:
                    action['type'] = 'middle_click'
                
                if self.target_window:
                    rel_x, rel_y = self._get_relative_coordinates(x, y)
                    action.update({
                        'x': rel_x,
                        'y': rel_y,
                        'relative_to': 'window',
                        'window_relative': True,
                        'absolute_x': x,
                        'absolute_y': y
                    })
                else:
                    action.update({
                        'x': x,
                        'y': y,
                        'window_relative': False
                    })
                
                self._add_action(action)
            
            self.drag_start = None
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Mouse scroll event handler"""
        if not self.recording:
            return
        
        action = {
            'type': 'scroll',
            'clicks': dy,  # Only vertical scroll supported
        }
        
        if self.target_window:
            rel_x, rel_y = self._get_relative_coordinates(x, y)
            action.update({
                'x': rel_x,
                'y': rel_y,
                'relative_to': 'window',
                'window_relative': True,
                'absolute_x': x,
                'absolute_y': y
            })
        else:
            action.update({
                'x': x,
                'y': y,
                'window_relative': False
            })
        
        self._add_action(action)
    
    def _on_key_press(self, key):
        """Key press event handler"""
        if not self.recording:
            return
        
        # Process special keys
        if hasattr(key, 'name'):
            self.current_keys.add(key.name)
        elif hasattr(key, 'char') and key.char:
            self.current_keys.add(key.char)
    
    def _on_key_release(self, key):
        """Key release event handler"""
        if not self.recording:
            return
        
        # Stop recording with ESC key
        if key == keyboard.Key.esc:
            print("\nESC key pressed. Stopping recording...")
            self.stop_recording()
            return False
        
        # Check key combinations
        if len(self.current_keys) > 1:
            # Hotkey
            keys = list(self.current_keys)
            action = {
                'type': 'hotkey',
                'keys': keys
            }
            self._add_action(action)
        elif len(self.current_keys) == 1:
            # Single key
            key_name = list(self.current_keys)[0]
            
            # For special keys
            if key_name in ['space', 'enter', 'tab', 'backspace', 'delete']:
                action = {
                    'type': 'hotkey',
                    'keys': [key_name]
                }
                self._add_action(action)
            # For regular characters
            elif len(key_name) == 1:
                # Merge with last action if it's a type action
                if (self.merge_similar_actions and 
                    self.actions and 
                    self.actions[-1]['type'] == 'type' and
                    time.time() - self.last_action_time < 0.5):
                    self.actions[-1]['text'] += key_name
                    self.last_action_time = time.time()
                else:
                    action = {
                        'type': 'type',
                        'text': key_name
                    }
                    self._add_action(action)
        
        # Clear keys
        if hasattr(key, 'name'):
            self.current_keys.discard(key.name)
        elif hasattr(key, 'char') and key.char:
            self.current_keys.discard(key.char)
    
    def start_recording(self):
        """Start recording"""
        self.recording = True
        self.start_time = time.time()
        self.last_action_time = time.time()
        
        print("\n=== Started recording operations ===")
        print("Press ESC key to stop recording")
        if self.window_name:
            print(f"Target window: {self.window_name}")
            if self.target_window:
                print(f"Window detection: Success")
            else:
                print(f"Window detection: Failed")
        else:
            print("Full screen mode (recording with absolute coordinates)")
        print("Recording...\n")
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        # Wait for listener to finish
        self.keyboard_listener.join()
    
    def stop_recording(self):
        """Stop recording"""
        self.recording = False
        
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        
        total_time = time.time() - self.start_time if self.start_time else 0
        print(f"\nRecording stopped")
        print(f"Recording time: {total_time:.1f} seconds")
        print(f"Number of recorded actions: {len(self.actions)}")
    
    def save_to_json(self, filename: str):
        """Save recorded actions to JSON format"""
        # Convert to window_controller.py compatible format
        config = {
            "settings": {
                "default_wait": 0.5,
                "screenshot_on_error": True,
                "max_runtime": 3600
            },
            "actions": self.actions,
            "metadata": {
                "recorded_at": datetime.now().isoformat(),
                "window_name": self.window_name,
                "total_actions": len(self.actions),
                "recording_duration": time.time() - self.start_time if self.start_time else 0
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\nRecording saved to file: {filename}")
        print(f"Execution command: python window_controller.py run --window \"{self.window_name or 'Window name'}\" --config {filename}")

@click.group()
def cli():
    """Operation recording tool"""
    pass

@cli.command()
def list_windows():
    """Display list of available windows"""
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )
    
    print("\nCurrently open windows:")
    print("-" * 60)
    
    window_list = []
    for window in windows:
        owner_name = window.get('kCGWindowOwnerName', '')
        window_title = window.get('kCGWindowName', '')
        window_id = window.get('kCGWindowNumber', 0)
        if owner_name and owner_name not in ['Window Server', 'Dock', 'SystemUIServer', 'Control Center']:
            bounds = window.get('kCGWindowBounds', {})
            window_list.append({
                'id': window_id,
                'app': owner_name,
                'title': window_title or '(No title)',
                'x': int(bounds.get('X', 0)),
                'y': int(bounds.get('Y', 0)),
                'width': int(bounds.get('Width', 0)),
                'height': int(bounds.get('Height', 0))
            })
    
    # Sort by app name
    window_list.sort(key=lambda x: x['app'])
    
    for w in window_list:
        print(f"ID: {w['id']:<6} | {w['app']:<20} | {w['title']:<30}")
        print(f"{'':10} | Position: ({w['x']}, {w['y']}) Size: {w['width']}x{w['height']}")
        print("-" * 60)
    
    print(f"\nTotal: {len(window_list)} windows")

@cli.command()
@click.option('--window', '-w', help='Target window name (defaults to full screen)')
@click.option('--window-id', '-i', type=int, help='Target window ID (check with window_controller.py list)')
@click.option('--output', '-o', default=None, help='Output file name (auto-generated if not specified)')
@click.option('--no-merge', is_flag=True, help='Do not merge consecutive actions of the same type')
@click.option('--record-mouse-move', is_flag=True, help='Also record mouse movements')
def record(window, window_id, output, no_merge, record_mouse_move):
    """Record operations and save to JSON file"""
    # Generate output file name
    if not output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = f"recording_{timestamp}.json"
    
    # Create recorder
    recorder = ActionRecorder(window_name=window, window_id=window_id)
    recorder.merge_similar_actions = not no_merge
    recorder.record_mouse_move = record_mouse_move
    
    # Start recording
    try:
        recorder.start_recording()
    except KeyboardInterrupt:
        pass
    finally:
        recorder.stop_recording()
        
        # Save to file
        if recorder.actions:
            recorder.save_to_json(output)
        else:
            print("\nNo actions were recorded")

if __name__ == '__main__':
    cli()