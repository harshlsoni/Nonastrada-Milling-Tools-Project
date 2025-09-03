#!/usr/bin/env python3
"""
Test script to verify hyperparameter tuner functionality
"""

import torch
import torch.nn as nn
import warnings
from torch.utils.data import DataLoader, TensorDataset
from hyperparameter_tuner import HyperparameterTuner
from network_architecture import Network, ResNetMultiModal

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def create_dummy_dataset(num_samples=100, num_classes=3):
    """Create a dummy dataset for testing"""
    print("Creating dummy dataset...")
    
    # Create dummy multi-modal data
    modalities = ["chip", "scalx", "scaly", "scalz", "specx", "specy", "specz", "tool", "work"]
    
    # Generate random data for each modality
    data_dict = {}
    for modality in modalities:
        data_dict[modality] = torch.randn(num_samples, 3, 224, 224)
    
    # Generate random labels
    labels = torch.randint(0, num_classes, (num_samples,))
    
    # Create custom dataset class
    class MultiModalDataset(torch.utils.data.Dataset):
        def __init__(self, data_dict, labels):
            self.data_dict = data_dict
            self.labels = labels
            
        def __len__(self):
            return len(self.labels)
        
        def __getitem__(self, idx):
            sample = {}
            for modality, data in self.data_dict.items():
                sample[modality] = data[idx]
            return sample, self.labels[idx], torch.tensor(0), torch.tensor(0.0)  # dummy tool_label and flank_wear
    
    dataset = MultiModalDataset(data_dict, labels)
    return dataset

def test_hyperparameter_tuner_initialization():
    """Test hyperparameter tuner initialization"""
    print("\nTesting HyperparameterTuner initialization...")
    
    try:
        # Create dummy data loaders
        dataset = create_dummy_dataset(50)
        train_loader = DataLoader(dataset, batch_size=8, shuffle=True)
        val_loader = DataLoader(dataset, batch_size=8, shuffle=False)
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize tuner
        tuner = HyperparameterTuner(
            model_class=Network,
            train_loader=train_loader,
            val_loader=val_loader,
            num_classes=3,
            device=device
        )
        
        print("PASS: HyperparameterTuner initialized successfully")
        return True, tuner, train_loader, val_loader, device
        
    except Exception as e:
        print(f"FAIL: HyperparameterTuner initialization error - {e}")
        return False, None, None, None, None

def test_parameter_grid_creation(tuner):
    """Test parameter grid creation"""
    print("\nTesting parameter grid creation...")
    
    try:
        param_grid = tuner.create_param_grid()
        
        # Check if all expected parameters are present
        expected_params = ['learning_rate', 'batch_size', 'optimizer', 'weight_decay', 
                          'dropout_rate', 'scheduler', 'scheduler_params']
        
        for param in expected_params:
            if param not in param_grid:
                print(f"FAIL: Missing parameter {param} in grid")
                return False
        
        # Check if parameter values are reasonable
        if not isinstance(param_grid['learning_rate'], list) or len(param_grid['learning_rate']) == 0:
            print("FAIL: Invalid learning_rate parameter")
            return False
        
        print("PASS: Parameter grid created successfully")
        print(f"   Learning rates: {param_grid['learning_rate']}")
        print(f"   Optimizers: {param_grid['optimizer']}")
        print(f"   Schedulers: {param_grid['scheduler']}")
        return True
        
    except Exception as e:
        print(f"FAIL: Parameter grid creation error - {e}")
        return False

def test_optimizer_creation(tuner):
    """Test optimizer creation"""
    print("\nTesting optimizer creation...")
    
    try:
        # Create a dummy model
        model = Network(3)
        
        # Test different optimizers
        optimizers_to_test = ['adam', 'sgd', 'adamw']
        
        for opt_name in optimizers_to_test:
            optimizer = tuner.get_optimizer(model, opt_name, 1e-4, 1e-5)
            
            if optimizer is None:
                print(f"FAIL: Failed to create {opt_name} optimizer")
                return False
            
            # Check if optimizer has the correct parameters
            if not hasattr(optimizer, 'param_groups'):
                print(f"FAIL: {opt_name} optimizer missing param_groups")
                return False
        
        print("PASS: All optimizers created successfully")
        return True
        
    except Exception as e:
        print(f"FAIL: Optimizer creation error - {e}")
        return False

def test_scheduler_creation(tuner):
    """Test scheduler creation"""
    print("\nTesting scheduler creation...")
    
    try:
        # Create a dummy model and optimizer
        model = Network(3)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
        
        # Test different schedulers
        schedulers_to_test = [
            ('none', {}),
            ('step', {'step_size': 10, 'gamma': 0.1}),
            ('cosine', {'T_max': 50})
        ]
        
        for scheduler_name, scheduler_params in schedulers_to_test:
            scheduler = tuner.get_scheduler(optimizer, scheduler_name, scheduler_params)
            
            if scheduler_name == 'none':
                if scheduler is not None:
                    print(f"FAIL: 'none' scheduler should return None")
                    return False
            else:
                if scheduler is None:
                    print(f"FAIL: Failed to create {scheduler_name} scheduler")
                    return False
        
        print("PASS: All schedulers created successfully")
        return True
        
    except Exception as e:
        print(f"FAIL: Scheduler creation error - {e}")
        return False

def test_single_config_training(tuner, train_loader, val_loader):
    """Test training with a single configuration"""
    print("\nTesting single configuration training...")
    
    try:
        # Create a simple configuration
        config = {
            'learning_rate': 1e-3,
            'optimizer': 'adam',
            'weight_decay': 1e-5,
            'scheduler': 'none'
        }
        
        # Train for just 2 epochs to test functionality
        result = tuner.train_single_config(config, max_epochs=2, patience=5)
        
        # Check if result has expected keys
        expected_keys = ['config', 'train_losses', 'train_accs', 'val_losses', 'val_accs',
                        'best_val_acc', 'final_val_acc', 'epochs_trained', 'training_time']
        
        for key in expected_keys:
            if key not in result:
                print(f"FAIL: Missing key {key} in training result")
                return False
        
        # Check if training actually happened
        if result['epochs_trained'] == 0:
            print("FAIL: No epochs were trained")
            return False
        
        # Check if losses and accuracies are reasonable
        if not (0 <= result['best_val_acc'] <= 1):
            print(f"FAIL: Invalid validation accuracy {result['best_val_acc']}")
            return False
        
        print("PASS: Single configuration training completed successfully")
        print(f"   Epochs trained: {result['epochs_trained']}")
        print(f"   Best validation accuracy: {result['best_val_acc']:.4f}")
        print(f"   Training time: {result['training_time']:.2f}s")
        return True
        
    except Exception as e:
        print(f"FAIL: Single configuration training error - {e}")
        return False

def test_hyperparameter_tuning(tuner):
    """Test full hyperparameter tuning with limited trials"""
    print("\nTesting hyperparameter tuning (limited trials)...")
    
    try:
        # Run tuning with very limited parameters for speed
        best_config, best_score, all_results = tuner.tune_hyperparameters(
            max_trials=3,  # Very limited for testing
            max_epochs=2,  # Very short training
            patience=2
        )
        
        # Check if results are valid
        if best_config is None:
            print("FAIL: No best configuration found")
            return False
        
        if not (0 <= best_score <= 1):
            print(f"FAIL: Invalid best score {best_score}")
            return False
        
        if len(all_results) == 0:
            print("FAIL: No results returned")
            return False
        
        # Check if all results have required structure
        for i, result in enumerate(all_results):
            if 'best_val_acc' not in result:
                print(f"FAIL: Result {i} missing best_val_acc")
                return False
        
        print("PASS: Hyperparameter tuning completed successfully")
        print(f"   Trials completed: {len(all_results)}")
        print(f"   Best score: {best_score:.4f}")
        print(f"   Best config: {best_config}")
        return True
        
    except Exception as e:
        print(f"FAIL: Hyperparameter tuning error - {e}")
        return False

def test_results_saving(tuner):
    """Test saving tuning results"""
    print("\nTesting results saving...")
    
    try:
        # Save results (should have results from previous test)
        if not tuner.results:
            print("SKIP: No results to save")
            return True
        
        filename = 'test_hyperparameter_results.csv'
        df = tuner.save_tuning_results(filename)
        
        if df is None:
            print("FAIL: Failed to save results")
            return False
        
        # Check if file was created and has content
        import os
        if not os.path.exists(filename):
            print("FAIL: Results file was not created")
            return False
        
        if len(df) == 0:
            print("FAIL: Results dataframe is empty")
            return False
        
        # Clean up test file
        os.remove(filename)
        
        print("PASS: Results saved successfully")
        print(f"   Saved {len(df)} results")
        return True
        
    except Exception as e:
        print(f"FAIL: Results saving error - {e}")
        return False

def test_with_different_models():
    """Test hyperparameter tuner with different model architectures"""
    print("\nTesting with different model architectures...")
    
    models_to_test = [
        (Network, "Custom CNN"),
        (ResNetMultiModal, "ResNet18 MultiModal")
    ]
    
    try:
        # Create dummy data
        dataset = create_dummy_dataset(30)  # Very small dataset for speed
        train_loader = DataLoader(dataset, batch_size=4, shuffle=True)
        val_loader = DataLoader(dataset, batch_size=4, shuffle=False)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        for model_class, model_name in models_to_test:
            print(f"   Testing with {model_name}...")
            
            tuner = HyperparameterTuner(
                model_class=model_class,
                train_loader=train_loader,
                val_loader=val_loader,
                num_classes=3,
                device=device
            )
            
            # Test single config training
            config = {
                'learning_rate': 1e-3,
                'optimizer': 'adam',
                'weight_decay': 1e-5,
                'scheduler': 'none'
            }
            
            result = tuner.train_single_config(config, max_epochs=1, patience=2)
            
            if result['epochs_trained'] == 0:
                print(f"FAIL: {model_name} training failed")
                return False
            
            print(f"   PASS: {model_name} training successful")
        
        print("PASS: All model architectures work with hyperparameter tuner")
        return True
        
    except Exception as e:
        print(f"FAIL: Multi-model testing error - {e}")
        return False

def main():
    """Test hyperparameter tuner comprehensively"""
    print("Testing Hyperparameter Tuner")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: Initialization
    success, tuner, train_loader, val_loader, device = test_hyperparameter_tuner_initialization()
    test_results.append(("Initialization", success))
    
    if not success:
        print("\nCannot continue testing without successful initialization")
        return False
    
    # Test 2: Parameter grid creation
    success = test_parameter_grid_creation(tuner)
    test_results.append(("Parameter Grid Creation", success))
    
    # Test 3: Optimizer creation
    success = test_optimizer_creation(tuner)
    test_results.append(("Optimizer Creation", success))
    
    # Test 4: Scheduler creation
    success = test_scheduler_creation(tuner)
    test_results.append(("Scheduler Creation", success))
    
    # Test 5: Single configuration training
    success = test_single_config_training(tuner, train_loader, val_loader)
    test_results.append(("Single Config Training", success))
    
    # Test 6: Hyperparameter tuning
    success = test_hyperparameter_tuning(tuner)
    test_results.append(("Hyperparameter Tuning", success))
    
    # Test 7: Results saving
    success = test_results_saving(tuner)
    test_results.append(("Results Saving", success))
    
    # Test 8: Different model architectures
    success = test_with_different_models()
    test_results.append(("Multi-Model Testing", success))
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    percentage = (passed / total) * 100 if total > 0 else 0
    print(f"\nResults: {passed}/{total} tests passed ({percentage:.1f}%)")
    
    if percentage == 100:
        print("\nAll tests passed! Hyperparameter tuner is ready for use.")
    elif percentage >= 75:
        print("\nMost tests passed. Minor issues may need attention.")
    else:
        print("\nSeveral tests failed. Please review and fix issues.")
    
    return percentage == 100

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)