#!/usr/bin/env python3
"""
Test script to verify all model architectures work correctly
"""

import torch
import warnings
from network_architecture import (
    Network, ResNetMultiModal, EfficientNetMultiModal, 
    MobileNetMultiModal, AlexNetMultiModal, VGG16MultiModal
)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def test_model_architecture(model_class, model_name, num_classes=3):
    """Test a single model architecture"""
    print(f"\nTesting {model_name}...")
    
    try:
        # Initialize model
        model = model_class(num_classes)
        model.eval()
        
        # Create dummy input (9 modalities, batch_size=2, 3 channels, 224x224)
        dummy_input = {}
        modalities = ["chip", "scalx", "scaly", "scalz", "specx", "specy", "specz", "tool", "work"]
        
        for modality in modalities:
            dummy_input[modality] = torch.randn(2, 3, 224, 224)
        
        # Forward pass
        with torch.no_grad():
            output = model(dummy_input)
        
        # Check output shape
        expected_shape = (2, num_classes)
        if output.shape == expected_shape:
            print(f"PASS {model_name}: Output shape {output.shape}")
            
            # Check parameter counts
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            
            print(f"   Total parameters: {total_params:,}")
            print(f"   Trainable parameters: {trainable_params:,}")
            print(f"   Model size: {total_params * 4 / (1024**2):.2f} MB")
            
            # Test gradient flow with fresh forward pass
            model.train()  # Set to training mode
            model.zero_grad()  # Clear any existing gradients
            
            # Create fresh input that requires gradients
            fresh_input = {}
            for modality in modalities:
                fresh_input[modality] = torch.randn(2, 3, 224, 224, requires_grad=True)
            
            # Fresh forward pass
            fresh_output = model(fresh_input)
            loss = torch.nn.functional.cross_entropy(fresh_output, torch.tensor([0, 1]))
            loss.backward()
            
            # Check if gradients exist for trainable parameters
            trainable_params = [p for p in model.parameters() if p.requires_grad]
            if len(trainable_params) == 0:
                print(f"   Gradient flow: SKIPPED (no trainable parameters)")
            else:
                grad_check = any(p.grad is not None for p in trainable_params)
                if grad_check:
                    print(f"   Gradient flow: OK")
                else:
                    print(f"   Gradient flow: FAILED")
                    return False
            
            return True
        else:
            print(f"FAIL {model_name}: Wrong output shape {output.shape}, expected {expected_shape}")
            return False
            
    except Exception as e:
        print(f"FAIL {model_name}: Error - {e}")
        return False

def test_model_consistency(model_class, model_name, num_classes=3):
    """Test model consistency across multiple runs"""
    print(f"\nTesting {model_name} consistency...")
    
    try:
        # Create two identical models
        model1 = model_class(num_classes)
        model2 = model_class(num_classes)
        
        # Load same state dict
        state_dict = model1.state_dict()
        model2.load_state_dict(state_dict)
        
        # Set to eval mode
        model1.eval()
        model2.eval()
        
        # Create dummy input
        dummy_input = {}
        modalities = ["chip", "scalx", "scaly", "scalz", "specx", "specy", "specz", "tool", "work"]
        
        for modality in modalities:
            dummy_input[modality] = torch.randn(1, 3, 224, 224)
        
        # Forward pass on both models
        with torch.no_grad():
            output1 = model1(dummy_input)
            output2 = model2(dummy_input)
        
        # Check if outputs are identical
        if torch.allclose(output1, output2, atol=1e-6):
            print(f"PASS {model_name}: Consistency check passed")
            return True
        else:
            print(f"FAIL {model_name}: Outputs differ between identical models")
            return False
            
    except Exception as e:
        print(f"FAIL {model_name}: Consistency test error - {e}")
        return False

def test_different_batch_sizes(model_class, model_name, num_classes=3):
    """Test model with different batch sizes"""
    print(f"\nTesting {model_name} with different batch sizes...")
    
    try:
        model = model_class(num_classes)
        model.eval()
        
        batch_sizes = [1, 4, 8]
        modalities = ["chip", "scalx", "scaly", "scalz", "specx", "specy", "specz", "tool", "work"]
        
        for batch_size in batch_sizes:
            dummy_input = {}
            for modality in modalities:
                dummy_input[modality] = torch.randn(batch_size, 3, 224, 224)
            
            with torch.no_grad():
                output = model(dummy_input)
            
            expected_shape = (batch_size, num_classes)
            if output.shape != expected_shape:
                print(f"FAIL {model_name}: Batch size {batch_size} failed, got {output.shape}")
                return False
        
        print(f"PASS {model_name}: All batch sizes work correctly")
        return True
        
    except Exception as e:
        print(f"FAIL {model_name}: Batch size test error - {e}")
        return False

def test_memory_usage(model_class, model_name, num_classes=3):
    """Test memory usage and cleanup"""
    print(f"\nTesting {model_name} memory usage...")
    
    try:
        # Clear any existing cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            initial_memory = torch.cuda.memory_allocated()
        else:
            initial_memory = 0
        
        # Create and use model
        model = model_class(num_classes)
        if torch.cuda.is_available():
            model = model.cuda()
        
        dummy_input = {}
        modalities = ["chip", "scalx", "scaly", "scalz", "specx", "specy", "specz", "tool", "work"]
        
        for modality in modalities:
            tensor = torch.randn(2, 3, 224, 224)
            if torch.cuda.is_available():
                tensor = tensor.cuda()
            dummy_input[modality] = tensor
        
        # Forward pass
        output = model(dummy_input)
        
        if torch.cuda.is_available():
            peak_memory = torch.cuda.memory_allocated()
            memory_used = (peak_memory - initial_memory) / (1024**2)  # MB
            print(f"PASS {model_name}: GPU memory used: {memory_used:.2f} MB")
        else:
            print(f"PASS {model_name}: CPU mode - memory test skipped")
        
        # Cleanup
        del model, dummy_input, output
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return True
        
    except Exception as e:
        print(f"FAIL {model_name}: Memory test error - {e}")
        return False

def main():
    """Test all model architectures comprehensively"""
    print("Testing All Model Architectures")
    print("=" * 50)
    
    models_to_test = [
        (Network, "Custom CNN"),
        (ResNetMultiModal, "ResNet18 MultiModal"),
        (EfficientNetMultiModal, "EfficientNet-B0 MultiModal"),
        (MobileNetMultiModal, "MobileNetV2 MultiModal"),
        (AlexNetMultiModal, "AlexNet MultiModal"),
        (VGG16MultiModal, "VGG16 MultiModal")
    ]
    
    test_results = {
        'basic': [],
        'consistency': [],
        'batch_sizes': [],
        'memory': []
    }
    
    # Run all tests
    for model_class, model_name in models_to_test:
        print(f"\n{'='*60}")
        print(f"TESTING: {model_name}")
        print(f"{'='*60}")
        
        # Basic functionality test
        basic_result = test_model_architecture(model_class, model_name)
        test_results['basic'].append((model_name, basic_result))
        
        # Consistency test
        consistency_result = test_model_consistency(model_class, model_name)
        test_results['consistency'].append((model_name, consistency_result))
        
        # Batch size test
        batch_result = test_different_batch_sizes(model_class, model_name)
        test_results['batch_sizes'].append((model_name, batch_result))
        
        # Memory test
        memory_result = test_memory_usage(model_class, model_name)
        test_results['memory'].append((model_name, memory_result))
    
    # Print comprehensive summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    
    test_categories = [
        ('Basic Functionality', 'basic'),
        ('Model Consistency', 'consistency'),
        ('Batch Size Handling', 'batch_sizes'),
        ('Memory Usage', 'memory')
    ]
    
    overall_results = {}
    
    for category_name, category_key in test_categories:
        print(f"\n{category_name}:")
        print("-" * 30)
        
        passed = 0
        total = len(test_results[category_key])
        
        for model_name, success in test_results[category_key]:
            status = "PASS" if success else "FAIL"
            print(f"  {status} {model_name}")
            if success:
                passed += 1
        
        overall_results[category_name] = (passed, total)
        print(f"  Result: {passed}/{total} models passed")
    
    # Overall summary
    print(f"\n{'='*60}")
    print("OVERALL RESULTS")
    print(f"{'='*60}")
    
    total_tests = 0
    total_passed = 0
    
    for category, (passed, total) in overall_results.items():
        total_tests += total
        total_passed += passed
        percentage = (passed / total) * 100 if total > 0 else 0
        print(f"{category}: {passed}/{total} ({percentage:.1f}%)")
    
    overall_percentage = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    print(f"\nOverall: {total_passed}/{total_tests} ({overall_percentage:.1f}%)")
    
    if overall_percentage == 100:
        print("\nAll tests passed! Models are ready for training.")
    elif overall_percentage >= 75:
        print("\nMost tests passed. Minor issues may need attention.")
    else:
        print("\nSeveral tests failed. Please review and fix issues before training.")
    
    return overall_percentage == 100

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)