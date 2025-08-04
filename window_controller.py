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
from coordinate_helper import CoordinateRecorder, ScreenshotAnalyzer

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

class WindowController:
    def __init__(self):
        self.running = True
        self.recorded_coordinates = {}
        self.current_window = None
        self.debug = False
        self.screenshot_on_error = True
        self.action_history = []
        self.keyboard_listener = None
        
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n\n中断されました")
        self.running = False
        sys.exit(0)
    
    def _on_key_press(self, key):
        """キーボードイベントハンドラー"""
        try:
            if key == keyboard.Key.esc:
                print("\n\nESCキーが押されました - 処理を中断します")
                self.running = False
                return False  # リスナーを停止
        except AttributeError:
            pass
    
    def list_windows(self) -> List[Dict[str, Any]]:
        """現在開いているウィンドウの一覧を取得"""
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
        """指定された名前またはIDのウィンドウを検索"""
        windows = self.list_windows()
        
        # IDで検索
        if window_id:
            for window in windows:
                if window['window_id'] == window_id:
                    return window
        
        # 名前で検索（完全一致を優先）
        if window_name:
            # まず完全一致を試す
            for window in windows:
                if window_name.lower() == window['owner_name'].lower() or \
                   window_name.lower() == window['window_name'].lower():
                    return window
            
            # 部分一致を試す
            for window in windows:
                if window_name.lower() in window['owner_name'].lower() or \
                   window_name.lower() in window['window_name'].lower():
                    return window
        
        return None
    
    def focus_window(self, window: Dict[str, Any]) -> bool:
        """指定されたウィンドウにフォーカスを移動"""
        try:
            pid = window['pid']
            
            app = AppKit.NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
            if app:
                app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)
                # JSONのdefault_waitを使用するため、ここでは待機しない
                return True
        except Exception as e:
            if self.debug:
                print(f"ウィンドウフォーカスエラー: {e}")
        return False
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """JSON設定ファイルを読み込み"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_coordinates(self, coord_path: str) -> Dict[str, Dict[str, Any]]:
        """座標定義ファイルを読み込み"""
        with open(coord_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            coordinates = {}
            for point in data.get('recorded_points', []):
                coordinates[point['name']] = point
            return coordinates
    
    def resolve_coordinates(self, action: Dict[str, Any]) -> Tuple[int, int]:
        """アクションから座標を解決"""
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
                raise ValueError(f"座標 '{coord_name}' が見つかりません")
        
        x = action.get('x', 0)
        y = action.get('y', 0)
        
        if action.get('relative_to') == 'window' and self.current_window:
            bounds = self.current_window['bounds']
            x += bounds['x']
            y += bounds['y']
        
        return x, y
    
    def wait_for_condition(self, condition: Dict[str, Any], timeout: float = 10) -> bool:
        """条件が満たされるまで待機"""
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
            
            time.sleep(0.01)  # より短いポーリング間隔
        
        return False
    
    def execute_action(self, action: Dict[str, Any]) -> Any:
        """単一のアクションを実行"""
        if not self.running:
            return None
        
        action_type = action['type']
        
        # タイムスタンプを取得
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if self.debug:
            print(f"実行: {action_type} - {action}")
        
        result = None
        
        try:
            if action_type == 'click':
                x, y = self.resolve_coordinates(action)
                pyautogui.click(x, y)
                # アクション情報を構築
                action_info = f"クリック: ({x}, {y})"
                if 'comment' in action:
                    action_info += f" - {action['comment']}"
            
            elif action_type == 'double_click':
                x, y = self.resolve_coordinates(action)
                pyautogui.doubleClick(x, y)
                # アクション情報を構築
                action_info = f"ダブルクリック: ({x}, {y})"
                if 'comment' in action:
                    action_info += f" - {action['comment']}"
            
            elif action_type == 'right_click':
                x, y = self.resolve_coordinates(action)
                pyautogui.rightClick(x, y)
                # アクション情報を構築
                action_info = f"右クリック: ({x}, {y})"
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
                start_x, start_y = self.resolve_coordinates(action)
                end_x = action.get('end_x', start_x + 100)
                end_y = action.get('end_y', start_y)
                duration = action.get('duration', 1.0)
                pyautogui.dragTo(end_x, end_y, duration=duration)
            
            elif action_type == 'scroll':
                clicks = action.get('clicks', 1)
                x, y = self.resolve_coordinates(action) if 'x' in action else pyautogui.position()
                pyautogui.scroll(clicks, x=x, y=y)
            
            elif action_type == 'wait':
                seconds = action.get('seconds', 1)
                action_info = f"{seconds}秒待機"
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
                print(f"スクリーンショット保存: {filename}")
            
            elif action_type == 'log':
                message = action.get('message', '')
                print(f"[LOG] {message}")
            
            elif action_type == 'loop':
                max_iterations = action.get('max_iterations', 10)
                actions = action.get('actions', [])
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ループ開始 (最大 {max_iterations} 回)")
                
                for i in range(max_iterations):
                    if not self.running:
                        break
                    if i % 10 == 0 or self.debug:  # 10回ごとまたはデバッグモードで進捗表示
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] ループ {i + 1}/{max_iterations}")
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
                    print(f"色 {color} が見つかりませんでした")
            
            # wait情報を追加
            wait_info = ""
            wait_time = action.get('wait', None)
            if wait_time is not None:
                if wait_time > 0:
                    wait_info = f" (wait: {wait_time}秒)"
                    time.sleep(wait_time)
                else:
                    wait_info = " (wait: 0秒)"
            elif hasattr(self, '_default_wait') and self._default_wait > 0:
                wait_info = f" (default_wait: {self._default_wait}秒)"
            
            # 最終的な出力（アクションがある場合のみ）
            if 'action_info' in locals():
                print(f"[{timestamp}] {action_info}{wait_info}")
            elif 'comment' in action and action_type not in ['click', 'double_click', 'right_click']:
                # クリック以外のアクションでコメントがある場合
                print(f"[{timestamp}] {action['comment']}{wait_info}")
            
            self.action_history.append({
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'result': result
            })
            
        except Exception as e:
            print(f"アクションエラー: {action_type} - {e}")
            if self.screenshot_on_error:
                error_screenshot = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                pyautogui.screenshot().save(error_screenshot)
                print(f"エラースクリーンショット: {error_screenshot}")
            raise
        
        return result
    
    def run_automation(self, window_name: str = None, window_id: int = None, 
                      config_path: str = None, coordinates_path: str = None,
                      debug: bool = False):
        """自動化を実行"""
        self.debug = debug
        
        # ESCキー監視リスナーを開始
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()
        print("ESCキーで中断できます")
        
        if window_name or window_id:
            self.current_window = self.find_window(window_name, window_id)
            if not self.current_window:
                print(f"ウィンドウが見つかりません")
                self.keyboard_listener.stop()
                sys.exit(1)
            
            print(f"対象ウィンドウ: {self.current_window['owner_name']} - {self.current_window['window_name']}")
            bounds = self.current_window.get('bounds')
            if bounds:
                print(f"ウィンドウ位置: ({bounds['x']}, {bounds['y']}) サイズ: {bounds['width']}x{bounds['height']}")
            
            if not self.focus_window(self.current_window):
                print("ウィンドウにフォーカスできませんでした")
        
        if coordinates_path and os.path.exists(coordinates_path):
            self.recorded_coordinates = self.load_coordinates(coordinates_path)
            print(f"座標定義を読み込みました: {len(self.recorded_coordinates)} 個")
        
        config = self.load_config(config_path)
        
        settings = config.get('settings', {})
        self.screenshot_on_error = settings.get('screenshot_on_error', True)
        default_wait = settings.get('default_wait', 0)
        max_runtime = settings.get('max_runtime', 3600)
        
        # default_waitをインスタンス変数として保存
        self._default_wait = default_wait
        
        pyautogui.PAUSE = default_wait
        
        actions = config.get('actions', [])
        
        print(f"\ndefault_wait: {default_wait}秒")
        print(f"{len(actions)} 個のアクションを実行します...")
        
        start_time = time.time()
        
        try:
            for i, action in enumerate(actions):
                if not self.running:
                    break
                
                if time.time() - start_time > max_runtime:
                    print(f"\n最大実行時間 ({max_runtime}秒) を超えました")
                    break
                
                if self.debug:
                    print(f"\nアクション {i + 1}/{len(actions)}")
                
                self.execute_action(action)
            
            if self.running:
                print(f"\n完了: {len(self.action_history)} 個のアクションを実行しました")
            else:
                print(f"\n中断されました: {len(self.action_history)} 個のアクションを実行しました")
            
        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            sys.exit(1)
        finally:
            # リスナーを停止
            if self.keyboard_listener and self.keyboard_listener.is_alive():
                self.keyboard_listener.stop()

@click.group()
def cli():
    """macOS ウィンドウ操作自動化ツール"""
    pass

@cli.command()
def list():
    """現在開いているウィンドウの一覧を表示"""
    controller = WindowController()
    windows = controller.list_windows()
    
    print(f"\n現在開いているウィンドウ: {len(windows)} 個\n")
    print(f"{'ID':<8} {'PID':<8} {'アプリケーション':<20} {'ウィンドウタイトル':<30} {'位置とサイズ'}")
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

@cli.command()
@click.option('--window', '-w', help='対象ウィンドウ名')
@click.option('--fullscreen', '-f', is_flag=True, help='全画面モード')
@click.option('--output', '-o', help='出力ファイル名')
def record(window, fullscreen, output):
    """座標記録モード"""
    recorder = CoordinateRecorder(
        window_name=window,
        fullscreen=fullscreen
    )
    recorder.run_interactive_mode()

@cli.command()
@click.option('--window', '-w', help='対象ウィンドウ名')
@click.option('--window-id', '-i', type=int, help='対象ウィンドウID')
@click.option('--config', '-c', required=True, help='設定ファイルパス')
@click.option('--coordinates', help='座標定義ファイルパス')
@click.option('--debug', '-d', is_flag=True, help='デバッグモード')
def run(window, window_id, config, coordinates, debug):
    """設定ファイルに基づいて自動化を実行"""
    if not window and not window_id:
        print("エラー: --window または --window-id を指定してください")
        sys.exit(1)
    
    controller = WindowController()
    controller.run_automation(
        window_name=window,
        window_id=window_id,
        config_path=config,
        coordinates_path=coordinates,
        debug=debug
    )

@cli.command()
@click.option('--window', '-w', help='対象ウィンドウ名')
@click.option('--analyze', '-a', is_flag=True, help='撮影後に分析')
def capture(window, analyze):
    """スクリーンショットを撮影"""
    analyzer = ScreenshotAnalyzer(window_name=window)
    filename = analyzer.capture_screenshot()
    
    if filename and analyze:
        analyzer.analyze_with_gui(filename)

@cli.command()
@click.option('--image', '-i', required=True, help='分析する画像ファイル')
def analyze(image):
    """スクリーンショットを分析"""
    if not os.path.exists(image):
        print(f"エラー: 画像ファイル '{image}' が見つかりません")
        sys.exit(1)
    
    analyzer = ScreenshotAnalyzer()
    analyzer.analyze_with_gui(image)

@cli.command()
@click.option('--coordinates', '-c', required=True, help='座標定義ファイル')
@click.option('--output', '-o', default='generated_config.json', help='出力ファイル名')
def generate_config(coordinates, output):
    """座標定義から設定ファイルのテンプレートを生成"""
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
            "comment": f"座標: ({point['x']}, {point['y']}) - 色: RGB{point['color']}"
        })
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"設定ファイルを生成しました: {output}")

if __name__ == '__main__':
    cli()