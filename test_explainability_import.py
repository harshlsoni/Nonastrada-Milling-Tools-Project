#!/usr/bin/env python3
"""Test if explainability module can be imported."""

import sys
import os

# Add Code directory to path
code_dir = os.path.join(os.path.dirname(__file__), 'Code')
sys.path.insert(0, code_dir)

print(f"Testing import from: {code_dir}")
print()

try:
    from Explainability.simple_explainer import (
        analyze_prediction_simple,
        format_explanation_text,
        create_contribution_breakdown_simple,
        visualize_contributions_simple
    )
    print("✓ SUCCESS: All functions imported successfully!")
    print()
    
    # Test with sample data
    sample_prediction = {
        'predicted_label': 'Worn',
        'confidence': 0.87,
        'probabilities': [0.05, 0.08, 0.87],
        'class_names': ['Sharp', 'Used', 'Worn']
    }
    
    print("Testing functions...")
    explanation = analyze_prediction_simple(sample_prediction)
    print("✓ analyze_prediction_simple() works")
    
    contributions = create_contribution_breakdown_simple(sample_prediction)
    print("✓ create_contribution_breakdown_simple() works")
    
    text = format_explanation_text(explanation)
    print("✓ format_explanation_text() works")
    
    viz = visualize_contributions_simple(contributions)
    print("✓ visualize_contributions_simple() works")
    
    print()
    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("The explainability module is working correctly.")
    print("You can now run: python Code/flask_app.py")
    
except ImportError as e:
    print(f"✗ FAILED: Could not import explainability module")
    print(f"Error: {e}")
    print()
    print("Troubleshooting:")
    print("1. Check that Code/Explainability/simple_explainer.py exists")
    print("2. Check that Code/Explainability/__init__.py exists")
    print("3. Try running from project root directory")
    sys.exit(1)
