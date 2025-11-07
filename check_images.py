#!/usr/bin/env python3
"""
Script to check which datapoints have complete image sets.
Helps identify which samples can be used for demo with predictions.
"""

import os
import pandas as pd
from pathlib import Path

def check_image_availability():
    """Check which datapoints have all required images."""
    
    # Get project root
    script_dir = Path(__file__).parent
    files_dir = script_dir / 'Files'
    
    # Check if Files directory exists
    if not files_dir.exists():
        print(f"ERROR: Files directory not found at {files_dir}")
        return
    
    # Load labels
    labels_path = files_dir / 'labels.csv'
    if not labels_path.exists():
        print(f"ERROR: labels.csv not found at {labels_path}")
        return
    
    df = pd.read_csv(labels_path)
    print(f"Found {len(df)} datapoints in labels.csv\n")
    
    # Check image directories
    work_dir = files_dir / 'work'
    tool_dir = files_dir / 'tool'
    chip_dir = files_dir / 'chip'
    
    print("Checking image directories...")
    print(f"  Work: {work_dir.exists()} - {work_dir}")
    print(f"  Tool: {tool_dir.exists()} - {tool_dir}")
    print(f"  Chip: {chip_dir.exists()} - {chip_dir}")
    print()
    
    # Statistics
    complete_count = 0
    missing_work = 0
    missing_tool = 0
    missing_chip = 0
    complete_samples = []
    
    # Check each datapoint
    for idx, row in df.iterrows():
        image_id = row['id']
        
        # Check for each image type
        work_exists = (work_dir / f"{image_id}.png").exists()
        tool_exists = (tool_dir / f"{image_id}.jpg").exists()
        chip_exists = (chip_dir / f"{image_id}.jpg").exists()
        
        if work_exists and tool_exists and chip_exists:
            complete_count += 1
            complete_samples.append((idx, image_id))
        else:
            if not work_exists:
                missing_work += 1
            if not tool_exists:
                missing_tool += 1
            if not chip_exists:
                missing_chip += 1
    
    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total datapoints: {len(df)}")
    print(f"Complete image sets: {complete_count} ({complete_count/len(df)*100:.1f}%)")
    print(f"Missing work images: {missing_work}")
    print(f"Missing tool images: {missing_tool}")
    print(f"Missing chip images: {missing_chip}")
    print()
    
    if complete_count > 0:
        print("=" * 60)
        print(f"DATAPOINTS WITH COMPLETE IMAGES (first 20)")
        print("=" * 60)
        for idx, image_id in complete_samples[:20]:
            print(f"  Datapoint {idx:3d}: {image_id}")
        
        if len(complete_samples) > 20:
            print(f"  ... and {len(complete_samples) - 20} more")
        print()
        
        print("=" * 60)
        print("RECOMMENDATION")
        print("=" * 60)
        print(f"Use datapoint indices: {', '.join(str(idx) for idx, _ in complete_samples[:10])}")
        print("These have all required images for full predictions.")
    else:
        print("=" * 60)
        print("WARNING")
        print("=" * 60)
        print("No datapoints have complete image sets!")
        print("Please check your Files directory structure:")
        print("  Files/work/*.png")
        print("  Files/tool/*.jpg")
        print("  Files/chip/*.jpg")
    
    print()
    
    # Check for any images at all
    if work_dir.exists():
        work_files = list(work_dir.glob("*.png"))
        print(f"Found {len(work_files)} work images")
        if work_files:
            print(f"  Example: {work_files[0].name}")
    
    if tool_dir.exists():
        tool_files = list(tool_dir.glob("*.jpg"))
        print(f"Found {len(tool_files)} tool images")
        if tool_files:
            print(f"  Example: {tool_files[0].name}")
    
    if chip_dir.exists():
        chip_files = list(chip_dir.glob("*.jpg"))
        print(f"Found {len(chip_files)} chip images")
        if chip_files:
            print(f"  Example: {chip_files[0].name}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("IMAGE AVAILABILITY CHECKER")
    print("=" * 60 + "\n")
    
    try:
        check_image_availability()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
