#!/usr/bin/env python3
"""
Generate labels.csv file by mapping datapoint indices to image IDs.
This creates the mapping needed for the demo to find the correct images.
"""

import os
import pandas as pd
from pathlib import Path
import re

def extract_image_ids():
    """Extract all image IDs from the chip directory."""
    files_dir = Path('Files')
    chip_dir = files_dir / 'chip'
    
    if not chip_dir.exists():
        print(f"ERROR: Chip directory not found at {chip_dir}")
        return []
    
    # Get all .jpg files from chip directory
    chip_files = sorted(chip_dir.glob('*.jpg'))
    
    # Extract image IDs (filename without extension)
    image_ids = [f.stem for f in chip_files]
    
    print(f"Found {len(image_ids)} image IDs")
    if image_ids:
        print(f"First few: {image_ids[:5]}")
        print(f"Last few: {image_ids[-5:]}")
    
    return image_ids

def verify_images_exist(image_ids):
    """Verify that all three image types exist for each ID."""
    files_dir = Path('Files')
    work_dir = files_dir / 'work'
    tool_dir = files_dir / 'tool'
    chip_dir = files_dir / 'chip'
    
    complete = []
    incomplete = []
    
    for image_id in image_ids:
        work_exists = (work_dir / f"{image_id}.png").exists()
        tool_exists = (tool_dir / f"{image_id}.jpg").exists()
        chip_exists = (chip_dir / f"{image_id}.jpg").exists()
        
        if work_exists and tool_exists and chip_exists:
            complete.append(image_id)
        else:
            incomplete.append({
                'id': image_id,
                'work': work_exists,
                'tool': tool_exists,
                'chip': chip_exists
            })
    
    print(f"\nVerification:")
    print(f"  Complete sets: {len(complete)}")
    print(f"  Incomplete sets: {len(incomplete)}")
    
    if incomplete and len(incomplete) <= 10:
        print(f"\nIncomplete image sets:")
        for item in incomplete:
            missing = []
            if not item['work']: missing.append('work')
            if not item['tool']: missing.append('tool')
            if not item['chip']: missing.append('chip')
            print(f"  {item['id']}: missing {', '.join(missing)}")
    
    return complete

def generate_labels_csv():
    """Generate labels.csv file."""
    print("=" * 60)
    print("GENERATING LABELS.CSV")
    print("=" * 60)
    print()
    
    # Extract image IDs
    image_ids = extract_image_ids()
    
    if not image_ids:
        print("ERROR: No images found!")
        return False
    
    # Verify all images exist
    complete_ids = verify_images_exist(image_ids)
    
    if not complete_ids:
        print("\nERROR: No complete image sets found!")
        return False
    
    # Create DataFrame
    # Map datapoint index (0-511) to image ID
    df = pd.DataFrame({
        'datapoint_index': range(len(complete_ids)),
        'id': complete_ids
    })
    
    # Save to CSV
    output_path = Path('Files') / 'labels.csv'
    df.to_csv(output_path, index=False)
    
    print(f"\n{'=' * 60}")
    print(f"SUCCESS")
    print(f"{'=' * 60}")
    print(f"Created {output_path}")
    print(f"Mapped {len(df)} datapoints to image IDs")
    print()
    print("Sample mappings:")
    print(df.head(10).to_string(index=False))
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = generate_labels_csv()
        if success:
            print("\n✓ labels.csv generated successfully!")
            print("\nYou can now run the demo with full image support.")
        else:
            print("\n✗ Failed to generate labels.csv")
            print("\nPlease check your Files directory structure.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
