# Custom Test Data Folder

This folder is for storing custom test data to use with the milling forces analysis pipeline.

## Purpose

Use this folder to test the pipeline with your own data without modifying the main `Files` directory. This is useful for:
- Testing with different milling conditions
- Validating the pipeline with new datasets
- Experimenting without affecting production data
- Quick prototyping and debugging

## Folder Structure

```
custom_data/
├── README.md (this file)
├── sample_test_1/
│   ├── force_data.mat (MAT file with force signals)
│   ├── work.png (workpiece image)
│   ├── tool.jpg (tool image)
│   └── chip.jpg (chip image)
├── sample_test_2/
│   └── ... (another test case)
└── your_test_name/
    └── ... (your custom data)
```

## Data Format Requirements

### 1. Force Data (MAT file)

**File**: `force_data.mat` or any `.mat` file

**Required structure**:
- Must contain a variable named `baseDatastore`
- Format: 2D array where each row is a datapoint
- Column 4 (index 3) should contain force data
- Force data should be 3×N array (X, Y, Z axes)

**Example in MATLAB**:
```matlab
% Create sample force data
fs = 10000; % Sampling frequency
duration = 2; % seconds
t = 0:1/fs:duration-1/fs;

% Generate synthetic force signals
x_force = sin(2*pi*50*t) + 0.2*randn(size(t));
y_force = sin(2*pi*120*t) + 0.2*randn(size(t));
z_force = sin(2*pi*300*t) + 0.2*randn(size(t));

% Combine into 3×N array
force_data = [x_force; y_force; z_force];

% Create baseDatastore structure
baseDatastore = cell(1, 4);
baseDatastore{1, 4} = force_data;

% Save
save('force_data.mat', 'baseDatastore');
```

**Example in Python**:
```python
import numpy as np
from scipy.io import savemat

# Generate sample force data
fs = 10000
duration = 2
t = np.arange(0, duration, 1/fs)

x_force = np.sin(2*np.pi*50*t) + 0.2*np.random.randn(len(t))
y_force = np.sin(2*np.pi*120*t) + 0.2*np.random.randn(len(t))
z_force = np.sin(2*np.pi*300*t) + 0.2*np.random.randn(len(t))

# Combine into 3×N array
force_data = np.vstack([x_force, y_force, z_force])

# Create baseDatastore structure
baseDatastore = np.empty((1, 4), dtype=object)
baseDatastore[0, 3] = force_data

# Save
savemat('force_data.mat', {'baseDatastore': baseDatastore})
```

### 2. Images

**Work Image**: `work.png`
- Format: PNG
- Recommended size: 224×224 pixels (will be resized if different)
- RGB color image
- Shows the workpiece/material being machined

**Tool Image**: `tool.jpg`
- Format: JPG/JPEG
- Recommended size: 224×224 pixels
- RGB color image
- Shows the cutting tool

**Chip Image**: `chip.jpg`
- Format: JPG/JPEG
- Recommended size: 224×224 pixels
- RGB color image
- Shows the chips/swarf produced during machining

## How to Use

### Method 1: Via Web Interface

1. Start the Flask application:
   ```bash
   python Code/flask_app.py
   ```

2. Open browser to `http://localhost:5000`

3. Use the "Upload Custom Data" form:
   - Upload your MAT file
   - Upload work, tool, and chip images
   - Set sampling frequency (default: 10000 Hz)
   - Click "Run Pipeline"

### Method 2: Via Python Script

```python
from Code.Preprocessing_Pipeline import generate_timefrequency_representation
from scipy.io import loadmat
import numpy as np

# Load your custom MAT file
mat_data = loadmat('custom_data/sample_test_1/force_data.mat')
force_data = mat_data['baseDatastore'][0, 3]

# Extract axes
x = force_data[0, :]
y = force_data[1, :]
z = force_data[2, :]

# Generate time-frequency representations
tfr = generate_timefrequency_representation(
    x, y, z,
    fs=10000,
    plot=True,
    outdir='custom_data/sample_test_1/results',
    prefix='test_'
)

print("Spectrograms and scalograms generated!")
```

### Method 3: Test Specific Datapoint

```python
from Code.sample_raw_force_data import get_random_force_streams_with_images

# Get data from main dataset
x, y, z, work, tool, chip, metadata = get_random_force_streams_with_images()

# Save for testing
import scipy.io as sio
import numpy as np
from PIL import Image

# Save force data
baseDatastore = np.empty((1, 4), dtype=object)
baseDatastore[0, 3] = np.vstack([x, y, z])
sio.savemat('custom_data/extracted_sample/force_data.mat', 
            {'baseDatastore': baseDatastore})

# Save images
Image.fromarray(work).save('custom_data/extracted_sample/work.png')
Image.fromarray(tool).save('custom_data/extracted_sample/tool.jpg')
Image.fromarray(chip).save('custom_data/extracted_sample/chip.jpg')

print(f"Saved datapoint {metadata['datapoint_index']} to custom_data/extracted_sample/")
```

## Sample Data Generation Script

Create synthetic test data:

```python
import numpy as np
from scipy.io import savemat
from PIL import Image
import os

def create_sample_test_data(output_dir, test_name="sample_test"):
    """Create synthetic test data for pipeline testing."""
    
    # Create output directory
    test_dir = os.path.join(output_dir, test_name)
    os.makedirs(test_dir, exist_ok=True)
    
    # Generate force signals
    fs = 10000
    duration = 2
    t = np.arange(0, duration, 1/fs)
    
    # Simulate different milling conditions
    x_force = np.sin(2*np.pi*50*t) + 0.3*np.sin(2*np.pi*150*t) + 0.2*np.random.randn(len(t))
    y_force = np.sin(2*np.pi*120*t) + 0.3*np.sin(2*np.pi*200*t) + 0.2*np.random.randn(len(t))
    z_force = np.sin(2*np.pi*300*t) + 0.3*np.sin(2*np.pi*400*t) + 0.2*np.random.randn(len(t))
    
    # Create MAT file
    force_data = np.vstack([x_force, y_force, z_force])
    baseDatastore = np.empty((1, 4), dtype=object)
    baseDatastore[0, 3] = force_data
    
    mat_path = os.path.join(test_dir, 'force_data.mat')
    savemat(mat_path, {'baseDatastore': baseDatastore})
    print(f"Created: {mat_path}")
    
    # Create sample images (colored patterns)
    img_size = 224
    
    # Work image (blue-ish)
    work_img = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    work_img[:, :, 2] = 150  # Blue channel
    work_img[:, :, 0] = np.linspace(0, 100, img_size).reshape(1, -1)
    Image.fromarray(work_img).save(os.path.join(test_dir, 'work.png'))
    print(f"Created: work.png")
    
    # Tool image (gray-ish)
    tool_img = np.ones((img_size, img_size, 3), dtype=np.uint8) * 128
    tool_img[:, :, 0] += np.linspace(-50, 50, img_size).reshape(-1, 1).astype(np.uint8)
    Image.fromarray(tool_img).save(os.path.join(test_dir, 'tool.jpg'))
    print(f"Created: tool.jpg")
    
    # Chip image (brown-ish)
    chip_img = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    chip_img[:, :, 0] = 139  # Red
    chip_img[:, :, 1] = 90   # Green
    chip_img[:, :, 2] = 43   # Blue
    Image.fromarray(chip_img).save(os.path.join(test_dir, 'chip.jpg'))
    print(f"Created: chip.jpg")
    
    print(f"\nTest data created in: {test_dir}")
    print(f"Samples: {len(t)} per axis")
    print(f"Duration: {duration} seconds")
    print(f"Sampling frequency: {fs} Hz")

# Run it
if __name__ == "__main__":
    create_sample_test_data("custom_data", "sample_test_1")
```

## Validation

To verify your custom data is correctly formatted:

```python
from scipy.io import loadmat
import numpy as np
from PIL import Image
import os

def validate_test_data(test_dir):
    """Validate custom test data format."""
    
    print(f"Validating: {test_dir}")
    print("=" * 60)
    
    # Check MAT file
    mat_files = [f for f in os.listdir(test_dir) if f.endswith('.mat')]
    if not mat_files:
        print("ERROR: No MAT file found")
        return False
    
    mat_path = os.path.join(test_dir, mat_files[0])
    try:
        mat_data = loadmat(mat_path)
        if 'baseDatastore' not in mat_data:
            print("ERROR: 'baseDatastore' not found in MAT file")
            return False
        
        bd = mat_data['baseDatastore']
        force_data = bd[0, 3]
        
        if force_data.shape[0] != 3:
            print(f"WARNING: Expected 3 axes, got {force_data.shape[0]}")
        
        print(f"✓ MAT file: {mat_files[0]}")
        print(f"  Shape: {force_data.shape}")
        print(f"  Samples: {force_data.shape[1]} per axis")
        
    except Exception as e:
        print(f"ERROR loading MAT file: {e}")
        return False
    
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
                print(f"✓ {desc}: {img_file} ({img.size[0]}×{img.size[1]})")
            except Exception as e:
                print(f"ERROR loading {img_file}: {e}")
        else:
            print(f"✗ {desc}: {img_file} NOT FOUND")
    
    print("=" * 60)
    print("Validation complete!")
    return True

# Run it
if __name__ == "__main__":
    validate_test_data("custom_data/sample_test_1")
```

## Tips

1. **Sampling Frequency**: Make sure to set the correct sampling frequency (default: 10000 Hz)
2. **Signal Length**: Longer signals (2-5 seconds) work better for frequency analysis
3. **Image Quality**: Higher resolution images (224×224 or larger) give better results
4. **File Naming**: Keep consistent naming for easy organization
5. **Backup**: Keep original data backed up before processing

## Troubleshooting

### "baseDatastore not found"
- Check MAT file structure
- Ensure variable is named exactly `baseDatastore`
- Use `scipy.io.loadmat()` to inspect file contents

### "Signal is empty"
- Verify force data is in column 4 (index 3)
- Check data shape is 3×N (three axes)
- Ensure data is numeric, not empty

### "Image not found"
- Check file names match exactly (case-sensitive)
- Verify file extensions (.png for work, .jpg for tool/chip)
- Ensure files are in the correct directory

### "Prediction failed"
- All three images must be present for predictions
- Images must be valid RGB format
- Check model file exists in Files directory

## Examples

See the included sample test cases:
- `sample_test_1/` - Basic synthetic data
- `sample_test_2/` - Different frequency patterns
- `extracted_sample/` - Real data from main dataset

## Next Steps

1. Create your test data following the format above
2. Validate using the validation script
3. Test via web interface or Python script
4. Review generated spectrograms and scalograms
5. Iterate and refine your test cases

For questions or issues, refer to the main documentation in the project root.
