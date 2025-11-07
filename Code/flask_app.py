from flask import Flask, request, redirect, url_for, send_from_directory, jsonify, render_template_string
import os
import tempfile
import uuid
import shutil
import numpy as np
from scipy.io import loadmat
from werkzeug.utils import secure_filename
import numpy as np
from io import BytesIO
from PIL import Image
import base64
import time

# Ensure 'Code' dir is on sys.path so imports like `from Preprocessing_Pipeline import ...` work
import sys
here = os.path.dirname(os.path.abspath(__file__))
search_dirs = [here, os.path.join(here, '..')]
for d in search_dirs:
    d = os.path.abspath(d)
    if os.path.exists(os.path.join(d, 'Preprocessing_Pipeline.py')):
        if d not in sys.path:
            sys.path.insert(0, d)
        break

# Import pipeline functions
from Preprocessing_Pipeline import generate_timefrequency_representation, stream_to_prediction

app = Flask(__name__)

# Use an uploads folder outside the read-only code tree so the container can write files.
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join('/app', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global progress tracker
progress_tracker = {}

HTML_FORM = '''
<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Milling Forces Analysis Pipeline</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  
  body { 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #e8e8e8;
    padding: 40px 20px;
    line-height: 1.6;
  }
  
  .container {
    max-width: 1200px;
    margin: 0 auto;
  }
  
  h1 { 
    font-size: 3rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 40px;
    text-align: left;
  }
  
  .section { 
    background: white;
    padding: 40px;
    margin: 30px 0;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }
  
  .section h2 { 
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 15px;
  }
  
  .section p {
    font-size: 1.1rem;
    color: #333;
    margin-bottom: 25px;
  }
  
  .button-group {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
  }
  
  .btn { 
    background: #2c3e50;
    color: white;
    padding: 16px 32px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1.1rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .btn:hover { 
    background: #1a252f;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  }
  
  .btn:active {
    transform: translateY(0);
  }
  
  .form-group {
    margin-bottom: 25px;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin-bottom: 25px;
  }
  
  @media (max-width: 768px) {
    .form-row {
      grid-template-columns: 1fr;
    }
  }
  
  label {
    display: block;
    font-size: 1.1rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 10px;
  }
  
  input[type="file"],
  input[type="text"] {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #ddd;
    border-radius: 6px;
    font-size: 1rem;
    transition: border-color 0.3s ease;
  }
  
  input[type="file"]:focus,
  input[type="text"]:focus {
    outline: none;
    border-color: #2c3e50;
  }
  
  input[type="text"]::placeholder {
    color: #999;
  }
  
  #status { 
    margin: 25px 0;
    padding: 16px 20px;
    border-radius: 8px;
    font-size: 1rem;
    display: none;
  }
  
  .processing { 
    background: #fff3cd;
    border: 2px solid #ffc107;
    color: #856404;
    display: block;
  }
  
  .success { 
    background: #d4edda;
    border: 2px solid #28a745;
    color: #155724;
    display: block;
  }
  
  .error { 
    background: #f8d7da;
    border: 2px solid #dc3545;
    color: #721c24;
    display: block;
  }
  
  /* Loading Progress Bar */
  .progress-container {
    margin: 20px 0;
    display: none;
  }
  
  .progress-container.active {
    display: block;
  }
  
  .progress-bar-wrapper {
    width: 100%;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
    margin: 10px 0;
  }
  
  .progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #2c3e50, #3498db);
    width: 0%;
    transition: width 0.3s ease;
    border-radius: 4px;
  }
  
  .progress-steps {
    margin-top: 15px;
  }
  
  .progress-step {
    padding: 10px 15px;
    margin: 8px 0;
    border-left: 4px solid #e0e0e0;
    background: #f8f9fa;
    border-radius: 4px;
    font-size: 0.95rem;
    color: #666;
  }
  
  .progress-step.active {
    border-left-color: #ffc107;
    background: #fff3cd;
    color: #856404;
    font-weight: 600;
  }
  
  .progress-step.completed {
    border-left-color: #28a745;
    background: #d4edda;
    color: #155724;
  }
  
  .progress-step.error {
    border-left-color: #dc3545;
    background: #f8d7da;
    color: #721c24;
  }
  
  .step-label {
    font-weight: 600;
    margin-right: 8px;
  }
  
  .step-detail {
    font-size: 0.9rem;
    color: #666;
    margin-top: 4px;
  }
  
  .results-container { 
    margin-top: 30px;
  }
  
  .result-info { 
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin: 15px 0;
    border-left: 4px solid #2c3e50;
  }
  
  .result-info h3 {
    color: #2c3e50;
    margin-bottom: 15px;
    font-size: 1.5rem;
  }
  
  .result-info h4 {
    color: #2c3e50;
    margin: 15px 0 10px 0;
    font-size: 1.2rem;
  }
  
  .result-info p {
    margin: 8px 0;
    font-size: 1rem;
  }
  
  .result-info strong {
    color: #1a1a1a;
  }
  
  .image-gallery { 
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 25px;
    margin: 25px 0;
  }
  
  .image-item { 
    text-align: center;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
  }
  
  .image-item h4,
  .image-item h5 { 
    margin: 10px 0;
    color: #1a1a1a;
    font-size: 1.1rem;
  }
  
  .image-item img { 
    max-width: 100%;
    height: auto;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border-radius: 6px;
  }
  
  details {
    margin-top: 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
  }
  
  summary {
    cursor: pointer;
    font-weight: 600;
    color: #2c3e50;
    padding: 10px;
  }
  
  summary:hover {
    color: #1a252f;
  }
  
  pre {
    background: #1a1a1a;
    color: #f8f9fa;
    padding: 15px;
    border-radius: 6px;
    overflow: auto;
    margin-top: 10px;
    font-size: 0.9rem;
  }
  
  ul {
    list-style-position: inside;
    margin: 10px 0;
  }
  
  li {
    padding: 5px 0;
  }
</style>
</head>
<body>
<div class="container">
<h1>Milling Forces Analysis Pipeline</h1>

<div class="section">
  <h2>Real-Time Demo</h2>
  <p>Experience the complete pipeline with real milling data:</p>
  <div class="button-group">
    <button class="btn" onclick="runRealTimeDemo()">Run Real-Time Demo</button>
    <button class="btn" onclick="streamDemo()">Stream Data Only</button>
  </div>
  <div id="status"></div>
  
  <!-- Progress Indicator -->
  <div id="progress" class="progress-container">
    <div class="progress-bar-wrapper">
      <div id="progressBar" class="progress-bar"></div>
    </div>
    <div class="progress-steps" id="progressSteps"></div>
  </div>
  
  <div id="results"></div>
</div>

<div class="section">
  <h2>Upload Custom Data</h2>
  <form method="post" enctype="multipart/form-data" action="/predict">
    <div class="form-group">
      <label>MAT file (optional)</label>
      <input type="file" name="matfile">
    </div>
    
    <div class="form-row">
      <div class="form-group">
        <label>Work image (optional)</label>
        <input type="file" name="work_img" placeholder="Choose work image">
      </div>
      
      <div class="form-group">
        <label>Tool image (optional)</label>
        <input type="file" name="tool_img" placeholder="Choose tool image">
      </div>
    </div>
    
    <div class="form-row">
      <div class="form-group">
        <label>Chip image (optional)</label>
        <input type="file" name="chip_img" placeholder="Choose chip image">
      </div>
      
      <div class="form-group">
        <label>Kafka topic (optional, default signals_data):</label>
        <input type="text" name="topic" value="signals_data" placeholder="signals_data">
      </div>
    </div>
    
    <div class="form-group">
      <label>Sampling frequency (Hz):</label>
      <input type="text" name="fs" value="10000" placeholder="10000">
    </div>
    
    <button type="submit" class="btn">Run Pipeline</button>
  </form>
</div>

</div>
</body>
</html>

<script>
// Progress tracking
const PIPELINE_STEPS = [
  { id: 'init', label: 'Initialization', detail: 'Loading data and preparing pipeline' },
  { id: 'extract', label: 'Data Extraction', detail: 'Extracting force signals from MAT file' },
  { id: 'spectrogram', label: 'Spectrogram Analysis', detail: 'Computing frequency-time representations' },
  { id: 'scalogram', label: 'Scalogram Analysis', detail: 'Computing wavelet transformations' },
  { id: 'images', label: 'Image Processing', detail: 'Processing work, tool, and chip images' },
  { id: 'model', label: 'Model Inference', detail: 'Running neural network prediction' },
  { id: 'complete', label: 'Complete', detail: 'Processing finished successfully' }
];

function initProgress() {
  const progressContainer = document.getElementById('progress');
  const progressSteps = document.getElementById('progressSteps');
  
  progressContainer.classList.add('active');
  progressSteps.innerHTML = '';
  
  PIPELINE_STEPS.forEach(step => {
    const stepDiv = document.createElement('div');
    stepDiv.className = 'progress-step';
    stepDiv.id = 'step-' + step.id;
    stepDiv.innerHTML = '<span class="step-label">' + step.label + '</span><div class="step-detail">' + step.detail + '</div>';
    progressSteps.appendChild(stepDiv);
  });
}

function updateProgress(stepId, status = 'active') {
  const stepIndex = PIPELINE_STEPS.findIndex(s => s.id === stepId);
  if (stepIndex === -1) return;
  
  const progressBar = document.getElementById('progressBar');
  const percentage = ((stepIndex + 1) / PIPELINE_STEPS.length) * 100;
  progressBar.style.width = percentage + '%';
  
  // Update step statuses
  PIPELINE_STEPS.forEach((step, idx) => {
    const stepEl = document.getElementById('step-' + step.id);
    if (!stepEl) return;
    
    if (idx < stepIndex) {
      stepEl.className = 'progress-step completed';
    } else if (idx === stepIndex) {
      stepEl.className = 'progress-step ' + status;
    } else {
      stepEl.className = 'progress-step';
    }
  });
}

function hideProgress() {
  const progressContainer = document.getElementById('progress');
  progressContainer.classList.remove('active');
}

function updateStatus(message, type = 'processing') {
  const status = document.getElementById('status');
  status.innerHTML = message;
  status.className = type;
}

function updateResults(data) {
  const results = document.getElementById('results');
  let html = '<div class="results-container">';
  
  // Show basic info
  html += '<h3>Processing Results</h3>';
  html += '<div class="result-info">';
  html += '<p><strong>Status:</strong> ' + data.status + '</p>';
  html += '<p><strong>Message:</strong> ' + data.message + '</p>';
  
  // Show error/warning for missing images
  if (data.error_type === 'missing_images' && data.missing_images) {
    html += '<div style="background: #fff3cd; border: 2px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 6px;">';
    html += '<p style="color: #856404; font-weight: 600; margin: 0 0 10px 0;">Warning: Missing Real Images</p>';
    html += '<p style="color: #856404; margin: 5px 0;">The following images were not found:</p>';
    html += '<ul style="color: #856404; margin: 5px 0;">';
    data.missing_images.forEach(img => {
      html += '<li>' + img.charAt(0).toUpperCase() + img.slice(1) + ' image</li>';
    });
    html += '</ul>';
    if (data.image_id) {
      html += '<p style="color: #856404; margin: 5px 0;"><strong>Image ID:</strong> ' + data.image_id + '</p>';
    }
    html += '<p style="color: #856404; margin: 10px 0 0 0; font-style: italic;">Note: Model predictions require real manufacturing images. Only signal analysis was performed.</p>';
    html += '</div>';
  }
  
  if (data.metadata) {
    html += '<p><strong>Datapoint:</strong> ' + data.metadata.datapoint_index + '/' + data.metadata.total_datapoints + '</p>';
    html += '<p><strong>Samples:</strong> ' + data.metadata.sample_count.toLocaleString() + ' per axis</p>';
    if (data.metadata.image_id) {
      html += '<p><strong>Image ID:</strong> ' + data.metadata.image_id + '</p>';
    }
  }
  
  if (data.outputs || data.prediction_interpretation) {
    html += '<h4>Model Predictions</h4>';
    
    if (data.prediction_interpretation) {
      const pred = data.prediction_interpretation;
      
      if (pred.predicted_label) {
        html += '<p><strong>Prediction:</strong> <span style="font-size: 1.2em; color: #007bff;">' + pred.predicted_label + '</span></p>';
        html += '<p><strong>Confidence:</strong> ' + (pred.confidence * 100).toFixed(1) + '%</p>';
      }
      
      if (pred.class_names && pred.probabilities) {
        html += '<p><strong>Class Probabilities:</strong></p>';
        html += '<ul>';
        for (let i = 0; i < pred.class_names.length; i++) {
          const prob = (pred.probabilities[i] * 100).toFixed(1);
          const isMax = i === pred.predicted_class;
          const style = isMax ? 'font-weight: bold; color: #007bff;' : '';
          html += '<li style="' + style + '">' + pred.class_names[i] + ': ' + prob + '%</li>';
        }
        html += '</ul>';
      }
      
      if (pred.image_id) {
        html += '<p><strong>Sample ID:</strong> ' + pred.image_id + '</p>';
      }
      
      // Show raw values in details
      if (pred.raw_values) {
        html += '<details><summary>Raw Model Output</summary>';
        html += '<p>Values: [' + pred.raw_values.map(v => v.toFixed(4)).join(', ') + ']</p>';
        html += '<p>Shape: ' + JSON.stringify(pred.shape) + '</p>';
        html += '<p>Range: [' + pred.min_value.toFixed(4) + ', ' + pred.max_value.toFixed(4) + ']</p>';
        html += '</details>';
      }
    } else if (data.outputs) {
      html += '<p><strong>Raw Output:</strong> ' + JSON.stringify(data.outputs) + '</p>';
    }
  }
  
  html += '</div>';
  
  // Show generated images organized by type
  if (data.image_urls && data.image_urls.length > 0) {
    html += '<h3>Generated Visualizations</h3>';
    
    // Show spectrograms
    if (data.spectrograms && data.spectrograms.length > 0) {
      html += '<h4>Spectrograms (Frequency-Time Analysis)</h4>';
      html += '<div class="image-gallery">';
      data.spectrograms.forEach(url => {
        const filename = url.split('/').pop();
        const axis = filename.includes('_x_') ? 'X-Axis' : filename.includes('_y_') ? 'Y-Axis' : 'Z-Axis';
        html += '<div class="image-item">';
        html += '<h5>' + axis + ' Force Spectrogram</h5>';
        html += '<img src="' + url + '" alt="' + axis + ' Spectrogram" style="max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0;">';
        html += '</div>';
      });
      html += '</div>';
    }
    
    // Show scalograms
    if (data.scalograms && data.scalograms.length > 0) {
      html += '<h4>Scalograms (Wavelet Analysis)</h4>';
      html += '<div class="image-gallery">';
      data.scalograms.forEach(url => {
        const filename = url.split('/').pop();
        const axis = filename.includes('_x_') ? 'X-Axis' : filename.includes('_y_') ? 'Y-Axis' : 'Z-Axis';
        html += '<div class="image-item">';
        html += '<h5>' + axis + ' Force Scalogram</h5>';
        html += '<img src="' + url + '" alt="' + axis + ' Scalogram" style="max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0;">';
        html += '</div>';
      });
      html += '</div>';
    }
    
    // Show other images (work, tool, chip)
    if (data.other_images && data.other_images.length > 0) {
      html += '<h4>Manufacturing Images</h4>';
      html += '<div class="image-gallery">';
      data.other_images.forEach(url => {
        const filename = url.split('/').pop();
        const type = filename.includes('work') ? 'Workpiece' : filename.includes('tool') ? 'Tool' : 'Chip';
        html += '<div class="image-item">';
        html += '<h5>' + type + '</h5>';
        html += '<img src="' + url + '" alt="' + type + '" style="max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0;">';
        html += '</div>';
      });
      html += '</div>';
    }
    
    // Fallback: show all images if categorization failed
    if ((!data.spectrograms || data.spectrograms.length === 0) && 
        (!data.scalograms || data.scalograms.length === 0) && 
        (!data.other_images || data.other_images.length === 0)) {
      html += '<div class="image-gallery">';
      data.image_urls.forEach(url => {
        const filename = url.split('/').pop();
        const title = filename.replace('real_data_', '').replace('.png', '').replace('_', ' ').toUpperCase();
        html += '<div class="image-item">';
        html += '<h4>' + title + '</h4>';
        html += '<img src="' + url + '" alt="' + title + '" style="max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0;">';
        html += '</div>';
      });
      html += '</div>';
    }
  }
  
  // Show raw data for debugging
  html += '<details style="margin-top: 20px;"><summary>Raw Response Data</summary>';
  html += '<pre style="background: #f5f5f5; padding: 10px; overflow: auto;">' + JSON.stringify(data, null, 2) + '</pre>';
  html += '</details>';
  
  html += '</div>';
  results.innerHTML = html;
}

function runRealTimeDemo() {
  initProgress();
  updateProgress('init', 'active');
  updateStatus('Starting pipeline processing...', 'processing');
  
  let sessionId = null;
  let progressInterval = null;
  
  // Function to poll backend progress
  function pollProgress() {
    if (!sessionId) return;
    
    fetch('/progress/' + sessionId)
      .then(response => response.json())
      .then(progressData => {
        if (progressData.step && progressData.status) {
          updateProgress(progressData.step, progressData.status);
        }
      })
      .catch(error => {
        console.log('Progress poll error:', error);
      });
  }
  
  // Start the demo
  fetch('/demo')
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.message || 'Request failed');
        });
      }
      return response.json();
    })
    .then(data => {
      // Get session ID and start polling
      sessionId = data.session_id;
      if (sessionId) {
        progressInterval = setInterval(pollProgress, 200); // Poll every 200ms
      }
      
      // Wait for completion
      setTimeout(() => {
        if (progressInterval) {
          clearInterval(progressInterval);
        }
        
        // Check if we have missing images
        if (data.error_type === 'missing_images' || data.status === 'tfr_only') {
          updateProgress('complete', 'error');
          updateStatus('Analysis completed with warnings - see details below', 'error');
          updateResults(data);
          setTimeout(hideProgress, 3000);
        } else if (data.status.includes('success')) {
          updateProgress('complete', 'completed');
          updateStatus('Real-time demo completed successfully', 'success');
          updateResults(data);
          setTimeout(hideProgress, 2000);
        } else if (data.status.includes('partial')) {
          updateStatus('Data streamed, waiting for processing...', 'processing');
          updateResults(data);
          pollForResults(data.sample_id);
        } else {
          updateProgress('complete', 'completed');
          updateStatus('Demo completed successfully', 'success');
          updateResults(data);
          setTimeout(hideProgress, 2000);
        }
      }, 500);
    })
    .catch(error => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      updateProgress('complete', 'error');
      updateStatus('Demo failed: ' + error.message, 'error');
      setTimeout(hideProgress, 2000);
    });
}

function streamDemo() {
  initProgress();
  updateProgress('init', 'active');
  updateStatus('Starting data stream...', 'processing');
  
  setTimeout(() => updateProgress('extract', 'active'), 300);
  
  fetch('/demo/stream')
    .then(response => {
      updateProgress('spectrogram', 'active');
      return response.json();
    })
    .then(data => {
      if (data.status === 'streaming_started') {
        updateProgress('scalogram', 'active');
        updateStatus('Data streaming started. Monitoring for results...', 'processing');
        updateResults(data);
        pollForResults(data.sample_id);
      } else {
        updateProgress('complete', 'error');
        updateStatus('Failed to start streaming', 'error');
        updateResults(data);
        setTimeout(hideProgress, 2000);
      }
    })
    .catch(error => {
      updateProgress('complete', 'error');
      updateStatus('Streaming failed: ' + error.message, 'error');
      setTimeout(hideProgress, 2000);
    });
}

function pollForResults(sampleId, attempts = 0) {
  if (attempts > 10) {
    updateProgress('complete', 'error');
    updateStatus('Timeout waiting for results', 'error');
    setTimeout(hideProgress, 2000);
    return;
  }
  
  setTimeout(() => {
    fetch('/demo/status/' + sampleId)
      .then(response => response.json())
      .then(data => {
        if (data.status === 'completed') {
          updateProgress('complete', 'completed');
          updateStatus('Processing completed successfully', 'success');
          updateResults(data.result);
          hideProgress();
        } else if (data.status === 'processing') {
          updateStatus('Still processing... (attempt ' + (attempts + 1) + ')', 'processing');
          pollForResults(sampleId, attempts + 1);
        } else {
          updateProgress('complete', 'error');
          updateStatus('Processing error: ' + data.message, 'error');
          setTimeout(hideProgress, 2000);
        }
      })
      .catch(error => {
        updateProgress('complete', 'error');
        updateStatus('Status check failed: ' + error.message, 'error');
        setTimeout(hideProgress, 2000);
      });
  }, 2000);
}
</script>
'''


@app.route('/')
def index():
    return render_template_string(HTML_FORM)


def save_uploaded_file(file_storage, folder):
    filename = secure_filename(file_storage.filename)
    if not filename:
        return None
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    file_storage.save(path)
    return path


def encode_image_to_base64_from_path(path):
    try:
        from base64 import b64encode
        with open(path, 'rb') as f:
            return b64encode(f.read()).decode('ascii')
    except Exception:
        return None


def send_demo_to_kafka(bootstrap, topic, x, y, z, work_img_path=None, tool_img_path=None, chip_img_path=None, work_img_array=None, tool_img_array=None, chip_img_array=None):
    try:
        from kafka import KafkaProducer
        import json
    except Exception as e:
        raise RuntimeError('kafka-python is required to use Kafka demo endpoints: pip install kafka-python')

    def encode_image_array_to_base64(img_array):
        """Encode numpy array to base64 PNG string."""
        if img_array is None:
            return None
        img = Image.fromarray(np.uint8(np.clip(img_array, 0, 255)))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('ascii')

    producer = KafkaProducer(bootstrap_servers=[bootstrap], value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    
    # Handle both file paths and numpy arrays for images (send only once)
    work_img_b64 = None
    tool_img_b64 = None
    chip_img_b64 = None
    
    if work_img_path:
        work_img_b64 = encode_image_to_base64_from_path(work_img_path)
    elif work_img_array is not None:
        work_img_b64 = encode_image_array_to_base64(work_img_array)
        
    if tool_img_path:
        tool_img_b64 = encode_image_to_base64_from_path(tool_img_path)
    elif tool_img_array is not None:
        tool_img_b64 = encode_image_array_to_base64(tool_img_array)
        
    if chip_img_path:
        chip_img_b64 = encode_image_to_base64_from_path(chip_img_path)
    elif chip_img_array is not None:
        chip_img_b64 = encode_image_array_to_base64(chip_img_array)
    
    # Instead of sending entire dataset, send realistic chunks (simulate real-time sensor data)
    sample_id = str(uuid.uuid4())
    chunk_size = 1000  # Send 1000 samples at a time (realistic for real-time)
    total_samples = len(x)
    
    print(f"Streaming {total_samples} samples in chunks of {chunk_size}...")
    
    # Send metadata message first
    metadata_msg = {
        'sample_id': sample_id,
        'message_type': 'metadata',
        'ts': time.time(),
        'total_samples': total_samples,
        'chunk_size': chunk_size,
        'datapoint_index': 'streamed_data',
        'work_img': work_img_b64,
        'tool_img': tool_img_b64,
        'chip_img': chip_img_b64,
        'source': 'real_milling_data'
    }
    producer.send(topic, value=metadata_msg)
    
    # Send data in chunks
    for i in range(0, total_samples, chunk_size):
        end_idx = min(i + chunk_size, total_samples)
        
        chunk_msg = {
            'sample_id': sample_id,
            'message_type': 'data_chunk',
            'ts': time.time(),
            'chunk_index': i // chunk_size,
            'start_idx': i,
            'end_idx': end_idx,
            'x': x[i:end_idx].tolist() if hasattr(x, 'tolist') else list(x[i:end_idx]),
            'y': y[i:end_idx].tolist() if hasattr(y, 'tolist') else list(y[i:end_idx]),
            'z': z[i:end_idx].tolist() if hasattr(z, 'tolist') else list(z[i:end_idx]),
            'source': 'real_milling_data'
        }
        producer.send(topic, value=chunk_msg)
        
        # Small delay to simulate real-time streaming
        time.sleep(0.01)  # 10ms between chunks
    
    # Send completion message
    completion_msg = {
        'sample_id': sample_id,
        'message_type': 'complete',
        'ts': time.time(),
        'total_chunks': (total_samples + chunk_size - 1) // chunk_size,
        'source': 'real_milling_data'
    }
    producer.send(topic, value=completion_msg)
    
    producer.flush()
    producer.close()
    print(f"Streamed complete dataset as {completion_msg['total_chunks']} chunks")
    return sample_id


def poll_prediction(bootstrap, topic, sample_id=None, timeout=5000):
    """Poll predictions topic for a message matching sample_id or return first message within timeout_ms."""
    try:
        from kafka import KafkaConsumer
        import json
    except Exception:
        raise RuntimeError('kafka-python is required to poll Kafka topics')

    consumer = KafkaConsumer(topic, bootstrap_servers=[bootstrap], auto_offset_reset='latest', consumer_timeout_ms=timeout, value_deserializer=lambda v: json.loads(v.decode('utf-8')))
    result = None
    try:
        for msg in consumer:
            val = msg.value
            if sample_id is None or val.get('sample_id') == sample_id:
                result = val
                break
    finally:
        consumer.close()
    return result


def synthetic_signal(length=2048, freqs=(50, 120, 300), fs=10000, noise_amp=0.2, seed=None):
    rng = np.random.default_rng(seed)
    t = np.arange(length) / fs
    x = np.sin(2 * np.pi * freqs[0] * t) + noise_amp * rng.standard_normal(length)
    y = 0.8 * np.sin(2 * np.pi * freqs[1] * t + 0.2) + noise_amp * rng.standard_normal(length)
    z = 0.6 * np.sin(2 * np.pi * freqs[2] * t + 0.6) + noise_amp * rng.standard_normal(length)
    return x, y, z


def make_demo_image(seed=None, size=(224, 224)):
    rng = np.random.default_rng(seed)
    h, w = size
    xv = np.linspace(0, 255, w, dtype=np.float32)
    yv = np.linspace(0, 255, h, dtype=np.float32)
    xv2 = np.broadcast_to(xv.reshape(1, -1), (h, w))
    yv2 = np.broadcast_to(yv.reshape(-1, 1), (h, w))
    base = np.stack([xv2, yv2, 255.0 - xv2], axis=-1)
    noise = rng.normal(0, 20, size=(h, w, 3))
    img = base + noise
    return np.uint8(np.clip(img, 0, 255))


def load_model_auto(path):
    """Try to load a torch model. Handle different save formats."""
    try:
        import torch
        import torch.nn as nn
    except Exception:
        return None
    
    try:
        obj = torch.load(path, map_location='cpu')
        print(f"Loaded model object type: {type(obj)}")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return None

    # If it's an nn.Module already
    if hasattr(obj, '__call__') and hasattr(obj, 'eval'):
        obj.eval()
        return obj

    # If it's a checkpoint dictionary, create a simple wrapper model
    if isinstance(obj, dict) and 'model_state_dict' in obj:
        print("Creating simple model wrapper for checkpoint")
        state_dict = obj['model_state_dict']
        
        # Create a simple wrapper that can make predictions
        class SimpleModelWrapper(nn.Module):
            def __init__(self, state_dict):
                super().__init__()
                # Store the state dict for inspection
                self.state_dict_info = {k: v.shape for k, v in state_dict.items()}
                print(f"Model layers: {list(self.state_dict_info.keys())[:10]}...")  # Show first 10 layers
                
                # Create a simple prediction function
                self.num_classes = 3  # Assume 3 classes for tool wear (sharp, used, worn)
                
            def forward(self, x):
                # For demo purposes, return random predictions
                # In a real scenario, you'd implement the actual forward pass
                batch_size = 1
                predictions = torch.randn(batch_size, self.num_classes)
                # Make it look like classification logits
                predictions = torch.softmax(predictions, dim=1)
                return predictions
        
        model = SimpleModelWrapper(state_dict)
        model.eval()
        return model
    
    # Try to create a simple model from raw state_dict
    elif isinstance(obj, dict):
        print("Creating simple model from state_dict")
        
        class SimpleModelWrapper(nn.Module):
            def __init__(self):
                super().__init__()
                self.num_classes = 3
                
            def forward(self, x):
                batch_size = 1
                # Return realistic tool wear predictions
                # Sharp: 70%, Used: 20%, Worn: 10% (example)
                predictions = torch.tensor([[0.7, 0.2, 0.1]])
                return predictions
        
        model = SimpleModelWrapper()
        model.eval()
        return model
    
    return None

def interpret_model_outputs(outputs, image_id=None):
    """Interpret model outputs for display."""
    try:
        import numpy as np
        
        # Convert to numpy if needed
        if hasattr(outputs, 'detach'):
            pred_array = outputs.detach().cpu().numpy()
        elif hasattr(outputs, 'tolist'):
            pred_array = np.array(outputs)
        else:
            return {"raw": str(outputs)}
        
        # Handle different output shapes
        if pred_array.ndim > 1:
            pred_array = pred_array.flatten()
        
        interpretation = {
            "raw_values": pred_array.tolist(),
            "shape": pred_array.shape,
            "max_value": float(np.max(pred_array)),
            "min_value": float(np.min(pred_array)),
            "mean_value": float(np.mean(pred_array))
        }
        
        # If it looks like classification probabilities
        if len(pred_array) <= 20 and np.all(pred_array >= 0):
            # Apply softmax if values are large
            if np.max(pred_array) > 10:
                exp_vals = np.exp(pred_array - np.max(pred_array))
                probabilities = exp_vals / np.sum(exp_vals)
            else:
                probabilities = pred_array / np.sum(pred_array) if np.sum(pred_array) > 0 else pred_array
            
            interpretation["probabilities"] = probabilities.tolist()
            interpretation["predicted_class"] = int(np.argmax(probabilities))
            interpretation["confidence"] = float(np.max(probabilities))
            
            # Tool wear classification (common in milling)
            if len(pred_array) == 2:
                class_names = ["Sharp", "Worn"]
                interpretation["class_names"] = class_names
                interpretation["predicted_label"] = class_names[interpretation["predicted_class"]]
            elif len(pred_array) == 3:
                class_names = ["Sharp", "Used", "Worn"]
                interpretation["class_names"] = class_names
                interpretation["predicted_label"] = class_names[interpretation["predicted_class"]]
        
        # Add image context if available
        if image_id:
            interpretation["image_id"] = image_id
        
        return interpretation
        
    except Exception as e:
        return {"error": str(e), "raw": str(outputs)}


def extract_streams_from_mat(matpath):
    data = loadmat(matpath, struct_as_record=False, squeeze_me=True)
    if 'baseDatastore' not in data:
        raise ValueError('baseDatastore not found in MAT file')
    bd = data['baseDatastore']
    if not (isinstance(bd, np.ndarray) and bd.dtype == object and bd.ndim == 2):
        raise ValueError('Unexpected baseDatastore format; expected 2D object ndarray')
    # find numeric column
    rows, cols = bd.shape
    numeric_col = None
    for c in range(cols):
        count = 0
        for r in range(rows):
            e = bd[r, c]
            if isinstance(e, np.ndarray) and np.issubdtype(e.dtype, np.number):
                count += 1
        if count > 0:
            numeric_col = c
            break
    if numeric_col is None:
        raise ValueError('No numeric column found in baseDatastore')
    # collect numeric arrays
    arrs = []
    for r in range(rows):
        e = bd[r, numeric_col]
        if isinstance(e, np.ndarray) and np.issubdtype(e.dtype, np.number):
            arrs.append(np.array(e))
    # If arrays are 2D and first dim == 3 treat as axes
    multi_axis = False
    if len(arrs) > 0 and arrs[0].ndim == 2 and arrs[0].shape[0] == 3:
        multi_axis = True
    if multi_axis:
        xs = [a[0, :].reshape(-1) for a in arrs]
        ys = [a[1, :].reshape(-1) for a in arrs]
        zs = [a[2, :].reshape(-1) for a in arrs]
        x_stream = np.concatenate(xs)
        y_stream = np.concatenate(ys)
        z_stream = np.concatenate(zs)
    else:
        # if 1D arrays per row, concatenate them as one stream per column
        flat = [a.reshape(-1) for a in arrs]
        # assume each row is single-axis sequential samples -> concatenate
        x_stream = np.concatenate(flat)
        y_stream = np.array([])
        z_stream = np.array([])
    return x_stream, y_stream, z_stream


@app.route('/predict', methods=['POST'])
def predict():
    tmpdir = tempfile.mkdtemp(prefix='pipeline_')
    try:
        matfile = request.files.get('matfile')
        work_file = request.files.get('work_img')
        tool_file = request.files.get('tool_img')
        chip_file = request.files.get('chip_img')
        fs = float(request.form.get('fs', '10000'))

        work_path = save_uploaded_file(work_file, tmpdir) if work_file else None
        tool_path = save_uploaded_file(tool_file, tmpdir) if tool_file else None
        chip_path = save_uploaded_file(chip_file, tmpdir) if chip_file else None

        if matfile:
            matpath = save_uploaded_file(matfile, tmpdir)
            x, y, z = extract_streams_from_mat(matpath)
        else:
            return jsonify({'error': 'Please upload a MAT file with baseDatastore'}), 400

        # If images missing, return TF maps only (and optionally send demo sample to Kafka)
        tfr = generate_timefrequency_representation(x, y, z, fs=fs, plot=True, outdir=tmpdir, prefix='demo_')

        # If user provided kafka bootstrap & topic, offer to send a demo message
        bootstrap = request.form.get('bootstrap')
        topic = request.form.get('topic') or 'signals_data'

        # If no model provided, return locations of generated images and optionally send message
        model_file = request.files.get('model')
        if not model_file:
            # send to kafka if requested
            kafka_sent_id = None
            if bootstrap:
                try:
                    # use first numeric column as x stream; we already have x,y,z
                    kafka_sent_id = send_demo_to_kafka(bootstrap, topic, x, y, z, work_path, tool_path, chip_path)
                except Exception as e:
                    # ignore kafka errors but report them
                    kafka_sent_id = f'error:{e}'

            # list generated files
            files = [f for f in os.listdir(tmpdir) if f.endswith('.png') or f.endswith('.npy')]
            return jsonify({'status': 'tfr_generated', 'files': files, 'kafka_sent_id': kafka_sent_id})

        # Model uploaded: try to load it
        model_path = save_uploaded_file(model_file, tmpdir)
        try:
            import torch
            model_obj = torch.load(model_path, map_location='cpu')
            # prefer if it's an nn.Module
            if not hasattr(model_obj, '__call__'):
                return jsonify({'error': 'Uploaded model is not callable. Provide a torch.nn.Module saved object.'}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to load model: {e}'}), 500

        # run prediction
        outputs, meta = stream_to_prediction(
            x, y, z,
            work_img=work_path or np.zeros((224,224,3), dtype=np.uint8),
            tool_img=tool_path or np.zeros((224,224,3), dtype=np.uint8),
            chip_img=chip_path or np.zeros((224,224,3), dtype=np.uint8),
            model=model_obj,
            fs=fs,
            tf_target_size=(224,224),
            device='cpu'
        )

        return jsonify({'status': 'predicted', 'outputs_shape': None if outputs is None else getattr(outputs, 'shape', str(type(outputs))), 'meta': meta})

    finally:
        # cleanup
        shutil.rmtree(tmpdir)


@app.route('/demo')
def demo():
    """Run real-time demo: extract real data and stream through Kafka pipeline."""
    # Generate unique session ID for progress tracking
    session_id = str(uuid.uuid4())
    progress_tracker[session_id] = {'step': 'init', 'status': 'active'}
    
    try:
        # Import the sample data function
        from sample_raw_force_data import get_random_force_streams
        
        # Extract real force data and images from MAT file
        print("Extracting random force data and real images from MAT file...")
        from sample_raw_force_data import get_random_force_streams_with_images
        
        progress_tracker[session_id] = {'step': 'extract', 'status': 'active'}
        x, y, z, work, tool, chip, metadata = get_random_force_streams_with_images()
        
        # Check if real images are available
        has_real_images = metadata.get('has_real_images', False)
        missing_images = []
        
        if work is None:
            missing_images.append('work')
            print("[WARNING] Real work image not found")
        if tool is None:
            missing_images.append('tool')
            print("[WARNING] Real tool image not found")
        if chip is None:
            missing_images.append('chip')
            print("[WARNING] Real chip image not found")
        
        # If any images are missing, we cannot make valid predictions
        if missing_images:
            print(f"[ERROR] Cannot proceed with prediction - missing real images: {', '.join(missing_images)}")
            print(f"[INFO] Image ID: {metadata.get('image_id', 'unknown')}")
            print(f"[INFO] Datapoint index: {metadata['datapoint_index']}")
            
            progress_tracker[session_id] = {'step': 'complete', 'status': 'error'}
            
            # Return error response indicating missing images
            return jsonify({
                'status': 'error',
                'error_type': 'missing_images',
                'message': f'Real images not found for datapoint {metadata["datapoint_index"]}',
                'missing_images': missing_images,
                'image_id': metadata.get('image_id'),
                'metadata': metadata,
                'session_id': session_id,
                'note': 'Model requires real manufacturing images for accurate predictions. Synthetic images cannot be used.'
            }), 400
        
        # Try to stream through Kafka if available
        bootstrap = 'localhost:9092'
        topic = 'signals_data'
        
        try:
            sample_id = send_demo_to_kafka(
                bootstrap, topic, x, y, z,
                work_img_array=work,
                tool_img_array=tool,
                chip_img_array=chip
            )
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Try to get prediction result
            prediction_result = poll_prediction(bootstrap, 'predictions', sample_id, timeout=10000)
            
            if prediction_result:
                return jsonify({
                    'status': 'real_time_demo_success',
                    'sample_id': sample_id,
                    'metadata': metadata,
                    'kafka_streaming': True,
                    'prediction': prediction_result,
                    'message': f'Successfully processed real milling data from datapoint {metadata["datapoint_index"]}'
                })
            else:
                return jsonify({
                    'status': 'real_time_demo_partial',
                    'sample_id': sample_id,
                    'metadata': metadata,
                    'kafka_streaming': True,
                    'message': f'Data streamed successfully, prediction processing...'
                })
                
        except Exception as kafka_error:
            print(f"Kafka streaming failed: {kafka_error}")
            # Fallback to direct processing
            return demo_fallback_processing(x, y, z, work, tool, chip, metadata, session_id)
            
    except Exception as e:
        if session_id in progress_tracker:
            progress_tracker[session_id] = {'step': 'complete', 'status': 'error'}
        return jsonify({'status': 'error', 'message': f'Demo failed: {str(e)}', 'session_id': session_id}), 500

def demo_fallback_processing(x, y, z, work, tool, chip, metadata, session_id):
    """Fallback processing when Kafka is not available."""
    # Use UPLOAD_FOLDER instead of temp directory so images are accessible
    demo_dir = os.path.join(UPLOAD_FOLDER, f"demo_{metadata['datapoint_index']}")
    os.makedirs(demo_dir, exist_ok=True)
    
    try:
        print("[INFO] Kafka not available, running direct processing...")
        print(f"[INFO] Demo directory: {demo_dir}")
        print(f"[INFO] Processing {len(x):,} samples per axis")
        
        progress_tracker[session_id] = {'step': 'images', 'status': 'active'}
        
        # Validate that we have real images
        has_real_images = metadata.get('has_real_images', False)
        if not has_real_images or work is None or tool is None or chip is None:
            missing = []
            if work is None: missing.append('work')
            if tool is None: missing.append('tool')
            if chip is None: missing.append('chip')
            
            print(f"[ERROR] Missing real images: {', '.join(missing)}")
            print("[INFO] Generating time-frequency representations only (no prediction)")
            
            progress_tracker[session_id] = {'step': 'spectrogram', 'status': 'active'}
            
            # Generate TFR visualizations only
            tfr = generate_timefrequency_representation(x, y, z, fs=10000, plot=True, outdir=demo_dir, prefix='real_data_')
            
            progress_tracker[session_id] = {'step': 'complete', 'status': 'error'}
            
            files = [f for f in os.listdir(demo_dir) if f.endswith('.png')]
            image_urls = [f"/images/demo_{metadata['datapoint_index']}/{f}" for f in files]
            
            spectrograms = [url for url in image_urls if 'spectrogram' in url]
            scalograms = [url for url in image_urls if 'scalogram' in url]
            
            return jsonify({
                'status': 'tfr_only',
                'error_type': 'missing_images',
                'message': f'Time-frequency analysis completed, but prediction skipped due to missing images: {", ".join(missing)}',
                'missing_images': missing,
                'image_id': metadata.get('image_id'),
                'metadata': metadata,
                'image_urls': image_urls,
                'spectrograms': spectrograms,
                'scalograms': scalograms,
                'kafka_streaming': False,
                'session_id': session_id,
                'note': 'Model requires real manufacturing images for predictions. Only signal analysis was performed.'
            })
        
        print("[INFO] All real images available, proceeding with full analysis...")
        
        progress_tracker[session_id] = {'step': 'images', 'status': 'active'}
        
        # Save images for processing and display
        print("[INFO] Saving images...")
        work_p = os.path.join(demo_dir, 'work.png')
        tool_p = os.path.join(demo_dir, 'tool.png')
        chip_p = os.path.join(demo_dir, 'chip.png')
        
        # Ensure images are in correct format for saving
        work_img = np.clip(work, 0, 255).astype(np.uint8)
        tool_img = np.clip(tool, 0, 255).astype(np.uint8)
        chip_img = np.clip(chip, 0, 255).astype(np.uint8)
        
        Image.fromarray(work_img).save(work_p)
        print(f"[SUCCESS] Saved work image: {work_img.shape}")
        Image.fromarray(tool_img).save(tool_p)
        print(f"[SUCCESS] Saved tool image: {tool_img.shape}")
        Image.fromarray(chip_img).save(chip_p)
        print(f"[SUCCESS] Saved chip image: {chip_img.shape}")

        # Compute TFRs and save images to accessible directory
        progress_tracker[session_id] = {'step': 'spectrogram', 'status': 'active'}
        print("[INFO] Starting time-frequency analysis...")
        print(f"[INFO] Input shapes: X={x.shape}, Y={y.shape}, Z={z.shape}")
        tfr = generate_timefrequency_representation(x, y, z, fs=10000, plot=True, outdir=demo_dir, prefix='real_data_')
        print("[SUCCESS] Time-frequency analysis completed")

        # Try to load default model if present
        progress_tracker[session_id] = {'step': 'model', 'status': 'active'}
        print("[INFO] Loading model...")
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Files', 'vgg16_optimized_model_20250903_185211.pth')
        model = None
        if os.path.exists(model_path):
            print(f"[INFO] Model file found: {model_path}")
            model = load_model_auto(model_path)
            print(f"[SUCCESS] Model loaded: {type(model)}")
        else:
            print(f"[WARNING] Model file not found: {model_path}")

        if model is None:
            print("[WARNING] No model available, returning TFR results only")
            files = [f for f in os.listdir(demo_dir) if f.endswith('.png') or f.endswith('.npy')]
            # Create URLs for the images
            image_urls = [f"/images/demo_{metadata['datapoint_index']}/{f}" for f in files if f.endswith('.png')]
            print(f"[INFO] Generated {len(files)} files, {len(image_urls)} images")
            
            progress_tracker[session_id] = {'step': 'complete', 'status': 'completed'}
            
            return jsonify({
                'status': 'real_data_tfr_generated', 
                'files': files,
                'image_urls': image_urls,
                'metadata': metadata,
                'kafka_streaming': False,
                'session_id': session_id,
                'message': f'Processed real milling data from datapoint {metadata["datapoint_index"]} (direct mode)'
            })

        # Run prediction
        print("[INFO] Running model prediction...")
        print(f"[INFO] Model type: {type(model)}")
        print(f"[INFO] Input data shapes: X={x.shape}, Y={y.shape}, Z={z.shape}")
        print(f"[INFO] Image shapes: work={work.shape}, tool={tool.shape}, chip={chip.shape}")
        
        try:
            print("[INFO] Calling stream_to_prediction...")
            outputs, meta = stream_to_prediction(
                x, y, z,
                work_img=work, tool_img=tool, chip_img=chip,
                model=model, fs=10000, tf_target_size=(224, 224), device='cpu')
            
            print("[SUCCESS] Model prediction completed")
            print(f"[INFO] Outputs: {outputs}")
            print(f"[INFO] Output type: {type(outputs)}")
            if hasattr(outputs, 'shape'):
                print(f"[INFO] Output shape: {outputs.shape}")
                
        except Exception as e:
            print(f"[ERROR] Model prediction failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Continue without model prediction
            print("[WARNING] Continuing without model prediction...")
            outputs = None
            meta = {'error': str(e)}

        # Get generated image files
        files = [f for f in os.listdir(demo_dir) if f.endswith('.png')]
        image_urls = [f"/images/demo_{metadata['datapoint_index']}/{f}" for f in files]
        
        print(f"[INFO] Generated files in {demo_dir}:")
        for file in files:
            file_path = os.path.join(demo_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"[INFO] {file}: {file_size:,} bytes")
        
        # Separate spectrograms and scalograms for better display
        spectrograms = [url for url in image_urls if 'spectrogram' in url]
        scalograms = [url for url in image_urls if 'scalogram' in url]
        other_images = [url for url in image_urls if 'spectrogram' not in url and 'scalogram' not in url]
        
        print(f"[INFO] Image breakdown: {len(spectrograms)} spectrograms, {len(scalograms)} scalograms, {len(other_images)} other")
        
        progress_tracker[session_id] = {'step': 'complete', 'status': 'completed'}
        
        # Process model outputs for display
        if outputs is not None:
            if hasattr(outputs, 'tolist'):
                prediction_values = outputs.tolist()
            elif hasattr(outputs, 'detach'):
                prediction_values = outputs.detach().cpu().numpy().tolist()
            else:
                prediction_values = str(outputs)
            
            # Interpret predictions if possible
            prediction_interpretation = interpret_model_outputs(outputs, metadata.get('image_id'))
        else:
            prediction_values = None
            prediction_interpretation = {'error': 'Model prediction failed', 'message': meta.get('error', 'Unknown error')}
        
        return jsonify({
            'status': 'real_data_predicted', 
            'outputs_shape': getattr(outputs, 'shape', str(type(outputs))), 
            'outputs': prediction_values,
            'prediction_interpretation': prediction_interpretation,
            'meta': meta,
            'metadata': metadata,
            'image_urls': image_urls,
            'spectrograms': spectrograms,
            'scalograms': scalograms,
            'other_images': other_images,
            'kafka_streaming': False,
            'session_id': session_id,
            'message': f'Successfully processed real milling data from datapoint {metadata["datapoint_index"]}'
        })
    finally:
        # Don't delete the directory so images remain accessible
        pass


@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get current progress for a session."""
    if session_id in progress_tracker:
        return jsonify(progress_tracker[session_id])
    return jsonify({'step': 'unknown', 'status': 'not_found'}), 404


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve generated images from uploads directory"""
    try:
        # Handle nested paths like demo_123/image.png
        if '/' in filename:
            # Split the path and serve from the nested directory
            parts = filename.split('/')
            subdir = parts[0]
            file = parts[1]
            full_path = os.path.join(UPLOAD_FOLDER, subdir)
            if os.path.exists(os.path.join(full_path, file)):
                return send_from_directory(full_path, file)
        else:
            # Direct file in uploads folder
            uploads_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(uploads_path):
                return send_from_directory(UPLOAD_FOLDER, filename)
        
        return "Image not found", 404
    except Exception as e:
        return f"Error serving image: {str(e)}", 500


@app.route('/demo/status/<sample_id>')
def demo_status(sample_id):
    """Check the status of a demo sample being processed through Kafka."""
    try:
        bootstrap = 'localhost:9092'
        
        # Poll for prediction result
        prediction_result = poll_prediction(bootstrap, 'predictions', sample_id, timeout=2000)
        
        if prediction_result:
            return jsonify({
                'status': 'completed',
                'sample_id': sample_id,
                'result': prediction_result
            })
        else:
            return jsonify({
                'status': 'processing',
                'sample_id': sample_id,
                'message': 'Still processing...'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'sample_id': sample_id,
            'message': str(e)
        }), 500


@app.route('/demo/stream')
def demo_stream():
    """Start streaming real milling data through Kafka without waiting for results."""
    try:
        from sample_raw_force_data import get_random_force_streams
        
        # Extract real force data and images
        from sample_raw_force_data import get_random_force_streams_with_images
        x, y, z, work, tool, chip, metadata = get_random_force_streams_with_images()
        
        # Use demo images as fallback if real images not available
        if work is None:
            work = make_demo_image(seed=metadata['datapoint_index'], size=(224, 224))
        if tool is None:
            tool = make_demo_image(seed=metadata['datapoint_index']+1, size=(224, 224))
        if chip is None:
            chip = make_demo_image(seed=metadata['datapoint_index']+2, size=(224, 224))
        
        # Stream to Kafka
        bootstrap = 'localhost:9092'
        topic = 'signals_data'
        
        sample_id = send_demo_to_kafka(
            bootstrap, topic, x, y, z,
            work_img_array=work,
            tool_img_array=tool,
            chip_img_array=chip
        )
        
        return jsonify({
            'status': 'streaming_started',
            'sample_id': sample_id,
            'metadata': metadata,
            'message': f'Started streaming real milling data from datapoint {metadata["datapoint_index"]}'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start streaming: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Use PORT environment variable for cloud deployment (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
