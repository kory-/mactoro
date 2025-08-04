#!/bin/bash

echo "Fixing SHA256 hashes for all packages..."

cd /Users/shimono/Documents/Work/private/homebrew-mactoro
git add Formula/mactoro.rb
git commit -m "Fix SHA256 hashes for pyobjc packages

- Fix pyobjc-core SHA256
- Fix pyobjc-framework-Cocoa SHA256
- All hashes now match actual downloaded files"

git push origin main

echo "✅ SHA256 hashes fixed and pushed!"
echo ""
echo "Now run:"
echo "brew untap kory-/mactoro"
echo "brew tap kory-/mactoro"
echo "brew install kory-/mactoro/mactoro"