#!/bin/bash

# List of interval names
feedbacks=(
  "Correct"
  "Incorrect"
)

# Output directory (optional)
output_dir="./sounds"
mkdir -p "$output_dir"

# Generate each interval as .wav
for feedback in "${feedbacks[@]}"; do
  filename=$(echo "$feedback" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
  aiff_path="$output_dir/${filename}.aiff"
  wav_path="$output_dir/${filename}.wav"

  say "$feedback" -o "$aiff_path"
  afconvert "$aiff_path" "$wav_path" -f WAVE -d LEI16@44100
  rm "$aiff_path"  # Optional: clean up intermediate .aiff
done
