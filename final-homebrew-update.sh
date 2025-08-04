#!/bin/bash

echo "Final update for Homebrew formula with all correct PyPI URLs..."

cd /Users/shimono/Documents/Work/private/homebrew-mactoro
git add Formula/mactoro.rb
git commit -m "Update all PyPI package URLs and versions

- Update pyobjc-core from 10.1 to 11.1
- Update pyobjc-framework-Cocoa from 10.1 to 11.1  
- Update pyobjc-framework-Quartz from 10.1 to 11.1
- Update opencv-python from 4.9.0.80 to 4.12.0.88
- Fix PyAutoGUI and pynput URLs
- All URLs and SHA256 hashes verified from PyPI"

git push origin main

echo "✅ Done! Formula has been updated with all correct URLs."
echo ""
echo "To install mactoro:"
echo "1. brew untap kory-/mactoro"
echo "2. brew tap kory-/mactoro"
echo "3. brew install kory-/mactoro/mactoro"