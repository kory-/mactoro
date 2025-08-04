#!/bin/bash

echo "Setting up homebrew-mactoro repository..."

HOMEBREW_DIR="/Users/shimono/Documents/Work/private/homebrew-mactoro"

cd "$HOMEBREW_DIR"

# Check if already a git repo
if [ -d ".git" ]; then
    echo "Git repository already initialized"
    git add .
    git commit -m "Add mactoro formula and documentation" || echo "Nothing to commit"
else
    echo "Initializing git repository..."
    git init
    git branch -M main
    git add .
    git commit -m "Initial commit: Add mactoro formula"
fi

# Add remote if not exists
if ! git remote | grep -q origin; then
    git remote add origin https://github.com/kory-/homebrew-mactoro.git
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure you've created the 'homebrew-mactoro' repository on GitHub"
echo "2. Run: cd $HOMEBREW_DIR"
echo "3. Run: git push -u origin main"
echo ""
echo "After pushing, you can use:"
echo "  brew tap kory-/mactoro"
echo "  brew install mactoro"