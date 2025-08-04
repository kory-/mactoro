#!/bin/bash

echo "Updating homebrew-mactoro formula..."

HOMEBREW_DIR="/Users/shimono/Documents/Work/private/homebrew-mactoro"

cd "$HOMEBREW_DIR"

git add Formula/mactoro.rb
git commit -m "Fix PyAutoGUI download URL and SHA256"
git push origin main

echo "Formula updated successfully!"