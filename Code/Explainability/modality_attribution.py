"""
Modality Attribution - Feature Importance Analysis

Determines which input modalities (spectrograms, scalograms, images)
contribute most to the model's prediction.
"""

import torch
import numpy as np
from typing import Dict, Tuple


def get_modality_contributions(
    model: torch.nn.Module,
    x_dict: Dict[str, torch.Tensor],
    target_class: int = None
) -> Dict[str, float]:
    """
    Calculate contribution of each modality using gradient-based attribution.
    
    Args:
        model: Trained PyTorch model
        x_dict: Dictionary of input tensors for each modality
        target_class: Target class index (if None, uses predicted class)
    
    Returns:
        Dictionary mapping modality names to contribution percentages
    """
    
    # Ensure model is in eval mode
    model.eval()
    
    # Enable gradients for inputs
    x_dict_grad = {}
    for modality_name, modality_input in x_dict.items():
        x_dict_grad[modality_name] = modality_input.clone().requires_grad_(True)
    
    # Forward pass
    output = model(x_dict_grad)
    
    # Use predicted class if target not specified
    if target_class is None:
        target_class = output.argmax(dim=1).item()
    
    # Backward pass for target class
    model.zero_grad()
    output[0, target_class].backward()
    
    # Calculate contribution for each modality
    contributions = {}
    for modality_name, modality_input in x_dict_grad.items():
        if modality_input.grad is not None:
            # Use gradient magnitude as contribution measure
            contribution = modality_input.grad.abs().mean().item()
            contributions[modality_name] = contribution
        else:
            contributions[modality_name] = 0.0
    
    # Normalize to percentages
    total = sum(contributions.values())
    if total > 0:
        contributions = {k: (v/total)*100 for k, v in contributions.items()}
    
    return contributions


def group_contributions_by_type(contributions: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    Group modality contributions by type (spectrograms, scalograms, images).
    
    Args:
        contributions: Raw modality contributions
    
    Returns:
        Grouped contributions with subtotals
    """
    
    grouped = {
        'spectrograms': {},
        'scalograms': {},
        'images': {}
    }
    
    for modality, value in contributions.items():
        if 'spec' in modality.lower():
            grouped['spectrograms'][modality] = value
        elif 'scal' in modality.lower():
            grouped['scalograms'][modality] = value
        else:
            grouped['images'][modality] = value
    
    # Calculate subtotals
    result = {}
    for group_name, group_data in grouped.items():
        if group_data:
            result[group_name] = {
                'total': sum(group_data.values()),
                'breakdown': group_data
            }
    
    return result


def visualize_contributions(contributions: Dict[str, float]) -> str:
    """
    Create a text-based visualization of modality contributions.
    
    Args:
        contributions: Modality contributions as percentages
    
    Returns:
        Formatted string representation
    """
    
    # Group by type
    grouped = group_contributions_by_type(contributions)
    
    output = ["Prediction Contribution Breakdown:", ""]
    
    # Sort groups by total contribution
    sorted_groups = sorted(grouped.items(), key=lambda x: x[1]['total'], reverse=True)
    
    for group_name, group_data in sorted_groups:
        total = group_data['total']
        breakdown = group_data['breakdown']
        
        # Group header
        bar_length = int(total / 2)  # Scale to fit display
        bar = '█' * bar_length
        output.append(f"├─ {group_name.title()}: {total:.1f}% {bar}")
        
        # Individual modalities
        sorted_modalities = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        for i, (modality, value) in enumerate(sorted_modalities):
            is_last = (i == len(sorted_modalities) - 1)
            prefix = "   └─" if is_last else "   ├─"
            
            # Clean up modality name
            clean_name = modality.replace('spec', 'Spectrogram ').replace('scal', 'Scalogram ')
            clean_name = clean_name.replace('x', 'X-axis').replace('y', 'Y-axis').replace('z', 'Z-axis')
            clean_name = clean_name.title()
            
            output.append(f"{prefix} {clean_name}: {value:.1f}%")
        
        output.append("")
    
    return "\n".join(output)


def get_top_contributors(contributions: Dict[str, float], n: int = 3) -> list:
    """
    Get the top N contributing modalities.
    
    Args:
        contributions: Modality contributions
        n: Number of top contributors to return
    
    Returns:
        List of (modality_name, contribution_percentage) tuples
    """
    
    sorted_contributions = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    return sorted_contributions[:n]


def interpret_contributions(contributions: Dict[str, float], prediction: str) -> str:
    """
    Generate human-readable interpretation of contributions.
    
    Args:
        contributions: Modality contributions
        prediction: Model prediction (e.g., "Worn Tool")
    
    Returns:
        Natural language interpretation
    """
    
    grouped = group_contributions_by_type(contributions)
    top_contributors = get_top_contributors(contributions, n=3)
    
    interpretation = []
    
    # Overall summary
    interpretation.append(f"The model predicted '{prediction}' based primarily on:")
    interpretation.append("")
    
    # Top contributors
    for i, (modality, value) in enumerate(top_contributors, 1):
        clean_name = modality.replace('spec', 'spectrogram ').replace('scal', 'scalogram ')
        clean_name = clean_name.replace('x', 'X-axis').replace('y', 'Y-axis').replace('z', 'Z-axis')
        interpretation.append(f"{i}. {clean_name.title()} ({value:.1f}% contribution)")
    
    interpretation.append("")
    
    # Group analysis
    if 'spectrograms' in grouped and grouped['spectrograms']['total'] > 40:
        interpretation.append(
            "Force signal analysis (spectrograms) was the dominant factor, "
            "indicating that frequency patterns in the cutting forces were "
            "the primary indicator of tool condition."
        )
    
    if 'images' in grouped and grouped['images']['total'] > 30:
        interpretation.append(
            "Visual inspection (images) played a significant role, "
            "suggesting visible wear patterns or chip characteristics "
            "were important for this prediction."
        )
    
    if 'scalograms' in grouped and grouped['scalograms']['total'] > 30:
        interpretation.append(
            "Wavelet analysis (scalograms) contributed substantially, "
            "indicating that time-localized frequency changes were "
            "important for detecting tool wear."
        )
    
    return "\n".join(interpretation)


# Example usage
if __name__ == "__main__":
    # This would be called with actual model and data
    print("Modality Attribution Module")
    print("=" * 60)
    print("\nExample output:")
    print()
    
    # Simulated contributions
    example_contributions = {
        'specx': 18.5,
        'specy': 15.2,
        'specz': 12.3,
        'scalx': 12.0,
        'scaly': 10.5,
        'scalz': 8.0,
        'tool': 15.0,
        'chip': 6.5,
        'work': 2.0
    }
    
    print(visualize_contributions(example_contributions))
    print()
    print(interpret_contributions(example_contributions, "Worn Tool"))
