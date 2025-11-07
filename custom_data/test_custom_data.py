#!/usr/bin/env python3
"""
Script to test custom data with the milling forces analysis pipeline.
"""

import sys
import os

# Add Code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Code'))

from Preprocessing_Pipeline import generate_timefrequency_representation
from scipy.io import loadmat
import numpy as np
from PIL import Image

def test_custom_data(test_dir, output_dir=None):
    """
    Test custom data through the pipeline.
    
    Args:
        test_dir: Directory containing test data
        output_dir: Directory for output (default: test_dir/results)
    """
    
    print(f"\n{'='*60}")
    print(f"TESTING CUSTOM DATA")
    print(f"{'='*60}\n")
    print(f"Test directory: {test_dir}")
    
    # Set output directory
    if output_dir is None:
        output_dir = os.path.join(test_dir, 'results')
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}\n")
    
    # Load MAT file
    mat_files = [f for f in os.listdir(test_dir) if f.endswith('.mat')]
    if not mat_files:
        print("ERROR: No MAT file found")
        return False
    
    mat_path = os.path.join(test_dir, mat_files[0])
    print(f"Loading: {mat_files[0]}")
    
    try:
        mat_data = loadmat(mat_path)
        force_data = mat_data['baseDatastore'][0, 3]
        
        # Extract axes
        x = force_data[0, :]
        y = force_data[1, :]
        z = force_data[2, :]
        
        print(f"  X-axis: {len(x):,} samples, range [{x.min():.3f}, {x.max():.3f}]")
        print(f"  Y-axis: {len(y):,} samples, range [{y.min():.3f}, {y.max():.3f}]")
        print(f"  Z-axis: {len(z):,} samples, range [{z.min():.3f}, {z.max():.3f}]")
        print()
        
    except Exception as e:
        print(f"ERROR loading MAT file: {e}")
        return False
    
    # Check images
    print("Checking images...")
    work_path = os.path.join(test_dir, 'work.png')
    tool_path = os.path.join(test_dir, 'tool.jpg')
    chip_path = os.path.join(test_dir, 'chip.jpg')
    
    images_ok = True
    for img_path, name in [(work_path, 'Work'), (tool_path, 'Tool'), (chip_path, 'Chip')]:
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                print(f"  ✓ {name}: {img.size[0]}×{img.size[1]}, {img.mode}")
            except Exception as e:
                print(f"  ✗ {name}: Error loading - {e}")
                images_ok = False
        else:
            print(f"  ✗ {name}: Not found")
            images_ok = False
    
    if not images_ok:
        print("\nWARNING: Some images missing or invalid")
    print()
    
    # Generate time-frequency representations
    print("Generating time-frequency representations...")
    print("This may take a minute...\n")
    
    try:
        tfr = generate_timefrequency_representation(
            x, y, z,
            fs=10000,
            plot=True,
            outdir=output_dir,
            prefix='test_'
        )
        
        print(f"\n{'='*60}")
        print("SUCCESS!")
        print(f"{'='*60}\n")
        
        # List generated files
        result_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
        print(f"Generated {len(result_files)} visualization files:")
        for f in sorted(result_files):
            print(f"  - {f}")
        
        print(f"\nResults saved to: {output_dir}")
        print("\nYou can now:")
        print("  1. View the generated spectrograms and scalograms")
        print("  2. Upload this data via the web interface for full analysis")
        print("  3. Use the data for model predictions")
        
        return True
        
    except Exception as e:
        print(f"\nERROR during processing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_samples():
    """Test all sample data in custom_data folder."""
    
    custom_data_dir = os.path.dirname(__file__)
    
    # Find all test directories
    test_dirs = []
    for item in os.listdir(custom_data_dir):
        item_path = os.path.join(custom_data_dir, item)
        if os.path.isdir(item_path) and item.startswith('sample_test'):
            test_dirs.append(item_path)
    
    if not test_dirs:
        print("No test directories found")
        print("Run: python custom_data/create_sample_data.py --multiple")
        return
    
    print(f"\nFound {len(test_dirs)} test directories")
    print("="*60)
    
    results = {}
    for test_dir in sorted(test_dirs):
        test_name = os.path.basename(test_dir)
        print(f"\nTesting: {test_name}")
        success = test_custom_data(test_dir)
        results[test_name] = success
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}\n")
    
    for test_name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for s in results.values() if s)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test custom data with the pipeline')
    parser.add_argument('--dir', type=str,
                       help='Specific test directory to process')
    parser.add_argument('--all', action='store_true',
                       help='Test all sample directories')
    parser.add_argument('--output', type=str,
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    if args.all:
        test_all_samples()
    elif args.dir:
        test_custom_data(args.dir, args.output)
    else:
        # Default: test first sample
        default_dir = os.path.join(os.path.dirname(__file__), 'sample_test_1_low_freq')
        if os.path.exists(default_dir):
            test_custom_data(default_dir)
        else:
            print("No test data found.")
            print("\nCreate sample data first:")
            print("  python custom_data/create_sample_data.py --multiple")
            print("\nThen test it:")
            print("  python custom_data/test_custom_data.py --all")
