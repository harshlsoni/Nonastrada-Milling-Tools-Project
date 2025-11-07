import scipy.io
import numpy as np
import json
import random
import os
import pandas as pd
from datetime import datetime
from PIL import Image

def extract_random_force_data(mat_file_path=None, output_dir='uploads', save_json=True):
    """
    Randomly picks a datapoint from baseDatastore and extracts force data.
    
    Args:
        mat_file_path (str): Path to the MATLAB file
        output_dir (str): Directory to save the JSON output
        save_json (bool): Whether to save JSON file or just return data
    
    Returns:
        dict: Dictionary containing the extracted force data
    """
    try:
        # Set default path if not provided
        if mat_file_path is None:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to project root and then to Files directory
            mat_file_path = os.path.join(os.path.dirname(script_dir), 'Files', 'forces_xyz_raw.mat')
        
        # Load the MATLAB file
        print(f"Loading MATLAB file: {mat_file_path}")
        mat_data = scipy.io.loadmat(mat_file_path)
        
        # Extract baseDatastore
        base_datastore = mat_data['baseDatastore']
        print(f"BaseDatastore shape: {base_datastore.shape}")
        
        # Get the number of available datapoints
        num_datapoints = base_datastore.shape[0]
        print(f"Total datapoints available: {num_datapoints}")
        
        # Randomly select a datapoint
        random_index = random.randint(0, num_datapoints - 1)
        print(f"Selected random datapoint index: {random_index}")
        
        # Extract the force data from the 4th column (index 3)
        force_data_cell = base_datastore[random_index, 3]
        
        # Convert to numpy array if it's not already
        if hasattr(force_data_cell, 'shape'):
            force_data = force_data_cell
        else:
            force_data = np.array(force_data_cell)
        
        print(f"Force data shape: {force_data.shape}")
        
        # Extract data for each axis
        x_axis_data = force_data[0, :].tolist()  # Top row - X axis
        y_axis_data = force_data[1, :].tolist()  # Middle row - Y axis  
        z_axis_data = force_data[2, :].tolist()  # Bottom row - Z axis
        
        # Create the data structure
        extracted_data = {
            'metadata': {
                'datapoint_index': int(random_index),
                'total_datapoints': int(num_datapoints),
                'extraction_timestamp': datetime.now().isoformat(),
                'data_shape': list(force_data.shape),
                'sample_count': len(x_axis_data)
            },
            'force_data': {
                'x_axis': x_axis_data,
                'y_axis': y_axis_data,
                'z_axis': z_axis_data
            }
        }
        
        # Optionally save to JSON file
        if save_json:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename with timestamp and datapoint index
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"force_data_sample_{random_index}_{timestamp}.json"
            output_path = os.path.join(output_dir, filename)
            
            # Save to JSON file
            with open(output_path, 'w') as f:
                json.dump(extracted_data, f, indent=2)
            
            print(f"Force data successfully saved to: {output_path}")
        
        print(f"Sample contains {len(x_axis_data)} data points per axis")
        
        return extracted_data
        
    except Exception as e:
        print(f"Error extracting force data: {str(e)}")
        raise

def get_random_force_streams(mat_file_path=None):
    """
    Get random force data as numpy arrays for streaming.
    
    Args:
        mat_file_path (str): Path to the MATLAB file
    
    Returns:
        tuple: (x_array, y_array, z_array, metadata_dict)
    """
    try:
        # Set default path if not provided
        if mat_file_path is None:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to project root and then to Files directory
            mat_file_path = os.path.join(os.path.dirname(script_dir), 'Files', 'forces_xyz_raw.mat')
        
        # Load the MATLAB file
        mat_data = scipy.io.loadmat(mat_file_path)
        base_datastore = mat_data['baseDatastore']
        
        # Get random datapoint
        num_datapoints = base_datastore.shape[0]
        random_index = random.randint(0, num_datapoints - 1)
        
        # Extract force data from 4th column (index 3)
        force_data_cell = base_datastore[random_index, 3]
        
        if hasattr(force_data_cell, 'shape'):
            force_data = force_data_cell
        else:
            force_data = np.array(force_data_cell)
        
        # Extract arrays for each axis
        x_array = force_data[0, :].astype(np.float64)
        y_array = force_data[1, :].astype(np.float64) 
        z_array = force_data[2, :].astype(np.float64)
        
        metadata = {
            'datapoint_index': int(random_index),
            'total_datapoints': int(num_datapoints),
            'sample_count': len(x_array),
            'data_shape': list(force_data.shape),
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        print(f"Extracted streams from datapoint {random_index}: {len(x_array)} samples per axis")
        return x_array, y_array, z_array, metadata
        
    except Exception as e:
        print(f"Error getting force streams: {str(e)}")
        raise

def get_image_id_for_datapoint(datapoint_index, labels_file_path=None):
    """
    Map datapoint index to corresponding image ID.
    
    Args:
        datapoint_index (int): Index of the datapoint (0-511)
        labels_file_path (str): Path to labels.csv file
    
    Returns:
        str: Image ID (e.g., 'T1R2B3') or None if not found
    """
    try:
        if labels_file_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            labels_file_path = os.path.join(os.path.dirname(script_dir), 'Files', 'labels.csv')
        
        # Read labels file
        df = pd.read_csv(labels_file_path)
        
        # Check if datapoint_index is within range
        if 0 <= datapoint_index < len(df):
            image_id = df.iloc[datapoint_index]['id']
            return image_id
        else:
            print(f"Datapoint index {datapoint_index} out of range (0-{len(df)-1})")
            return None
            
    except Exception as e:
        print(f"Error mapping datapoint to image ID: {e}")
        return None

def load_real_images_for_datapoint(datapoint_index, files_dir=None):
    """
    Load real work, tool, and chip images for a given datapoint.
    
    Args:
        datapoint_index (int): Index of the datapoint
        files_dir (str): Path to Files directory
    
    Returns:
        tuple: (work_img_array, tool_img_array, chip_img_array) or (None, None, None) if not found
    """
    try:
        if files_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            files_dir = os.path.join(os.path.dirname(script_dir), 'Files')
        
        # Get image ID for this datapoint
        image_id = get_image_id_for_datapoint(datapoint_index)
        if image_id is None:
            return None, None, None
        
        # Construct image paths
        work_path = os.path.join(files_dir, 'work', f'{image_id}.png')
        tool_path = os.path.join(files_dir, 'tool', f'{image_id}.jpg')
        chip_path = os.path.join(files_dir, 'chip', f'{image_id}.jpg')
        
        # Load images
        work_img = None
        tool_img = None
        chip_img = None
        
        if os.path.exists(work_path):
            work_img = np.array(Image.open(work_path).convert('RGB'))
            print(f"Loaded work image: {work_path} ({work_img.shape})")
        
        if os.path.exists(tool_path):
            tool_img = np.array(Image.open(tool_path).convert('RGB'))
            print(f"Loaded tool image: {tool_path} ({tool_img.shape})")
        
        if os.path.exists(chip_path):
            chip_img = np.array(Image.open(chip_path).convert('RGB'))
            print(f"Loaded chip image: {chip_path} ({chip_img.shape})")
        
        return work_img, tool_img, chip_img
        
    except Exception as e:
        print(f"Error loading real images: {e}")
        return None, None, None

def get_random_force_streams_with_images(mat_file_path=None):
    """
    Get random force data and corresponding real images.
    
    Returns:
        tuple: (x_array, y_array, z_array, work_img, tool_img, chip_img, metadata_dict)
    """
    try:
        # Get force data
        x, y, z, metadata = get_random_force_streams(mat_file_path)
        
        # Get real images for this datapoint
        work_img, tool_img, chip_img = load_real_images_for_datapoint(metadata['datapoint_index'])
        
        # Add image info to metadata
        image_id = get_image_id_for_datapoint(metadata['datapoint_index'])
        metadata['image_id'] = image_id
        metadata['has_real_images'] = all(img is not None for img in [work_img, tool_img, chip_img])
        
        return x, y, z, work_img, tool_img, chip_img, metadata
        
    except Exception as e:
        print(f"Error getting force streams with images: {e}")
        raise

def main():
    """
    Main function to demonstrate the force data extraction
    """
    try:
        # Extract random force data (will use default path)
        data = extract_random_force_data()
        
        # Print some basic statistics
        print("\n--- Data Summary ---")
        print(f"Datapoint Index: {data['metadata']['datapoint_index']}")
        print(f"Sample Count: {data['metadata']['sample_count']}")
        print(f"X-axis range: [{min(data['force_data']['x_axis']):.3f}, {max(data['force_data']['x_axis']):.3f}]")
        print(f"Y-axis range: [{min(data['force_data']['y_axis']):.3f}, {max(data['force_data']['y_axis']):.3f}]")
        print(f"Z-axis range: [{min(data['force_data']['z_axis']):.3f}, {max(data['force_data']['z_axis']):.3f}]")
        
    except Exception as e:
        print(f"Failed to extract force data: {str(e)}")

if __name__ == "__main__":
    main()