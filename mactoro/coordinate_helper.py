#!/usr/bin/env python3
try:
    import tkinter as tk
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Warning: tkinter is not available. Coordinate overlay display feature will be disabled.")
import pyautogui
import json
import sys
from datetime import datetime
import threading
import time
from PIL import Image, ImageDraw
try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None
import os
import tempfile
import Quartz
from pynput import mouse, keyboard

class CoordinateRecorder:
    def __init__(self, window_name=None, fullscreen=False):
        self.window_name = window_name
        self.fullscreen = fullscreen
        self.recorded_points = []
        self.running = True
        self.overlay = None
        self.target_window = None
        self.show_coordinates_in_terminal = False
        self.last_coordinates = None
        
        if window_name:
            self.target_window = self._find_window(window_name)
            if not self.target_window:
                print(f"Window '{window_name}' not found")
                sys.exit(1)
    
    def _find_window(self, window_name):
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID
        )
        
        for window in windows:
            if window_name.lower() in window.get('kCGWindowOwnerName', '').lower() or \
               window_name.lower() in window.get('kCGWindowName', '').lower():
                return window
        return None
    
    def _get_window_bounds(self):
        if self.target_window:
            bounds = self.target_window.get('kCGWindowBounds')
            return (
                int(bounds.get('X', 0)),
                int(bounds.get('Y', 0)),
                int(bounds.get('Width', 0)),
                int(bounds.get('Height', 0))
            )
        return None
    
    def _get_relative_coordinates(self, x, y):
        if self.target_window:
            bounds = self._get_window_bounds()
            if bounds:
                return x - bounds[0], y - bounds[1]
        return x, y
    
    def _get_pixel_color(self, x, y):
        try:
            screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
            return list(screenshot.getpixel((0, 0)))
        except:
            return [0, 0, 0]
    
    def record_point(self, x, y, name=None):
        color = self._get_pixel_color(x, y)
        
        if self.target_window:
            rel_x, rel_y = self._get_relative_coordinates(x, y)
            point = {
                "name": name or f"point_{len(self.recorded_points) + 1}",
                "x": rel_x,
                "y": rel_y,
                "absolute_x": x,
                "absolute_y": y,
                "color": color,
                "window_relative": True,
                "window_name": self.window_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            point = {
                "name": name or f"point_{len(self.recorded_points) + 1}",
                "x": x,
                "y": y,
                "color": color,
                "window_relative": False,
                "timestamp": datetime.now().isoformat()
            }
        
        self.recorded_points.append(point)
        print(f"Recorded: {point['name']} - Coordinates: ({point['x']}, {point['y']}) - Color: RGB{tuple(color)}")
        return point
    
    def save_recorded_points(self, filename=None):
        if not filename:
            filename = f"coordinates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "recorded_points": self.recorded_points,
                "window_name": self.window_name,
                "recorded_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\nCoordinates saved to {filename}")
        return filename
    
    def _update_terminal_coordinates(self):
        """Display coordinates in terminal"""
        while self.running and self.show_coordinates_in_terminal:
            x, y = pyautogui.position()
            
            info = f"Screen coordinates: ({x}, {y})"
            
            if self.target_window:
                bounds = self._get_window_bounds()
                if bounds:
                    rel_x, rel_y = self._get_relative_coordinates(x, y)
                    info += f" | Window relative: ({rel_x}, {rel_y})"
            
            try:
                color = self._get_pixel_color(x, y)
                info += f" | Color: RGB{tuple(color)}"
            except:
                pass
            
            # カーソル位置を同じ行に更新
            if self.last_coordinates != info:
                print(f"\r{info}          ", end='', flush=True)
                self.last_coordinates = info
            
            time.sleep(0.05)
    
    def run_interactive_mode(self):
        print("\n=== Coordinate Recording Mode ===")
        print("Instructions:")
        print("  - Left mouse click: Record coordinates")
        print("  - Right mouse click: Record coordinates and color information in detail")
        print("  - ESC key: Stop recording")
        print("  - S key: Save current recording")
        
        if self.window_name:
            print(f"\nTarget window: {self.window_name}")
            bounds = self._get_window_bounds()
            if bounds:
                print(f"Window position: ({bounds[0]}, {bounds[1]}) Size: {bounds[2]}x{bounds[3]}")
        
        print("\nStarting recording...\n")
        
        self.start_overlay()
        
        # ターミナルでの座標表示を開始
        if self.show_coordinates_in_terminal:
            coord_thread = threading.Thread(target=self._update_terminal_coordinates)
            coord_thread.daemon = True
            coord_thread.start()
        
        def on_click(x, y, button, pressed):
            if pressed:
                if self.show_coordinates_in_terminal:
                    print()  # 新しい行に移動
                if button == mouse.Button.left:
                    self.record_point(x, y)
                elif button == mouse.Button.right:
                    name = f"detailed_point_{len(self.recorded_points) + 1}"
                    self.record_point(x, y, name)
        
        def on_key_press(key):
            try:
                if key == keyboard.Key.esc:
                    self.running = False
                    return False
                elif hasattr(key, 'char') and key.char == 's':
                    if self.show_coordinates_in_terminal:
                        print()  # 新しい行に移動
                    self.save_recorded_points()
            except:
                pass
        
        mouse_listener = mouse.Listener(on_click=on_click)
        keyboard_listener = keyboard.Listener(on_press=on_key_press)
        
        mouse_listener.start()
        keyboard_listener.start()
        
        try:
            keyboard_listener.join()
        finally:
            self.running = False
            mouse_listener.stop()
            self.stop_overlay()
            
            if self.show_coordinates_in_terminal:
                print()  # 新しい行に移動
            
            if self.recorded_points:
                filename = self.save_recorded_points()
                print(f"\nTotal {len(self.recorded_points)} coordinates recorded")

    def start_overlay(self):
        if TKINTER_AVAILABLE:
            # macOSではtkinterをメインスレッドで実行する必要があるため、オーバーレイは無効
            if sys.platform == 'darwin':
                print("On macOS, coordinate overlay runs in a separate process.")
                print("Current mouse coordinates will be displayed in the terminal.")
                self.show_coordinates_in_terminal = True
            else:
                def create_overlay():
                    self.overlay = CoordinateOverlay(self.target_window)
                    self.overlay.run()
                
                overlay_thread = threading.Thread(target=create_overlay)
                overlay_thread.daemon = True
                overlay_thread.start()
        else:
            print("Coordinate overlay is not available, but coordinate recording functions.")
    
    def stop_overlay(self):
        if self.overlay:
            self.overlay.stop()

class CoordinateOverlay:
    def __init__(self, target_window=None):
        self.target_window = target_window
        self.running = True
        self.root = None
        
    def run(self):
        if not TKINTER_AVAILABLE:
            return
            
        self.root = tk.Tk()
        self.root.title("Coordinate Display")
        self.root.attributes('-alpha', 0.8)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        self.root.geometry("250x100+10+10")
        
        self.root.configure(bg='black')
        
        self.coord_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 14),
            fg="white",
            bg="black",
            justify=tk.LEFT
        )
        self.coord_label.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.update_coordinates()
        self.root.mainloop()
    
    def update_coordinates(self):
        if not self.running:
            return
            
        x, y = pyautogui.position()
        
        text = f"Screen coordinates: ({x}, {y})"
        
        if self.target_window:
            bounds = self.target_window.get('kCGWindowBounds')
            if bounds:
                win_x = int(bounds.get('X', 0))
                win_y = int(bounds.get('Y', 0))
                rel_x = x - win_x
                rel_y = y - win_y
                text += f"\nWindow relative: ({rel_x}, {rel_y})"
        
        try:
            color = pyautogui.screenshot(region=(x, y, 1, 1)).getpixel((0, 0))
            text += f"\nColor: RGB{color}"
        except:
            pass
        
        self.coord_label.config(text=text)
        
        if self.root:
            self.root.after(50, self.update_coordinates)
    
    def stop(self):
        self.running = False
        if self.root:
            self.root.quit()

class ScreenshotAnalyzer:
    def __init__(self, image_path=None, window_name=None):
        self.image_path = image_path
        self.window_name = window_name
        self.image = None
        self.recorded_points = []
        
    def capture_screenshot(self):
        if self.window_name:
            windows = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID
            )
            
            for window in windows:
                if self.window_name.lower() in window.get('kCGWindowOwnerName', '').lower() or \
                   self.window_name.lower() in window.get('kCGWindowName', '').lower():
                    bounds = window.get('kCGWindowBounds')
                    x = int(bounds.get('X', 0))
                    y = int(bounds.get('Y', 0))
                    width = int(bounds.get('Width', 0))
                    height = int(bounds.get('Height', 0))
                    
                    screenshot = pyautogui.screenshot(region=(x, y, width, height))
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"screenshot_{self.window_name}_{timestamp}.png"
                    screenshot.save(filename)
                    print(f"Screenshot saved: {filename}")
                    return filename
        else:
            screenshot = pyautogui.screenshot()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_fullscreen_{timestamp}.png"
            screenshot.save(filename)
            print(f"Screenshot saved: {filename}")
            return filename
        
        return None
    
    def analyze_with_gui(self, image_path):
        if not TKINTER_AVAILABLE:
            print("GUI analysis feature cannot be used because tkinter is not available.")
            print("Please check coordinates manually or use a Python environment with tkinter installed.")
            return
            
        from tkinter import Canvas, Label
        
        root = tk.Tk()
        root.title("Screenshot Analysis")
        
        img = Image.open(image_path)
        
        scale = 1.0
        if img.width > 1200 or img.height > 800:
            scale = min(1200 / img.width, 800 / img.height)
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        canvas = Canvas(root, width=img.width, height=img.height)
        canvas.pack()
        canvas.create_image(0, 0, anchor='nw', image=photo)
        
        info_label = Label(root, text="", font=("Arial", 12))
        info_label.pack()
        
        def on_mouse_move(event):
            x = int(event.x / scale)
            y = int(event.y / scale)
            
            original_img = Image.open(image_path)
            if 0 <= x < original_img.width and 0 <= y < original_img.height:
                color = original_img.getpixel((x, y))
                info_label.config(text=f"Coordinates: ({x}, {y}) - Color: RGB{color}")
        
        def on_click(event):
            x = int(event.x / scale)
            y = int(event.y / scale)
            
            original_img = Image.open(image_path)
            if 0 <= x < original_img.width and 0 <= y < original_img.height:
                color = original_img.getpixel((x, y))
                point = {
                    "name": f"point_{len(self.recorded_points) + 1}",
                    "x": x,
                    "y": y,
                    "color": list(color),
                    "timestamp": datetime.now().isoformat()
                }
                self.recorded_points.append(point)
                print(f"記録: {point['name']} - 座標: ({x}, {y}) - 色: RGB{color}")
                
                root.clipboard_clear()
                root.clipboard_append(f"{x}, {y}")
                print("Coordinates copied to clipboard")
        
        canvas.bind('<Motion>', on_mouse_move)
        canvas.bind('<Button-1>', on_click)
        
        print("\n操作方法:")
        print("  - Mouse over: Display coordinates and color")
        print("  - Click: Record coordinates and copy to clipboard")
        print("  - Close window: End analysis")
        
        root.mainloop()
        
        if self.recorded_points:
            filename = f"analyzed_coordinates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "recorded_points": self.recorded_points,
                    "source_image": image_path,
                    "analyzed_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            print(f"\nRecorded coordinates saved to {filename}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Coordinate confirmation helper tool")
    parser.add_argument('mode', choices=['record', 'capture', 'analyze'],
                        help='Execution mode')
    parser.add_argument('--window', '-w', help='Target window name')
    parser.add_argument('--fullscreen', '-f', action='store_true',
                        help='Full screen mode')
    parser.add_argument('--image', '-i', help='Image file to analyze')
    parser.add_argument('--output', '-o', help='Output file name')
    
    args = parser.parse_args()
    
    if args.mode == 'record':
        recorder = CoordinateRecorder(
            window_name=args.window,
            fullscreen=args.fullscreen
        )
        recorder.run_interactive_mode()
    
    elif args.mode == 'capture':
        analyzer = ScreenshotAnalyzer(window_name=args.window)
        filename = analyzer.capture_screenshot()
        if filename and not args.image:
            print(f"\nAnalyze screenshot? (y/n): ", end='')
            if input().lower() == 'y':
                analyzer.analyze_with_gui(filename)
    
    elif args.mode == 'analyze':
        if not args.image:
            print("Error: Please specify an image file with the --image option")
            sys.exit(1)
        
        if not os.path.exists(args.image):
            print(f"Error: Image file '{args.image}' not found")
            sys.exit(1)
        
        analyzer = ScreenshotAnalyzer()
        analyzer.analyze_with_gui(args.image)