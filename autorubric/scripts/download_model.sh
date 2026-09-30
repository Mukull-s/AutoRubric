#!/bin/bash
set -e

echo "Downloading models..."
mkdir -p models
# Call P4's script when it's available, for now just touch a dummy file
touch models/dummy.bin
echo "Done."
