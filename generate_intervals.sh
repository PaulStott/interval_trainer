#!/bin/bash

# List of interval names
intervals=(
  "Minor Second"
  "Major Second"
  "Minor Third"
  "Major Third"
  "Perfect Fourth"
  "Tritone"
  "Perfect Fifth"
  "Minor Sixth"
  "Major Sixth"
  "Minor Seventh"
  "Major Seventh"
  "Octave"
)

# Output directory (optional)
output_dir="./sounds"
mkdir -p "$output_dir"

# Generate each interval as .wav
for interval in "${intervals[@]}"; do
  filename=$(echo "$interval" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
  aiff_path="$output_dir/${filename}.aiff"
  wav_path="$output_dir/${filename}.wav"

  say "$interval" -o "$aiff_path"
  afconvert "$aiff_path" "$wav_path" -f WAVE -d LEI16@44100
  rm "$aiff_path"  # Optional: clean up intermediate .aiff
done
