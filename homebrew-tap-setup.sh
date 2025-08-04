#!/bin/bash

# Homebrew tap setup script for mactoro

echo "Setting up homebrew-mactoro tap..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

# Initialize git repository
git init
git branch -M main

# Copy the formula
cp /Users/shimono/Documents/Work/private/mactoro/mactoro.rb Formula/mactoro.rb

# Create README
cat > README.md << 'EOF'
# Homebrew Mactoro

Homebrew tap for [mactoro](https://github.com/kory-/mactoro).

## Installation

```bash
brew tap kory-/mactoro
brew install mactoro
```

## Formula

- `mactoro` - macOS automation tool for window control and action recording
EOF

# Create directory structure
mkdir -p Formula

# Copy formula to Formula directory
cp /Users/shimono/Documents/Work/private/mactoro/mactoro.rb Formula/mactoro.rb

# Add and commit
git add .
git commit -m "Initial commit: Add mactoro formula"

# Add remote (you'll need to create the repository on GitHub first)
git remote add origin https://github.com/kory-/homebrew-mactoro.git

echo "Setup complete!"
echo "Next steps:"
echo "1. Create 'homebrew-mactoro' repository on GitHub"
echo "2. Run: cd $TEMP_DIR"
echo "3. Run: git push -u origin main"