# Custom Data Folder - Summary

## What Was Created

A complete `custom_data/` folder for testing the milling forces analysis pipeline with custom data.

## Structure

```
custom_data/
├── README.md                    # Comprehensive documentation
├── USAGE_GUIDE.md              # Quick start guide
├── create_sample_data.py       # Script to generate test data
├── test_custom_data.py         # Script to test data through pipeline
├── .gitignore                  # Git ignore rules
│
├── sample_test_1_low_freq/     # Low frequency test (30-250 Hz)
│   ├── force_data.mat
│   ├── work.png
│   ├── tool.jpg
│   ├── chip.jpg
│   └── results/                # Generated visualizations
│       ├── test_x_spectrogram.png
│       ├── test_x_scalogram.png
│       ├── test_y_spectrogram.png
│       ├── test_y_scalogram.png
│       ├── test_z_spectrogram.png
│       └── test_z_scalogram.png
│
├── sample_test_2_high_freq/    # High frequency test (200-800 Hz)
│   └── ... (same structure)
│
└── sample_test_3_mixed/        # Mixed frequencies (50-700 Hz)
    └── ... (same structure)
```

## Features

### 1. Sample Data Generation

**Script**: `create_sample_data.py`

**Capabilities**:
- Generate synthetic force signals with custom frequencies
- Create realistic test images (work, tool, chip)
- Support multiple test cases with different characteristics
- Validate generated data

**Usage**:
```bash
# Create multiple test cases
python custom_data/create_sample_data.py --multiple

# Create single custom test
python custom_data/create_sample_data.py --name my_test --duration 3

# Validate existing data
python custom_data/create_sample_data.py --validate custom_data/my_test
```

### 2. Data Testing

**Script**: `test_custom_data.py`

**Capabilities**:
- Load and validate custom MAT files
- Process through time-frequency analysis
- Generate spectrograms and scalograms
- Test all samples at once

**Usage**:
```bash
# Test all samples
python custom_data/test_custom_data.py --all

# Test specific sample
python custom_data/test_custom_data.py --dir custom_data/sample_test_1_low_freq
```

### 3. Pre-Generated Samples

Three ready-to-use test cases:

**Sample 1: Low Frequency**
- Frequencies: X(30,80), Y(50,100), Z(150,250) Hz
- Duration: 2 seconds
- Use case: Heavy cutting, slow operations

**Sample 2: High Frequency**
- Frequencies: X(200,400), Y(300,500), Z(600,800) Hz
- Duration: 2 seconds
- Use case: High-speed machining, finishing

**Sample 3: Mixed**
- Frequencies: X(50,150,300), Y(120,250,400), Z(300,500,700) Hz
- Duration: 3 seconds
- Use case: Variable conditions, realistic scenario

## How to Use

### Method 1: Web Interface

1. Start Flask app:
   ```bash
   python Code/flask_app.py
   ```

2. Open browser to `http://localhost:5000`

3. Use "Upload Custom Data" form:
   - Upload `force_data.mat` from any sample folder
   - Upload corresponding images
   - Click "Run Pipeline"

### Method 2: Python Script

```python
from custom_data.test_custom_data import test_custom_data

# Test a specific sample
test_custom_data("custom_data/sample_test_1_low_freq")
```

### Method 3: Direct Pipeline Access

```python
from Code.Preprocessing_Pipeline import generate_timefrequency_representation
from scipy.io import loadmat

# Load data
mat_data = loadmat('custom_data/sample_test_1_low_freq/force_data.mat')
force_data = mat_data['baseDatastore'][0, 3]

x, y, z = force_data[0, :], force_data[1, :], force_data[2, :]

# Generate TFR
tfr = generate_timefrequency_representation(
    x, y, z,
    fs=10000,
    plot=True,
    outdir='output',
    prefix='my_test_'
)
```

## Data Format

### MAT File Structure

```python
{
    'baseDatastore': [
        [
            '',  # Column 0 (empty)
            '',  # Column 1 (empty)
            '',  # Column 2 (empty)
            array([[x_force],  # Column 3: Force data
                   [y_force],  # 3×N array
                   [z_force]])
        ]
    ]
}
```

### Image Requirements

- **Work image**: PNG format, 224×224 pixels, RGB
- **Tool image**: JPG format, 224×224 pixels, RGB
- **Chip image**: JPG format, 224×224 pixels, RGB

## Creating Custom Data

### From Scratch

```python
from custom_data.create_sample_data import create_sample_test_data

create_sample_test_data(
    output_dir="custom_data",
    test_name="my_custom_test",
    duration=5,
    fs=10000,
    frequencies={
        'x': [40, 120, 250],
        'y': [80, 180, 300],
        'z': [200, 400, 600]
    }
)
```

### From Real Dataset

```python
from Code.sample_raw_force_data import get_random_force_streams_with_images
import scipy.io as sio
import numpy as np
from PIL import Image
import os

# Extract from main dataset
x, y, z, work, tool, chip, metadata = get_random_force_streams_with_images()

# Save to custom_data
test_dir = f"custom_data/extracted_{metadata['datapoint_index']}"
os.makedirs(test_dir, exist_ok=True)

# Save MAT file
baseDatastore = np.empty((1, 4), dtype=object)
baseDatastore[0, 0] = ''
baseDatastore[0, 1] = ''
baseDatastore[0, 2] = ''
baseDatastore[0, 3] = np.vstack([x, y, z])
sio.savemat(f'{test_dir}/force_data.mat', {'baseDatastore': baseDatastore})

# Save images
Image.fromarray(work).save(f'{test_dir}/work.png')
Image.fromarray(tool).save(f'{test_dir}/tool.jpg')
Image.fromarray(chip).save(f'{test_dir}/chip.jpg')
```

## Benefits

1. **Isolated Testing**: Test without affecting main dataset
2. **Reproducible**: Same test data every time
3. **Customizable**: Create data matching your needs
4. **Educational**: Learn data format and pipeline
5. **Debugging**: Isolate issues with known data

## Validation

All generated data is automatically validated for:
- Correct MAT file structure
- Proper force data shape (3×N)
- Image file existence and format
- Reasonable signal ranges

## Documentation

- **README.md**: Comprehensive guide with all details
- **USAGE_GUIDE.md**: Quick start and common use cases
- **This file**: High-level summary

## Quick Reference

```bash
# Create samples
python custom_data/create_sample_data.py --multiple

# Test samples
python custom_data/test_custom_data.py --all

# Validate data
python custom_data/create_sample_data.py --validate custom_data/my_test

# Use via web
python Code/flask_app.py
# Upload from custom_data/sample_test_X/
```

## Integration with Main System

The custom_data folder integrates seamlessly with:
- Web interface (upload form)
- Python scripts (direct import)
- Pipeline functions (same format as main data)
- Model predictions (when images provided)

## Next Steps

1. Review the generated samples
2. Test them through the pipeline
3. Create your own custom test cases
4. Use for development and debugging
5. Share test cases with team

For detailed information, see:
- `custom_data/README.md` - Full documentation
- `custom_data/USAGE_GUIDE.md` - Quick start guide
