"""Preprocessing utilities for force-sensor streams.

This module provides a helper to generate spectrograms and scalograms for
three-axis force streams (x, y, z). The main function is
`generate_timefrequency_representation` which accepts numeric 1D arrays for
each axis and returns the computed representations as numpy arrays. The
function can also optionally plot or save the figures.

Example:
	from Preprocessing_Pipeline import generate_timefrequency_representation
	out = generate_timefrequency_representation(x, y, z, fs=10000)

Return structure (dict):
	{
	  'spectrogram': {
		   'x': {'f': freqs, 't': times, 'Sxx_db': Sxx_db},
		   'y': {...},
		   'z': {...}
	  },
	  'scalogram': {
		   'x': {'coef': coef_x, 'freqs': cwt_freqs_x},
		   'y': {...},
		   'z': {...}
	  }
	}

Notes:
- Requires scipy for spectrograms. For scalograms (CWT) pywt is recommended
  (pip install pywt). If pywt is not available, the scalogram entries will be
  None.
"""

from typing import Optional, Tuple, Dict, Any
import numpy as np
from scipy import signal
import os
import matplotlib.pyplot as plt

try:
	import pywt
except Exception:
	pywt = None

try:
	import torch
	from torch import nn
except Exception:
	torch = None

from scipy import ndimage as ndi
from PIL import Image


def _ensure_1d_array(x):
	arr = np.asarray(x)
	if arr.ndim == 0:
		return arr.reshape(1,)
	if arr.ndim > 1:
		# flatten multi-dimensional samples to 1D time series
		return arr.reshape(-1)
	return arr


def generate_timefrequency_representation(
	x, y, z,
	fs: float = 10000.0,
	nperseg: int = 256,
	noverlap: Optional[int] = None,
	wavelet: str = 'morl',
	widths: Optional[np.ndarray] = None,
	plot: bool = False,
	outdir: Optional[str] = None,
	prefix: str = '',
) -> Dict[str, Dict[str, Any]]:
	"""Compute spectrogram and scalogram for three axes.

	Inputs:
		x, y, z: array-like 1D numeric signals (same or different lengths)
		fs: sampling frequency in Hz
		nperseg, noverlap: passed to scipy.signal.spectrogram
		wavelet, widths: passed to pywt.cwt for scalogram (if pywt available)
		plot: if True, save plots to `outdir` (must be provided) or show inline
		outdir: optional directory where plots will be saved when plot=True
		prefix: filename prefix for saved plots

	Returns:
		dict with keys 'spectrogram' and 'scalogram'. Each contains keys 'x','y','z'.
		Spectrogram entries contain arrays 'f', 't', 'Sxx_db'. Scalogram entries
		contain 'coef' and 'freqs' (or None if pywt missing).
	"""

	print(f"🔬 Starting TFR generation for {len(x)}, {len(y)}, {len(z)} samples")
	
	# normalize and validate
	x = _ensure_1d_array(x)
	y = _ensure_1d_array(y)
	z = _ensure_1d_array(z)
	
	print(f"📊 Normalized arrays: X={x.shape}, Y={y.shape}, Z={z.shape}")

	signals = {'x': x, 'y': y, 'z': z}
	spec_out = {}
	scalo_out = {}

	if outdir and plot:
		os.makedirs(outdir, exist_ok=True)
		print(f"📁 Output directory ready: {outdir}")

	for name, sig in signals.items():
		print(f"🔄 Processing {name}-axis signal ({sig.size} samples)...")
		
		if sig.size == 0:
			raise ValueError(f"Signal '{name}' is empty")

		# Spectrogram
		print(f"   📈 Computing spectrogram...")
		f, t, Sxx = signal.spectrogram(sig, fs=fs, nperseg=nperseg, noverlap=noverlap)
		# convert to dB, add small epsilon to avoid log(0)
		Sxx_db = 10.0 * np.log10(Sxx + 1e-12)
		spec_out[name] = {'f': f, 't': t, 'Sxx_db': Sxx_db}
		print(f"   ✅ Spectrogram done: {Sxx_db.shape}")

		# Scalogram (CWT) if pywt available
		if pywt is not None:
			print(f"   🌊 Computing scalogram...")
			if widths is None:
				# Use fewer scales to speed up computation
				widths = np.arange(1, 64)  # Reduced from 128 to 64
			
			print(f"      Using {len(widths)} scales for CWT...")
			
			# For very large signals, downsample for scalogram computation
			sig_for_cwt = sig
			downsample_factor = 1
			
			if sig.size > 20000:  # If signal is larger than 20k samples
				downsample_factor = max(1, sig.size // 20000)  # Downsample to ~20k samples
				sig_for_cwt = sig[::downsample_factor]
				print(f"      Downsampling by factor {downsample_factor} for CWT: {sig.size} → {sig_for_cwt.size}")
			
			# cwt returns (coef, freqs) with sampling_period parameter available in newer pywt
			try:
				import time
				start_time = time.time()
				
				try:
					coef, freqs = pywt.cwt(sig_for_cwt, widths, wavelet, sampling_period=downsample_factor / fs)
				except TypeError:
					# older pywt versions may not accept sampling_period
					coef, freqs = pywt.cwt(sig_for_cwt, widths, wavelet)
				
				elapsed = time.time() - start_time
				print(f"      CWT computation took {elapsed:.2f}s")
				
				scalo_out[name] = {'coef': coef, 'freqs': freqs, 'downsample_factor': downsample_factor}
				print(f"   ✅ Scalogram done: {coef.shape}")
				
			except Exception as cwt_e:
				print(f"   ❌ CWT computation failed: {cwt_e}")
				scalo_out[name] = None
		else:
			print(f"   ⚠️  PyWavelets not available, skipping scalogram")
			scalo_out[name] = None

		# Optional plotting
		if plot:
			print(f"   🎨 Creating plots...")
			# Set matplotlib to use non-GUI backend for web applications
			import matplotlib
			matplotlib.use('Agg')  # Use non-interactive backend
			
			# spectrogram figure
			print(f"      📊 Plotting spectrogram...")
			fig, ax = plt.subplots(figsize=(8, 4))
			im = ax.pcolormesh(t, f, Sxx_db, shading='gouraud')
			ax.set_ylabel('Frequency [Hz]')
			ax.set_xlabel('Time [sec]')
			ax.set_title(f'Spectrogram - {name} axis')
			plt.colorbar(im, ax=ax, label='PSD (dB)')
			plt.tight_layout()
			if outdir:
				spec_path = os.path.join(outdir, f"{prefix}{name}_spectrogram.png")
				plt.savefig(spec_path, dpi=150, bbox_inches='tight')
				print(f"      ✅ Saved: {spec_path}")
			plt.close(fig)

			# scalogram
			if scalo_out[name] is not None:
				print(f"      🌊 Plotting scalogram...")
				try:
					coef = scalo_out[name]['coef']
					freqs = scalo_out[name]['freqs']
					downsample_factor = scalo_out[name].get('downsample_factor', 1)
					
					# Create time axis for the scalogram (accounting for downsampling)
					t_s = np.arange(coef.shape[1]) * downsample_factor / fs
					
					print(f"         Scalogram data: coef={coef.shape}, freqs={len(freqs)}, downsample={downsample_factor}")
					
					# Skip plotting if data is still too large (shouldn't happen with downsampling)
					if coef.size > 5000000:  # 5M elements
						print(f"         Scalogram too large ({coef.size} elements), skipping plot")
						continue
					
					print(f"         Creating scalogram figure...")
					fig, ax = plt.subplots(figsize=(8, 4))
					# robust plotting: pcolormesh requires matching 2D shapes; fall back to imshow
					mag = np.abs(coef)
					mag = np.asarray(mag)
					print(f"         Magnitude array: {mag.shape}")
					
					# Ensure time axis length matches mag's time dimension
					if mag.ndim == 2:
						cols = mag.shape[1]
						if len(t_s) != cols:
							# recompute t_s to match mag shape
							t_s = np.linspace(0, (cols - 1) / fs, cols)
						try:
							T, F = np.meshgrid(t_s, freqs)
							mappable = ax.pcolormesh(T, F, mag, shading='gouraud')
							print(f"         Used pcolormesh")
						except Exception as e:
							print(f"         Pcolormesh failed: {e}, using imshow")
							# fallback: imshow with extent
							mappable = ax.imshow(mag, aspect='auto', origin='lower',
												extent=(t_s[0], t_s[-1], freqs[0], freqs[-1]))
					else:
						print(f"         Non-2D coef, using imshow")
						# non-2D coef, try to plot as image after forcing 2D
						mag2 = np.atleast_2d(mag)
						cols = mag2.shape[1]
						if len(t_s) != cols:
							t_s = np.linspace(0, (cols - 1) / fs, cols)
						mappable = ax.imshow(mag2, aspect='auto', origin='lower',
												extent=(t_s[0], t_s[-1], freqs[0] if hasattr(freqs, '__len__') and len(freqs)>0 else 0,
												freqs[-1] if hasattr(freqs, '__len__') and len(freqs)>0 else 1))
					
					print(f"         Setting labels and colorbar...")
					ax.set_ylabel('Frequency [Hz]')
					ax.set_xlabel('Time [sec]')
					ax.set_title(f'Scalogram (CWT) - {name} axis')
					
					# Add colorbar with error handling
					try:
						plt.colorbar(mappable, ax=ax, label='Magnitude')
						print(f"         Colorbar added")
					except Exception as cb_e:
						print(f"         Colorbar failed: {cb_e}")
					
					# Set log scale with error handling
					try:
						ax.set_yscale('log')
						print(f"         Log scale applied")
					except Exception as log_e:
						print(f"         Log scale failed: {log_e}, using linear scale")
					
					# Tight layout with error handling
					try:
						plt.tight_layout()
						print(f"         Layout adjusted")
					except Exception as layout_e:
						print(f"         Layout adjustment failed: {layout_e}")
					
					if outdir:
						scalo_path = os.path.join(outdir, f"{prefix}{name}_scalogram.png")
						print(f"         Saving scalogram to: {scalo_path}")
						try:
							plt.savefig(scalo_path, dpi=150, bbox_inches='tight')
							print(f"      ✅ Saved: {scalo_path}")
							# Verify file was created
							if os.path.exists(scalo_path):
								file_size = os.path.getsize(scalo_path)
								print(f"         File size: {file_size:,} bytes")
							else:
								print(f"         ❌ File not created!")
						except Exception as save_e:
							print(f"         ❌ Save failed: {save_e}")
					
					try:
						plt.close(fig)
						print(f"         Figure closed")
					except Exception as close_e:
						print(f"         Close failed: {close_e}")
					
				except Exception as e:
					print(f"      ❌ Scalogram plotting failed: {e}")
					import traceback
					traceback.print_exc()
			else:
				print(f"      ⚠️  No scalogram data to plot")

	print(f"✅ TFR generation completed for all axes")
	return {'spectrogram': spec_out, 'scalogram': scalo_out}


def predict_from_timefreq_and_images(
	model,
	spectrograms: Dict[str, Dict[str, np.ndarray]],
	scalograms: Dict[str, Optional[Dict[str, np.ndarray]]],
	work_img, tool_img, chip_img,
	device: Optional[str] = None,
	preprocess: Optional[Any] = None,
	target_size: Tuple[int, int] = (224, 224),
	as_numpy_output: bool = True,
):
	"""Prepare modalities and run a CNN model for prediction.

	Parameters
	- model: a callable / torch.nn.Module that accepts a tensor or a tuple of tensors.
	- spectrograms: dict with keys 'x','y','z' each -> {'f','t','Sxx_db'} or just 2D array
	- scalograms: dict with keys 'x','y','z' each -> {'coef','freqs'} or 2D array (abs values)
	- work_img, tool_img, chip_img: numpy arrays (H,W,3) or PIL.Image or image file paths
	- device: torch device string like 'cpu' or 'cuda' (optional)
	- preprocess: optional callable(input_array) -> tensor accepted by model
	- target_size: (H,W) target spatial size for CNN input
	- as_numpy_output: if True, convert outputs to numpy arrays before returning

	Default behavior: stack the six time-frequency maps (spec_x,y,z and scalo_x,y,z)
	as channels, then append the three RGB images (each kept as 3 channels). The
	resulting tensor shape will be (1, C, H, W) where C = 6 + 9 = 15 channels.
	If your model expects different input, pass a `preprocess` callable that
	converts the raw numpy inputs into the format the model expects.

	Returns: model outputs (numpy array if as_numpy_output=True) and a dict with
	metadata about the prepared input.
	"""

	if torch is None:
		raise RuntimeError('PyTorch not available in the environment. Install torch to run predictions.')

	def _load_img(img):
		# accept path, PIL.Image, or numpy array
		if isinstance(img, str):
			im = Image.open(img).convert('RGB')
			return np.array(im)
		if isinstance(img, Image.Image):
			return np.array(img.convert('RGB'))
		arr = np.asarray(img)
		# if grayscale, tile to 3 channels
		if arr.ndim == 2:
			arr = np.stack([arr] * 3, axis=-1)
		if arr.shape[-1] == 1:
			arr = np.concatenate([arr] * 3, axis=-1)
		return arr

	def _resize(arr, target):
		# arr is 2D or 3D (H,W or H,W,C). Resize using scipy.ndimage.zoom
		arr = np.asarray(arr)
		h, w = arr.shape[0], arr.shape[1]
		th, tw = target
		if (h, w) == (th, tw):
			return arr
		zh = th / h
		zw = tw / w
		if arr.ndim == 2:
			return ndi.zoom(arr, (zh, zw), order=1)
		else:
			# channel last
			channels = arr.shape[2]
			out = np.zeros((th, tw, channels), dtype=arr.dtype)
			for c in range(channels):
				out[..., c] = ndi.zoom(arr[..., c], (zh, zw), order=1)
			return out

	def _normalize_channel(ch):
		ch = ch.astype(np.float32)
		mn = ch.min()
		ch = ch - mn
		mx = ch.max()
		if mx > 0:
			ch = ch / mx
		return ch

	# extract Sxx_db or raw 2D arrays
	tf_maps = []
	for k in ('x', 'y', 'z'):
		# spectrograms[k] might be dict or ndarray
		spec_entry = spectrograms.get(k)
		if isinstance(spec_entry, dict):
			s = spec_entry.get('Sxx_db')
			if s is None:
				s = spec_entry.get('Sxx')
			if s is None:
				s = spec_entry.get('data')  # fallback key
		else:
			s = spec_entry
		if s is None:
			raise ValueError(f'Spectrogram for axis {k} not provided')
		s = np.asarray(s)
		s = _resize(s, target_size)
		s = _normalize_channel(s)
		tf_maps.append(s)

	for k in ('x', 'y', 'z'):
		sc = scalograms.get(k)
		if sc is None:
			# append zeros if scalogram missing
			tf_maps.append(np.zeros(target_size, dtype=np.float32))
			continue
		if isinstance(sc, dict):
			coef = sc.get('coef')
			if coef is None:
				tf_maps.append(np.zeros(target_size, dtype=np.float32))
				continue
			# take magnitude and sum/mean across scales to produce 2D map
			mag = np.abs(coef)
			# mag shape (scales, times)
			# reduce to 2D by resizing (scales x times) to target
			mag2 = _resize(mag, target_size)
		else:
			mag2 = _resize(np.asarray(sc), target_size)
		mag2 = _normalize_channel(mag2)
		tf_maps.append(mag2)

	# now load images and resize
	work = _load_img(work_img)
	tool = _load_img(tool_img)
	chip = _load_img(chip_img)
	work = _resize(work, target_size)
	tool = _resize(tool, target_size)
	chip = _resize(chip, target_size)
	# normalize images to 0-1
	work = _normalize_channel(work)
	tool = _normalize_channel(tool)
	chip = _normalize_channel(chip)

	# Stack tf_maps (each is HxW) into channels, then append images channels
	# tf_maps -> (H,W,6)
	tf_stack = np.stack(tf_maps, axis=-1)
	imgs_stack = np.concatenate([work, tool, chip], axis=-1)  # H,W,9
	full = np.concatenate([tf_stack, imgs_stack], axis=-1)  # H,W,C

	# move channels to channel-first
	input_arr = np.transpose(full, (2, 0, 1)).astype(np.float32)
	input_tensor = torch.from_numpy(input_arr).unsqueeze(0)  # 1,C,H,W

	# Optional user preprocess
	if preprocess is not None:
		input_for_model = preprocess(input_tensor)
	else:
		input_for_model = input_tensor

	# move to device
	dev = torch.device(device) if device is not None else next(model.parameters()).device if hasattr(model, 'parameters') else torch.device('cpu')
	input_for_model = input_for_model.to(dev)
	model = model.to(dev)
	model.eval()
	with torch.no_grad():
		outputs = model(input_for_model)

	if as_numpy_output:
		try:
			out_np = outputs.detach().cpu().numpy()
		except Exception:
			# if outputs is not tensor, just return as-is
			out_np = outputs
		return out_np, {'input_shape': input_tensor.shape}
	return outputs, {'input_shape': input_tensor.shape}


def stream_to_prediction(
	x_stream,
	y_stream,
	z_stream,
	work_img,
	tool_img,
	chip_img,
	model,
	fs: float = 10000.0,
	spec_nperseg: int = 256,
	spec_noverlap: Optional[int] = None,
	cwt_wavelet: str = 'morl',
	cwt_widths: Optional[np.ndarray] = None,
	tf_target_size: Tuple[int, int] = (224, 224),
	preprocess: Optional[Any] = None,
	device: Optional[str] = None,
	plot_tf: bool = False,
	outdir: Optional[str] = None,
):
	"""End-to-end helper: from raw streams -> TFRs -> model prediction.

	Parameters
	- x_stream, y_stream, z_stream: 1D numeric arrays (raw force streams)
	- work_img, tool_img, chip_img: images (path, PIL.Image, or numpy array)
	- model: PyTorch model or callable compatible with predict_from_timefreq_and_images
	- fs: sampling frequency
	- spec_nperseg, spec_noverlap: spectrogram params
	- cwt_wavelet, cwt_widths: scalogram params
	- tf_target_size: size to which TF maps are resized before feeding model
	- preprocess, device: passed to predict helper
	- plot_tf/outdir: if plot_tf True, spectrograms/scalograms will be saved to outdir

	Returns: model outputs (numpy array if model returns tensor and as_numpy_output True by default)
	"""

	# compute TFRs
	tfr = generate_timefrequency_representation(
		x_stream, y_stream, z_stream,
		fs=fs,
		nperseg=spec_nperseg,
		noverlap=spec_noverlap,
		wavelet=cwt_wavelet,
		widths=cwt_widths,
		plot=plot_tf,
		outdir=outdir,
		prefix='stream_'
	)

	specs = tfr['spectrogram']
	scalos = tfr['scalogram']

	# predict
	outputs, meta = predict_from_timefreq_and_images(
		model=model,
		spectrograms=specs,
		scalograms=scalos,
		work_img=work_img,
		tool_img=tool_img,
		chip_img=chip_img,
		device=device,
		preprocess=preprocess,
		target_size=tf_target_size,
		as_numpy_output=True,
	)

	return outputs, meta
