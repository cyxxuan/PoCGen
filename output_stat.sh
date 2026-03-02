#!/bin/bash

OUTPUT_DIR="output"

for dir in "$OUTPUT_DIR"/*; do
  if [ -d "$dir" ] && [ -f "$dir/test.js" ]; then
    basename "$dir"
  fi
done
