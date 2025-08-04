# Mactoro CLI Usage Guide

## Overview

Mactoro uses a simple two-command structure:
- **`record`** - Record various types of automation data
- **`run`** - Execute automation from recorded data

## Recording Commands

### List Available Windows
```bash
# Show all windows that can be automated
mactoro record window-list

# Short alias
mactoro list
```

### Record User Actions
```bash
# Record actions for a specific window
mactoro record actions --window "Safari"

# Record using window ID
mactoro record actions --window-id 12345

# Record with custom output file
mactoro record actions --window "My App" --output my_recording.json

# Record without merging similar actions
mactoro record actions --window "Game" --no-merge

# Also record mouse movements
mactoro record actions --window "Drawing App" --record-mouse-move
```

### Record Coordinates
```bash
# Record coordinate points by clicking
mactoro record coordinates --window "My App"

# Record in fullscreen mode
mactoro record coordinates --fullscreen

# Save to specific file
mactoro record coordinates --window "Game" --output game_coords.json
```

### Capture Screenshots
```bash
# Capture screenshot of specific window
mactoro record screenshot --window "My App"

# Capture and analyze immediately
mactoro record screenshot --window "Game" --analyze

# Capture with custom filename
mactoro record screenshot --window "App" --output app_screenshot.png
```

### Analyze Existing Images
```bash
# Open GUI to analyze image for coordinates
mactoro record analyze-image --image screenshot.png
```

## Running Automation

### Basic Execution
```bash
# Run recorded actions
mactoro run --config recording.json --window "My App"

# Run using window ID
mactoro run --config actions.json --window-id 12345

# Run with coordinate definitions
mactoro run --config automation.json --window "Game" --coordinates coords.json

# Debug mode (shows detailed execution info)
mactoro run --config recording.json --window "App" --debug

# Dry run (preview without executing)
mactoro run --config recording.json --window "App" --dry-run
```

## Utility Commands

### Generate Configuration Templates
```bash
# Generate basic click sequence from coordinates
mactoro generate --coordinates coords.json

# Generate loop template
mactoro generate --coordinates coords.json --template loop

# Generate conditional template
mactoro generate --coordinates coords.json --template conditional

# Custom output file
mactoro generate --coordinates coords.json --output my_config.json
```

## Typical Workflow

### 1. Find Your Target Window
```bash
mactoro record window-list
```

### 2. Record Actions or Coordinates
```bash
# Option A: Record your interactions
mactoro record actions --window "My App"

# Option B: Record specific coordinate points
mactoro record coordinates --window "My App"
```

### 3. Run the Automation
```bash
# Run recorded actions
mactoro run --config recording_20240118_143022.json --window "My App"

# Or generate and customize a config file first
mactoro generate --coordinates coordinates_20240118_143022.json
# Edit generated_config.json as needed
mactoro run --config generated_config.json --window "My App" --coordinates coordinates_20240118_143022.json
```

## Tips

1. **Window Names**: Use exact window titles as shown in `record window-list`
2. **Window IDs**: More reliable than names if window titles change
3. **Coordinates**: Use `record coordinates` for precise positioning
4. **Debug Mode**: Add `--debug` to see detailed execution information
5. **Dry Run**: Use `--dry-run` to preview what will be executed

## Examples

### Automate a Game
```bash
# 1. List windows to find game
mactoro list

# 2. Record coordinate points for buttons
mactoro record coordinates --window "My Game"

# 3. Generate a loop configuration
mactoro generate --coordinates coordinates.json --template loop

# 4. Edit the config file to add your logic

# 5. Run the automation
mactoro run --config game_automation.json --window "My Game" --coordinates coordinates.json
```

### Record and Replay User Actions
```bash
# 1. Start recording
mactoro record actions --window "Text Editor"

# 2. Perform your actions (clicks, typing, etc.)
# 3. Press ESC to stop recording

# 4. Replay the recording
mactoro run --config recording.json --window "Text Editor"
```