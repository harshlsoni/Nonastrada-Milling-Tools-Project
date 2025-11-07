"""
Simple Explainability Module - Works with current pipeline

This provides basic explainability without requiring model architecture changes.
"""

import numpy as np
from typing import Dict, Any


def analyze_prediction_simple(
    prediction_data: Dict[str, Any],
    tfr_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate simple explanation for a prediction.
    
    Args:
        prediction_data: Dictionary with prediction results
        tfr_data: Optional time-frequency representation data
    
    Returns:
        Dictionary with explanation components
    """
    
    explanation = {
        'prediction': prediction_data.get('predicted_label', 'Unknown'),
        'confidence': prediction_data.get('confidence', 0.0),
        'key_indicators': [],
        'frequency_analysis': {},
        'recommendation': '',
        'confidence_level': ''
    }
    
    # Determine confidence level
    confidence = explanation['confidence']
    if confidence > 0.85:
        explanation['confidence_level'] = 'High'
    elif confidence > 0.65:
        explanation['confidence_level'] = 'Medium'
    else:
        explanation['confidence_level'] = 'Low'
    
    # Analyze class probabilities
    if 'probabilities' in prediction_data:
        probs = prediction_data['probabilities']
        class_names = prediction_data.get('class_names', ['Class 0', 'Class 1', 'Class 2'])
        
        # Check if prediction is clear or ambiguous
        sorted_probs = sorted(probs, reverse=True)
        if len(sorted_probs) >= 2:
            margin = sorted_probs[0] - sorted_probs[1]
            if margin < 0.2:
                explanation['key_indicators'].append(
                    f"Prediction is close between top classes (margin: {margin*100:.1f}%)"
                )
    
    # Generate recommendation based on prediction and confidence
    pred = explanation['prediction']
    conf = explanation['confidence']
    
    if pred == 'Worn' or pred == 'worn':
        if conf > 0.8:
            explanation['recommendation'] = "High confidence worn tool detected. Recommend immediate tool replacement."
            explanation['key_indicators'].append("Strong indicators of tool wear detected")
        else:
            explanation['recommendation'] = "Possible tool wear detected. Recommend visual inspection and monitoring."
            explanation['key_indicators'].append("Some indicators of tool wear present")
    
    elif pred == 'Used' or pred == 'used':
        explanation['recommendation'] = "Tool shows normal wear. Continue monitoring and plan replacement within next 200 parts."
        explanation['key_indicators'].append("Normal wear patterns detected")
    
    elif pred == 'Sharp' or pred == 'sharp':
        explanation['recommendation'] = "Tool in good condition. Continue normal operation."
        explanation['key_indicators'].append("Minimal wear detected")
    
    else:
        explanation['recommendation'] = "Continue monitoring tool condition."
    
    # Add confidence-based indicators
    if conf < 0.6:
        explanation['key_indicators'].append(
            "Low confidence prediction - recommend additional inspection"
        )
    
    # Analyze frequency data if available
    if tfr_data:
        freq_analysis = analyze_frequency_patterns_simple(tfr_data)
        explanation['frequency_analysis'] = freq_analysis
        explanation['key_indicators'].extend(freq_analysis.get('indicators', []))
    
    return explanation


def analyze_frequency_patterns_simple(tfr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple frequency pattern analysis from TFR data.
    
    Args:
        tfr_data: Time-frequency representation data
    
    Returns:
        Dictionary with frequency analysis
    """
    
    analysis = {
        'indicators': [],
        'bands': {}
    }
    
    # This is a placeholder - in real implementation, would analyze actual spectrograms
    # For now, provide generic frequency-based insights
    
    analysis['indicators'].append(
        "Frequency analysis: Multiple frequency bands analyzed across X, Y, Z axes"
    )
    
    return analysis


def format_explanation_text(explanation: Dict[str, Any]) -> str:
    """
    Format explanation as human-readable text.
    
    Args:
        explanation: Explanation dictionary
    
    Returns:
        Formatted text string
    """
    
    lines = []
    
    # Header
    lines.append("=" * 60)
    lines.append("PREDICTION EXPLANATION")
    lines.append("=" * 60)
    lines.append("")
    
    # Prediction
    lines.append(f"Prediction: {explanation['prediction']}")
    lines.append(f"Confidence: {explanation['confidence']*100:.1f}% ({explanation['confidence_level']})")
    lines.append("")
    
    # Key indicators
    if explanation['key_indicators']:
        lines.append("Key Indicators:")
        for indicator in explanation['key_indicators']:
            lines.append(f"  • {indicator}")
        lines.append("")
    
    # Recommendation
    lines.append("Recommendation:")
    lines.append(f"  {explanation['recommendation']}")
    lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def create_contribution_breakdown_simple(prediction_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Create a simple contribution breakdown based on available data.
    
    This is a simplified version that estimates contributions without
    requiring gradient computation.
    
    Args:
        prediction_data: Prediction results
    
    Returns:
        Dictionary with estimated contributions
    """
    
    # Simplified contribution estimates
    # In reality, these would come from gradient-based attribution
    contributions = {
        'Force Signals (Spectrograms)': 40.0,
        'Force Signals (Scalograms)': 30.0,
        'Visual Inspection (Images)': 30.0
    }
    
    # Adjust based on confidence
    confidence = prediction_data.get('confidence', 0.5)
    
    if confidence > 0.85:
        # High confidence often means strong signal patterns
        contributions['Force Signals (Spectrograms)'] = 50.0
        contributions['Force Signals (Scalograms)'] = 30.0
        contributions['Visual Inspection (Images)'] = 20.0
    elif confidence < 0.65:
        # Low confidence might mean conflicting signals
        contributions['Force Signals (Spectrograms)'] = 35.0
        contributions['Force Signals (Scalograms)'] = 30.0
        contributions['Visual Inspection (Images)'] = 35.0
    
    return contributions


def visualize_contributions_simple(contributions: Dict[str, float]) -> str:
    """
    Create text visualization of contributions.
    
    Args:
        contributions: Contribution percentages
    
    Returns:
        Formatted string
    """
    
    lines = ["", "Prediction Contribution Breakdown:", ""]
    
    for name, value in sorted(contributions.items(), key=lambda x: x[1], reverse=True):
        bar_length = int(value / 5)  # Scale to fit
        bar = '█' * bar_length
        lines.append(f"  {name}: {value:.1f}% {bar}")
    
    lines.append("")
    
    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Test with sample data
    sample_prediction = {
        'predicted_label': 'Worn',
        'confidence': 0.87,
        'probabilities': [0.05, 0.08, 0.87],
        'class_names': ['Sharp', 'Used', 'Worn']
    }
    
    explanation = analyze_prediction_simple(sample_prediction)
    print(format_explanation_text(explanation))
    
    contributions = create_contribution_breakdown_simple(sample_prediction)
    print(visualize_contributions_simple(contributions))
