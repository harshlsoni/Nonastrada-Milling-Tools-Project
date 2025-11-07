#!/usr/bin/env python3
"""
Script to create sample test data for the milling forces analysis pipeline.
Run this to generate synthetic test data in the custom_data folder.
"""

import numpy as np
from scipy.io import savemat
from PIL import Image
import os
import sys

def create_sample_test_data(output_dir, test_name="sample_test", 
                           duration=2, fs=10000, frequencies=None):
    """
    Create synthetic test data for pipeline testing.
    
    Args:
        output_dir: Base directory for custom data
        test_name: Name of the test case
        duration: Signal duration in seconds
        fs: Sampling frequency in Hz
        frequencies: Dict with 'x', 'y', 'z' frequency lists
    """
    
    # Create output directory
    test_dir = os.path.join(output_dir, test_name)
    os.makedirs(test_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Creating test data: {test_name}")
    print(f"{'='*60}\n")
    
    # Default frequencies if not provided
    if frequencies is None:
        frequencies = {
            'x': [50, 150],
            'y': [120, 200],
            'z': [300, 400]
        }
    
    # Generate time vector
    t = np.arange(0, duration, 1/fs)
    n_samples = len(t)
    
    print(f"Signal parameters:")
    print(f"  Duration: {duration} seconds")
    print(f"  Sampling frequency: {fs} Hz")
    print(f"  Samples per axis: {n_samples:,}")
    print()
    
    # Generate force signals for each axis
    def generate_axis_signal(freqs, noise_level=0.2):
        signal = np.zeros(n_samples)
        for i, freq in enumerate(freqs):
            amplitude = 1.0 / (i + 1)  # Decreasing amplitude for harmonics
            signal += amplitude * np.sin(2*np.pi*freq*t)
        signal += noise_level * np.random.randn(n_samples)
        return signal
    
    x_force = generate_axis_signal(frequencies['x'])
    y_force = generate_axis_signal(frequencies['y'])
    z_force = generate_axis_signal(frequencies['z'])
    
    print(f"Force signal frequencies:")
    print(f"  X-axis: {frequencies['x']} Hz")
    print(f"  Y-axis: {frequencies['y']} Hz")
    print(f"  Z-axis: {frequencies['z']} Hz")
    print()
    
    # Create MAT file with baseDatastore structure
    force_data = np.vstack([x_force, y_force, z_force])
    baseDatastore = np.empty((1, 4), dtype=object)
    # Fill all columns (columns 0-2 can be empty strings, column 3 has force data)
    baseDatastore[0, 0] = ''
    baseDatastore[0, 1] = ''
    baseDatastore[0, 2] = ''
    baseDatastore[0, 3] = force_data
    
    mat_path = os.path.join(test_dir, 'force_data.mat')
    savemat(mat_path, {'baseDatastore': baseDatastore})
    print(f"✓ Created: {mat_path}")
    print(f"  Shape: {force_data.shape}")
    
    # Create sample images with different patterns
    img_size = 224
    
    # Work image (blue gradient - represents workpiece)
    work_img = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    work_img[:, :, 2] = 150  # Blue base
    gradient = np.linspace(0, 100, img_size).reshape(1, -1)
    work_img[:, :, 0] = gradient  # Red gradient
    work_img[:, :, 1] = gradient * 0.5  # Green gradient
    Image.fromarray(work_img).save(os.path.join(test_dir, 'work.png'))
    print(f"✓ Created: work.png ({img_size}×{img_size})")
    
    # Tool image (gray with texture - represents cutting tool)
    tool_img = np.ones((img_size, img_size, 3), dtype=np.uint8) * 128
    texture = np.linspace(-50, 50, img_size).reshape(-1, 1)
    tool_img[:, :, 0] = np.clip(128 + texture, 0, 255).astype(np.uint8)
    tool_img[:, :, 1] = np.clip(128 + texture * 0.5, 0, 255).astype(np.uint8)
    tool_img[:, :, 2] = np.clip(128 + texture * 0.3, 0, 255).astype(np.uint8)
    Image.fromarray(tool_img).save(os.path.join(test_dir, 'tool.jpg'))
    print(f"✓ Created: tool.jpg ({img_size}×{img_size})")
    
    # Chip image (brown/copper color - represents metal chips)
    chip_img = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    chip_img[:, :, 0] = 139  # Red
    chip_img[:, :, 1] = 90   # Green
    chip_img[:, :, 2] = 43   # Blue
    # Add some variation
    variation = (np.random.rand(img_size, img_size) * 40 - 20).astype(np.int16)
    for c in range(3):
        chip_img[:, :, c] = np.clip(chip_img[:, :, c] + variation, 0, 255).astype(np.uint8)
    Image.fromarray(chip_img).save(os.path.join(test_dir, 'chip.jpg'))
    print(f"✓ Created: chip.jpg ({img_size}×{img_size})")
    
    print(f"\n{'='*60}")
    print(f"Test data created successfully!")
    print(f"Location: {test_dir}")
    print(f"{'='*60}\n")
    
    return test_dir


def create_multiple_test_cases():
    """Create several test cases with different characteristics."""
    
    print("\n" + "="*60)
    print("CREATING MULTIPLE TEST CASES")
    print("="*60)
    
    # Test case 1: Low frequency vibrations
    create_sample_test_data(
        "custom_data",
        "sample_test_1_low_freq",
        duration=2,
        fs=10000,
        frequencies={'x': [30, 80], 'y': [50, 100], 'z': [150, 250]}
    )
    
    # Test case 2: High frequency vibrations
    create_sample_test_data(
        "custom_data",
        "sample_test_2_high_freq",
        duration=2,
        fs=10000,
        frequencies={'x': [200, 400], 'y': [300, 500], 'z': [600, 800]}
    )
    
    # Test case 3: Mixed frequencies (more realistic)
    create_sample_test_data(
        "custom_data",
        "sample_test_3_mixed",
        duration=3,
        fs=10000,
        frequencies={'x': [50, 150, 300], 'y': [120, 250, 400], 'z': [300, 500, 700]}
    )
    
    print("\n" + "="*60)
    print("ALL TEST CASES CREATED")
    print("="*60)
    print("\nYou can now test the pipeline with:")
    print("  - custom_data/sample_test_1_low_freq/")
    print("  - custom_data/sample_test_2_high_freq/")
    print("  - custom_data/sample_test_3_mixed/")
    print()


def validate_test_data(test_dir):
    """Validate that test data is correctly formatted."""
    
    print(f"\n{'='*60}")
    print(f"VALIDATING: {test_dir}")
    print(f"{'='*60}\n")
    
    valid = True
    
    # Check directory exists
    if not os.path.exists(test_dir):
        print(f"✗ Directory not found: {test_dir}")
        return False
    
    # Check MAT file
    mat_files = [f for f in os.listdir(test_dir) if f.endswith('.mat')]
    if not mat_files:
        print("✗ No MAT file found")
        valid = False
    else:
        mat_path = os.path.join(test_dir, mat_files[0])
        try:
            from scipy.io import loadmat
            mat_data = loadmat(mat_path)
            
            if 'baseDatastore' not in mat_data:
                print("✗ 'baseDatastore' not found in MAT file")
                valid = False
            else:
                bd = mat_data['baseDatastore']
                force_data = bd[0, 3]
                
                if force_data.shape[0] != 3:
                    print(f"⚠ Expected 3 axes, got {force_data.shape[0]}")
                
                print(f"✓ MAT file: {mat_files[0]}")
                print(f"  Shape: {force_data.shape}")
                print(f"  Samples: {force_data.shape[1]:,} per axis")
                print(f"  X-axis range: [{force_data[0].min():.3f}, {force_data[0].max():.3f}]")
                print(f"  Y-axis range: [{force_data[1].min():.3f}, {force_data[1].max():.3f}]")
                print(f"  Z-axis range: [{force_data[2].min():.3f}, {force_data[2].max():.3f}]")
                
        except Exception as e:
            print(f"✗ Error loading MAT file: {e}")
            valid = False
    
    print()
    
    # Check images
    required_images = {
        'work.png': 'Work image',
        'tool.jpg': 'Tool image',
        'chip.jpg': 'Chip image'
    }
    
    for img_file, desc in required_images.items():
        img_path = os.path.join(test_dir, img_file)
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                print(f"✓ {desc}: {img_file}")
                print(f"  Size: {img.size[0]}×{img.size[1]}")
                print(f"  Mode: {img.mode}")
            except Exception as e:
                print(f"✗ Error loading {img_file}: {e}")
                valid = False
        else:
            print(f"✗ {desc}: {img_file} NOT FOUND")
            valid = False
    
    print(f"\n{'='*60}")
    if valid:
        print("✓ VALIDATION PASSED")
    else:
        print("✗ VALIDATION FAILED")
    print(f"{'='*60}\n")
    
    return valid


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create sample test data for milling analysis')
    parser.add_argument('--name', type=str, default='sample_test_1',
                       help='Name of the test case (default: sample_test_1)')
    parser.add_argument('--duration', type=float, default=2.0,
                       help='Signal duration in seconds (default: 2.0)')
    parser.add_argument('--fs', type=int, default=10000,
                       help='Sampling frequency in Hz (default: 10000)')
    parser.add_argument('--multiple', action='store_true',
                       help='Create multiple test cases with different characteristics')
    parser.add_argument('--validate', type=str,
                       help='Validate existing test data directory')
    
    args = parser.parse_args()
    
    if args.validate:
        validate_test_data(args.validate)
    elif args.multiple:
        create_multiple_test_cases()
    else:
        test_dir = create_sample_test_data(
            "custom_data",
            args.name,
            duration=args.duration,
            fs=args.fs
        )
        
        # Validate the created data
        validate_test_data(test_dir)
        
        print("\nTo test this data:")
        print(f"  1. Start Flask app: python Code/flask_app.py")
        print(f"  2. Upload files from: {test_dir}")
        print(f"  3. Or use Python script to process directly")
