#!/usr/bin/env python3
import click
import sys
from .window_controller import WindowController
from .action_recorder import ActionRecorder  
import json
import os
from datetime import datetime

@click.group()
@click.version_option(version='0.1.0', prog_name='Mactoro')
def main():
    """Mactoro - macOS Automation Tool
    
    A powerful automation tool for macOS that enables window control,
    mouse/keyboard automation, and action recording.
    
    Main commands:
      record - Record various types of automation data
      run    - Execute automation from recorded data
    """
    pass

@main.group()
def record():
    """Record automation data (actions, coordinates, screenshots)"""
    pass

@record.command(name='window-list')
def record_window_list():
    """List all available windows"""
    controller = WindowController()
    windows = controller.list_windows()
    
    print(f"\nCurrently open windows: {len(windows)}\n")
    print(f"{'ID':<8} {'PID':<8} {'Application':<20} {'Window Title':<30} {'Position and Size'}")
    print("-" * 100)
    
    for window in windows:
        window_id = window['window_id']
        pid = window['pid']
        owner = window['owner_name'][:20]
        title = window['window_name'][:30] if window['window_name'] else '(No title)'
        
        bounds = window['bounds']
        if bounds:
            position = f"({bounds['x']}, {bounds['y']}) {bounds['width']}x{bounds['height']}"
        else:
            position = "N/A"
        
        print(f"{window_id:<8} {pid:<8} {owner:<20} {title:<30} {position}")

@record.command(name='actions')
@click.option('--window', '-w', help='Target window name')
@click.option('--window-id', '-i', type=int, help='Target window ID (use "record window-list" to find)')
@click.option('--output', '-o', help='Output file name (default: recording_TIMESTAMP.json)')
@click.option('--no-merge', is_flag=True, help='Don\'t merge consecutive similar actions')
@click.option('--record-mouse-move', is_flag=True, help='Also record mouse movements')
def record_actions(window, window_id, output, no_merge, record_mouse_move):
    """Record user actions (mouse clicks, keyboard input, etc.)"""
    if not output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = f"recording_{timestamp}.json"
    
    recorder = ActionRecorder(window_name=window, window_id=window_id)
    recorder.merge_similar_actions = not no_merge
    recorder.record_mouse_move = record_mouse_move
    
    try:
        recorder.start_recording()
    except KeyboardInterrupt:
        pass
    finally:
        recorder.stop_recording()
        
        if recorder.actions:
            recorder.save_to_json(output)
            print(f"\nTo run this recording, use:")
            print(f"  mactoro run --config {output}", end='')
            if window:
                print(f" --window \"{window}\"")
            elif window_id:
                print(f" --window-id {window_id}")
            else:
                print()
        else:
            print("\nNo actions recorded")

@record.command(name='coordinates')
@click.option('--window', '-w', help='Target window name')
@click.option('--fullscreen', '-f', is_flag=True, help='Fullscreen mode')
@click.option('--output', '-o', help='Output file name (default: coordinates_TIMESTAMP.json)')
def record_coordinates(window, fullscreen, output):
    """Record coordinates interactively (click to mark positions)"""
    from .coordinate_helper import CoordinateRecorder
    recorder = CoordinateRecorder(
        window_name=window,
        fullscreen=fullscreen
    )
    recorder.run_interactive_mode()

@record.command(name='screenshot')
@click.option('--window', '-w', help='Target window name')
@click.option('--analyze', '-a', is_flag=True, help='Open GUI to analyze coordinates after capture')
@click.option('--output', '-o', help='Output file name (default: screenshot_TIMESTAMP.png)')
def record_screenshot(window, analyze, output):
    """Capture screenshot for coordinate analysis"""
    from .coordinate_helper import ScreenshotAnalyzer
    analyzer = ScreenshotAnalyzer(window_name=window)
    filename = analyzer.capture_screenshot()
    
    if filename and analyze:
        analyzer.analyze_with_gui(filename)

@record.command(name='analyze-image')
@click.option('--image', '-i', required=True, help='Image file to analyze')
def record_analyze_image(image):
    """Analyze existing image for coordinates"""
    if not os.path.exists(image):
        print(f"Error: Image file '{image}' not found")
        sys.exit(1)
    
    from .coordinate_helper import ScreenshotAnalyzer
    analyzer = ScreenshotAnalyzer()
    analyzer.analyze_with_gui(image)

@main.command()
@click.option('--config', '-c', required=True, help='Configuration file path')
@click.option('--window', '-w', help='Target window name')
@click.option('--window-id', '-i', type=int, help='Target window ID')
@click.option('--coordinates', help='Coordinates definition file path (optional)')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--dry-run', is_flag=True, help='Show what would be executed without running')
def run(config, window, window_id, coordinates, debug, dry_run):
    """Execute automation from configuration file
    
    Examples:
      mactoro run --config recording.json --window "My App"
      mactoro run --config actions.json --window-id 12345
      mactoro run --config automation.json --window "Game" --coordinates coords.json
    """
    if not window and not window_id:
        print("Error: Please specify --window or --window-id")
        print("\nTip: Use 'mactoro record window-list' to see available windows")
        sys.exit(1)
    
    if dry_run:
        print(f"Dry run mode - would execute: {config}")
        with open(config, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        print(f"Total actions: {len(config_data.get('actions', []))}")
        return
    
    controller = WindowController()
    controller.run_automation(
        window_name=window,
        window_id=window_id,
        config_path=config,
        coordinates_path=coordinates,
        debug=debug
    )

@main.command()
@click.option('--coordinates', '-c', required=True, help='Coordinates definition file')
@click.option('--output', '-o', default='generated_config.json', help='Output file name')
@click.option('--template', '-t', type=click.Choice(['basic', 'loop', 'conditional']), 
              default='basic', help='Template type to generate')
def generate(coordinates, output, template):
    """Generate configuration template from recorded coordinates
    
    This command helps you create a configuration file from recorded coordinates.
    """
    with open(coordinates, 'r', encoding='utf-8') as f:
        coord_data = json.load(f)
    
    config = {
        "settings": {
            "default_wait": 0.5,
            "screenshot_on_error": True,
            "max_runtime": 3600
        },
        "actions": []
    }
    
    if template == 'basic':
        # Basic click sequence
        for point in coord_data.get('recorded_points', []):
            config['actions'].append({
                "type": "click",
                "coordinate": point['name'],
                "wait": 1,
                "comment": f"Coordinates: ({point['x']}, {point['y']}) - Color: RGB{point['color']}"
            })
    elif template == 'loop':
        # Loop template
        config['actions'].append({
            "type": "loop",
            "max_iterations": 10,
            "actions": [
                {
                    "type": "click",
                    "coordinate": coord_data['recorded_points'][0]['name'] if coord_data.get('recorded_points') else "point_1",
                    "wait": 1
                }
            ]
        })
    elif template == 'conditional':
        # Conditional template
        if coord_data.get('recorded_points'):
            point = coord_data['recorded_points'][0]
            config['actions'].append({
                "type": "wait_for_color",
                "coordinate": point['name'],
                "color": point.get('color', [0, 0, 0]),
                "tolerance": 10,
                "timeout": 5
            })
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"Configuration file generated: {output}")
    print(f"Template type: {template}")
    print(f"\nTo run this configuration, use:")
    print(f"  mactoro run --config {output} --window \"Your Window\" --coordinates {coordinates}")

# Quick command aliases for common operations
@main.command()
@click.pass_context
def list(ctx):
    """Alias for 'record window-list'"""
    ctx.invoke(record_window_list)

if __name__ == '__main__':
    main()