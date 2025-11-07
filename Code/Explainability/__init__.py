"""
Explainability module for milling forces analysis.

This module provides interpretability tools for the multi-modal CNN model.
"""

# Import available modules
try:
    from .simple_explainer import (
        analyze_prediction_simple,
        format_explanation_text,
        create_contribution_breakdown_simple,
        visualize_contributions_simple
    )
    __all__ = [
        'analyze_prediction_simple',
        'format_explanation_text',
        'create_contribution_breakdown_simple',
        'visualize_contributions_simple'
    ]
except ImportError:
    __all__ = []

# Future imports (when implemented)
# from .modality_attribution import get_modality_contributions, visualize_contributions
# from .frequency_analysis import analyze_frequency_bands, interpret_frequency_patterns
