# Mactoro

[![PyPI version](https://badge.fury.io/py/mactoro.svg)](https://badge.fury.io/py/mactoro)
[![Python Support](https://img.shields.io/pypi/pyversions/mactoro.svg)](https://pypi.org/project/mactoro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/kory-/mactoro/actions/workflows/ci.yml/badge.svg)](https://github.com/kory-/mactoro/actions/workflows/ci.yml)

A powerful Python-based automation tool for macOS that enables window control, mouse/keyboard automation, and action recording.

## Features

- **Window Management**: Find, focus, and control specific application windows
- **Action Recording**: Record mouse clicks, keyboard input, and other user interactions
- **Coordinate Helper**: Interactive coordinate recording with color detection
- **JSON Configuration**: Define complex automation workflows using JSON files
- **Relative Positioning**: Support for both absolute and window-relative coordinates
- **Conditional Logic**: Wait for colors, windows, or time-based conditions
- **Loop Support**: Execute repetitive tasks with various loop types
- **Screenshot Capabilities**: Capture screens for analysis or error debugging

## Requirements

- macOS (uses native Quartz and AppKit frameworks)
- Python 3.6 or higher
- Required Python packages (see requirements.txt)

## Installation

### Option 1: Install via pip (Recommended)
```bash
pip install mactoro
```

### Option 2: Install via Homebrew
```bash
brew tap kory-/mactoro
brew install mactoro
```

### Option 3: Install from source
```bash
git clone https://github.com/kory-/mactoro.git
cd mactoro
pip install -e .
```

4. Grant accessibility permissions:
   - Go to System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Terminal (or your Python interpreter) to the allowed applications

## Usage

### Basic Commands

Mactoro uses a hierarchical command structure:
```
mactoro <command> <subcommand> [options]
```

### Window Management

#### List Available Windows
```bash
mactoro window list
```

### Action Recording and Automation

#### Record User Actions
```bash
mactoro action record --window "TextEdit" --output recording.json
```

Options:
- `--window-id, -i`: Use window ID instead of name
- `--no-merge`: Don't merge consecutive similar actions
- `--record-mouse-move`: Also record mouse movements

#### Run Automation
```bash
mactoro action run --window "Chrome" --config my_automation.json
```

Options:
- `--window, -w`: Target window name
- `--window-id, -i`: Target window ID
- `--config, -c`: Configuration file path (required)
- `--coordinates`: Coordinates definition file
- `--debug, -d`: Enable debug mode

### Coordinate Management

#### Record Coordinates Interactively
```bash
mactoro coordinate record --window "Finder"
```

#### Capture Screenshot
```bash
mactoro coordinate capture --window "Safari" --analyze
```

#### Analyze Screenshot
```bash
mactoro coordinate analyze --image screenshot.png
```

### Configuration Generator

#### Generate Config from Coordinates
```bash
mactoro generate-config --coordinates coords.json --output config.json
```

## Configuration File Structure

### Basic Structure
```json
{
  "settings": {
    "default_wait": 0.5,
    "screenshot_on_error": true,
    "max_runtime": 3600
  },
  "actions": [
    {
      "type": "click",
      "x": 100,
      "y": 200,
      "wait": 1
    }
  ]
}
```

### Action Types

#### Click Actions
```json
{
  "type": "click",
  "x": 100,
  "y": 200,
  "relative_to": "window",
  "wait": 0.5
}
```

#### Type Text
```json
{
  "type": "type",
  "text": "Hello World",
  "interval": 0.05
}
```

#### Keyboard Shortcuts
```json
{
  "type": "hotkey",
  "keys": ["cmd", "c"]
}
```

#### Wait Actions
```json
{
  "type": "wait",
  "seconds": 2
}
```

#### Wait for Color
```json
{
  "type": "wait_for_color",
  "x": 150,
  "y": 250,
  "color": [0, 122, 255],
  "tolerance": 10,
  "timeout": 5
}
```

#### Loops
```json
{
  "type": "loop",
  "max_iterations": 10,
  "actions": [
    {
      "type": "click",
      "x": 100,
      "y": 100
    }
  ]
}
```

#### Conditional Loops
```json
{
  "type": "loop_until",
  "condition": {
    "type": "color_match",
    "x": 500,
    "y": 300,
    "color": [255, 0, 0],
    "tolerance": 10
  },
  "timeout": 60,
  "actions": [
    {
      "type": "click",
      "x": 400,
      "y": 400
    }
  ]
}
```

## Examples

### Example 1: Basic Web Form Automation
```json
{
  "settings": {
    "default_wait": 0.5
  },
  "actions": [
    {
      "type": "click",
      "x": 300,
      "y": 200,
      "relative_to": "window",
      "comment": "Click username field"
    },
    {
      "type": "type",
      "text": "john.doe@example.com"
    },
    {
      "type": "click",
      "x": 300,
      "y": 250,
      "relative_to": "window",
      "comment": "Click password field"
    },
    {
      "type": "type",
      "text": "password123"
    },
    {
      "type": "click",
      "x": 350,
      "y": 300,
      "relative_to": "window",
      "comment": "Click submit button"
    }
  ]
}
```

### Example 2: Recording Workflow
1. First, record the actions:
```bash
mactoro action record --window "MyApp" --output my_recording.json
```

2. The tool will create a JSON file with all recorded actions
3. Run the recorded automation:
```bash
mactoro action run --window "MyApp" --config my_recording.json
```

### Example 3: Coordinate-based Automation
1. Record specific coordinates:
```bash
mactoro coordinate record --window "Calculator"
```

2. Generate config template from coordinates:
```bash
mactoro generate-config --coordinates coordinates.json --output calc_automation.json
```

3. Edit the generated config and run:
```bash
mactoro action run --window "Calculator" --config calc_automation.json
```

## Command Structure

The new unified command structure:
```
mactoro window list                          # List all windows
mactoro action record [options]              # Record actions
mactoro action run [options]                 # Run automation
mactoro coordinate record [options]          # Record coordinates
mactoro coordinate capture [options]         # Capture screenshot  
mactoro coordinate analyze [options]         # Analyze image
mactoro generate-config [options]            # Generate config
```

## Tips and Best Practices

1. **Use Window-Relative Coordinates**: Always prefer `"relative_to": "window"` for better reliability across different screen positions

2. **Add Wait Times**: Use appropriate wait times between actions to ensure UI elements are ready

3. **Error Handling**: Enable `"screenshot_on_error": true` to capture the screen state when errors occur

4. **Test in Debug Mode**: Use `--debug` flag to see detailed execution information

5. **ESC to Stop**: Press ESC key anytime during execution to safely stop the automation

## Troubleshooting

### Common Issues

1. **"Window not found" error**
   - Ensure the window is open and visible
   - Try using partial window name matching
   - Use `list` command to see exact window names

2. **Permission denied errors**
   - Grant accessibility permissions in System Preferences
   - Run Terminal with appropriate permissions

3. **Coordinates not working**
   - Verify window position hasn't changed
   - Use window-relative coordinates instead of absolute
   - Re-record coordinates if necessary

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.