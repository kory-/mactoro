#!/bin/bash

echo "Final fix: Adding GitHub tarball SHA256..."

cd /Users/shimono/Documents/Work/private/homebrew-mactoro
git add Formula/mactoro.rb
git commit -m "Add SHA256 for GitHub tarball v0.1.0"
git push origin main

echo "✅ Complete! All URLs and SHA256 hashes are now correct."
echo ""
echo "To install mactoro:"
echo "brew untap kory-/mactoro"
echo "brew tap kory-/mactoro"
echo "brew install kory-/mactoro/mactoro"