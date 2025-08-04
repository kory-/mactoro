#!/bin/bash

echo "Updating to v0.1.1..."

# Update homebrew formula
cd /Users/shimono/Documents/Work/private/homebrew-mactoro
git add Formula/mactoro.rb
git commit -m "Update to v0.1.1"
git push origin main

echo "✅ Updated to v0.1.1!"
echo ""
echo "To install:"
echo "brew untap kory-/mactoro"
echo "brew tap kory-/mactoro"
echo "brew install mactoro"