#!/bin/bash

echo "Pushing Homebrew formula updates..."

cd /Users/shimono/Documents/Work/private/homebrew-mactoro
git add Formula/mactoro.rb
git commit -m "Fix PyPI download URLs for PyAutoGUI and pynput"
git push origin main

echo "Done! Now re-tap the formula:"
echo "brew untap kory-/mactoro"
echo "brew tap kory-/mactoro"
echo "brew install kory-/mactoro/mactoro"