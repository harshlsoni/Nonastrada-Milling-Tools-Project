#!/usr/bin/env python3
"""
VGG16 MultiModal Training with Hyperparameter Tuning

This script focuses on training and optimizing the VGG16 architecture
for the multimodal milling dataset with comprehensive hyperparameter tuning.
"""

import os
import torch
import warnings
import time
import pandas as pd
from torch.utils.data import DataLoader, random_split

from MultiModalMillingDataset import MultiModalMillingDataset
from network_architecture import VGG16MultiModal
from hyperparameter_tuner import HyperparameterTuner
from early_stopping import EarlyStopping

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


def setup_data_loaders(data_dir="Files", batch_size=16, train_split=0.8):
    """Setup data loaders for training and validation"""
    print("Setting up data loaders...")
    
    # Load dataset
    data = MultiModalMillingDataset(
        data_dir, 
        os.path.join(data_dir, "labels.csv"), 
        os.path.join(data_dir, "labels_reg.csv")
    )
    
    print(f"Dataset loaded: {len(data)} samples")
    print(f"Dataset info: {data.get_dataset_info()}")
    
    # Train/Validation split
    train_size = int(train_split * len(data))
    val_size = len(data) - train_size
    train_dataset, val_dataset = random_split(data, [train_size, val_size])
    
    print(f"Training samples: {train_size}")
    print(f"Validation samples: {val_size}")
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader, data.get_dataset_info()


def train_baseline_vgg16(train_loader, val_loader, num_classes, device, epochs=30):
    """Train a baseline VGG16 model for comparison"""
    print("\n" + "="*60)
    print("TRAINING BASELINE VGG16 MODEL")
    print("="*60)
    
    # Initialize model
    model = VGG16MultiModal(num_classes).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    criterion = torch.nn.CrossEntropyLoss()
    early_stopping = EarlyStopping(patience=10, verbose=True)
    
    # Training metrics
    train_losses, train_accs = [], []
    val_losses, val_accs = [], []
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
    
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_start = time.time()
        
        # Training phase
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        
        for x_dict, image_labels, _, _ in train_loader:
            # Move data to device
            for key in x_dict:
                x_dict[key] = x_dict[key].to(device)
            image_labels = image_labels.to(device)
            
            # Forward pass
            outputs = model(x_dict)
            loss = criterion(outputs, image_labels)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Metrics
            running_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            correct += (preds == image_labels).sum().item()
            total += image_labels.size(0)
        
        train_loss = running_loss / len(train_loader)
        train_acc = correct / total
        
        # Validation phase
        model.eval()
        running_loss, correct, total = 0.0, 0, 0
        
        with torch.no_grad():
            for x_dict, labels, _, _ in val_loader:
                for key in x_dict:
                    x_dict[key] = x_dict[key].to(device)
                labels = labels.to(device)
                
                outputs = model(x_dict)
                loss = criterion(outputs, labels)
                
                running_loss += loss.item()
                _, preds = torch.max(outputs, 1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
        
        val_loss = running_loss / len(val_loader)
        val_acc = correct / total
        
        # Store metrics
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        
        epoch_time = time.time() - epoch_start
        
        print(f"Epoch {epoch+1:2d}/{epochs} | "
              f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | "
              f"Time: {epoch_time:.2f}s")
        
        # Early stopping check
        early_stopping(val_loss, model)
        if early_stopping.early_stop:
            print(f"Early stopping triggered at epoch {epoch+1}")
            break
    
    total_time = time.time() - start_time
    best_val_acc = max(val_accs)
    
    print(f"\nBaseline Training Complete!")
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    print(f"Total training time: {total_time:.2f}s")
    print(f"Epochs trained: {len(train_losses)}")
    
    return {
        'model': model,
        'best_val_acc': best_val_acc,
        'final_val_acc': val_accs[-1],
        'train_losses': train_losses,
        'train_accs': train_accs,
        'val_losses': val_losses,
        'val_accs': val_accs,
        'total_time': total_time,
        'epochs_trained': len(train_losses)
    }


def run_hyperparameter_tuning(train_loader, val_loader, num_classes, device, 
                             max_trials=20, max_epochs=30, patience=10):
    """Run comprehensive hyperparameter tuning for VGG16"""
    print("\n" + "="*60)
    print("STARTING VGG16 HYPERPARAMETER TUNING")
    print("="*60)
    
    # Initialize hyperparameter tuner
    tuner = HyperparameterTuner(
        model_class=VGG16MultiModal,
        train_loader=train_loader,
        val_loader=val_loader,
        num_classes=num_classes,
        device=device
    )
    
    print(f"Configuration:")
    print(f"  Max trials: {max_trials}")
    print(f"  Max epochs per trial: {max_epochs}")
    print(f"  Early stopping patience: {patience}")
    
    # Run hyperparameter tuning
    start_time = time.time()
    best_config, best_score, all_results = tuner.tune_hyperparameters(
        max_trials=max_trials,
        max_epochs=max_epochs,
        patience=patience
    )
    tuning_time = time.time() - start_time
    
    print(f"\nHyperparameter tuning completed in {tuning_time:.2f}s")
    print(f"Trials completed: {len(all_results)}")
    print(f"Best validation accuracy: {best_score:.4f}")
    print(f"Best configuration: {best_config}")
    
    # Save detailed results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_filename = f'vgg16_hyperparameter_tuning_{timestamp}.csv'
    tuning_df = tuner.save_tuning_results(results_filename)
    
    return {
        'best_config': best_config,
        'best_score': best_score,
        'all_results': all_results,
        'tuning_time': tuning_time,
        'results_df': tuning_df,
        'results_filename': results_filename
    }


def train_optimized_vgg16(train_loader, val_loader, num_classes, device, 
                         best_config, max_epochs=50):
    """Train VGG16 with the best hyperparameters found"""
    print("\n" + "="*60)
    print("TRAINING OPTIMIZED VGG16 MODEL")
    print("="*60)
    print(f"Using best configuration: {best_config}")
    
    # Initialize model with best configuration
    model = VGG16MultiModal(num_classes).to(device)
    
    # Setup optimizer with best parameters
    if best_config['optimizer'] == 'adam':
        optimizer = torch.optim.Adam(
            model.parameters(), 
            lr=best_config['learning_rate'],
            weight_decay=best_config['weight_decay']
        )
    elif best_config['optimizer'] == 'sgd':
        optimizer = torch.optim.SGD(
            model.parameters(), 
            lr=best_config['learning_rate'],
            weight_decay=best_config['weight_decay'],
            momentum=0.9
        )
    elif best_config['optimizer'] == 'adamw':
        optimizer = torch.optim.AdamW(
            model.parameters(), 
            lr=best_config['learning_rate'],
            weight_decay=best_config['weight_decay']
        )
    
    # Setup scheduler if specified
    scheduler = None
    if best_config['scheduler'] == 'step':
        scheduler_params = best_config.get('scheduler_params', {'step_size': 10, 'gamma': 0.1})
        scheduler = torch.optim.lr_scheduler.StepLR(
            optimizer, 
            step_size=scheduler_params['step_size'],
            gamma=scheduler_params['gamma']
        )
    elif best_config['scheduler'] == 'cosine':
        scheduler_params = best_config.get('scheduler_params', {'T_max': 50})
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=scheduler_params['T_max']
        )
    
    criterion = torch.nn.CrossEntropyLoss()
    early_stopping = EarlyStopping(patience=15, verbose=True)
    
    # Training metrics
    train_losses, train_accs = [], []
    val_losses, val_accs = [], []
    
    start_time = time.time()
    
    for epoch in range(max_epochs):
        epoch_start = time.time()
        
        # Training phase
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        
        for x_dict, image_labels, _, _ in train_loader:
            # Move data to device
            for key in x_dict:
                x_dict[key] = x_dict[key].to(device)
            image_labels = image_labels.to(device)
            
            # Forward pass
            outputs = model(x_dict)
            loss = criterion(outputs, image_labels)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Metrics
            running_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            correct += (preds == image_labels).sum().item()
            total += image_labels.size(0)
        
        train_loss = running_loss / len(train_loader)
        train_acc = correct / total
        
        # Validation phase
        model.eval()
        running_loss, correct, total = 0.0, 0, 0
        
        with torch.no_grad():
            for x_dict, labels, _, _ in val_loader:
                for key in x_dict:
                    x_dict[key] = x_dict[key].to(device)
                labels = labels.to(device)
                
                outputs = model(x_dict)
                loss = criterion(outputs, labels)
                
                running_loss += loss.item()
                _, preds = torch.max(outputs, 1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
        
        val_loss = running_loss / len(val_loader)
        val_acc = correct / total
        
        # Store metrics
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        
        # Learning rate scheduling
        if scheduler is not None:
            scheduler.step()
        
        epoch_time = time.time() - epoch_start
        
        print(f"Epoch {epoch+1:2d}/{max_epochs} | "
              f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | "
              f"Time: {epoch_time:.2f}s")
        
        # Early stopping check
        early_stopping(val_loss, model)
        if early_stopping.early_stop:
            print(f"Early stopping triggered at epoch {epoch+1}")
            break
    
    total_time = time.time() - start_time
    best_val_acc = max(val_accs)
    
    print(f"\nOptimized Training Complete!")
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    print(f"Total training time: {total_time:.2f}s")
    print(f"Epochs trained: {len(train_losses)}")
    
    return {
        'model': model,
        'best_val_acc': best_val_acc,
        'final_val_acc': val_accs[-1],
        'train_losses': train_losses,
        'train_accs': train_accs,
        'val_losses': val_losses,
        'val_accs': val_accs,
        'total_time': total_time,
        'epochs_trained': len(train_losses),
        'config': best_config
    }


def save_results(baseline_results, tuning_results, optimized_results):
    """Save all results to files"""
    print("\n" + "="*60)
    print("SAVING RESULTS")
    print("="*60)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Create results directory
    os.makedirs('vgg16_results', exist_ok=True)
    
    # Save comparison results
    comparison_data = {
        'Model': ['VGG16_Baseline', 'VGG16_Optimized'],
        'Best_Val_Accuracy': [baseline_results['best_val_acc'], optimized_results['best_val_acc']],
        'Final_Val_Accuracy': [baseline_results['final_val_acc'], optimized_results['final_val_acc']],
        'Training_Time_Seconds': [baseline_results['total_time'], optimized_results['total_time']],
        'Epochs_Trained': [baseline_results['epochs_trained'], optimized_results['epochs_trained']]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_filename = f'vgg16_results/vgg16_comparison_{timestamp}.csv'
    comparison_df.to_csv(comparison_filename, index=False)
    print(f"Comparison results saved to: {comparison_filename}")
    
    # Save detailed training history
    detailed_data = []
    
    # Baseline results
    for epoch in range(len(baseline_results['train_losses'])):
        detailed_data.append({
            'Model': 'VGG16_Baseline',
            'Epoch': epoch + 1,
            'Train_Loss': baseline_results['train_losses'][epoch],
            'Train_Accuracy': baseline_results['train_accs'][epoch],
            'Val_Loss': baseline_results['val_losses'][epoch],
            'Val_Accuracy': baseline_results['val_accs'][epoch]
        })
    
    # Optimized results
    for epoch in range(len(optimized_results['train_losses'])):
        detailed_data.append({
            'Model': 'VGG16_Optimized',
            'Epoch': epoch + 1,
            'Train_Loss': optimized_results['train_losses'][epoch],
            'Train_Accuracy': optimized_results['train_accs'][epoch],
            'Val_Loss': optimized_results['val_losses'][epoch],
            'Val_Accuracy': optimized_results['val_accs'][epoch]
        })
    
    detailed_df = pd.DataFrame(detailed_data)
    detailed_filename = f'vgg16_results/vgg16_training_history_{timestamp}.csv'
    detailed_df.to_csv(detailed_filename, index=False)
    print(f"Training history saved to: {detailed_filename}")
    
    # Save optimized model
    model_filename = f'vgg16_results/vgg16_optimized_model_{timestamp}.pth'
    torch.save({
        'model_state_dict': optimized_results['model'].state_dict(),
        'config': optimized_results['config'],
        'best_val_acc': optimized_results['best_val_acc'],
        'training_history': {
            'train_losses': optimized_results['train_losses'],
            'train_accs': optimized_results['train_accs'],
            'val_losses': optimized_results['val_losses'],
            'val_accs': optimized_results['val_accs']
        }
    }, model_filename)
    print(f"Optimized model saved to: {model_filename}")
    
    return {
        'comparison_file': comparison_filename,
        'detailed_file': detailed_filename,
        'model_file': model_filename
    }


def main():
    """Main training pipeline for VGG16 hyperparameter tuning"""
    print("VGG16 MultiModal Training with Hyperparameter Tuning")
    print("="*60)
    
    # Configuration
    config = {
        'data_dir': 'Files',
        'batch_size': 16,
        'train_split': 0.8,
        'baseline_epochs': 30,
        'tuning_max_trials': 15,
        'tuning_max_epochs': 25,
        'tuning_patience': 8,
        'final_max_epochs': 50
    }
    
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nUsing device: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name()}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    try:
        # Setup data loaders
        train_loader, val_loader, dataset_info = setup_data_loaders(
            config['data_dir'], 
            config['batch_size'], 
            config['train_split']
        )
        num_classes = dataset_info['num_classes']
        
        # Step 1: Train baseline VGG16
        baseline_results = train_baseline_vgg16(
            train_loader, val_loader, num_classes, device, 
            epochs=config['baseline_epochs']
        )
        
        # Step 2: Hyperparameter tuning
        tuning_results = run_hyperparameter_tuning(
            train_loader, val_loader, num_classes, device,
            max_trials=config['tuning_max_trials'],
            max_epochs=config['tuning_max_epochs'],
            patience=config['tuning_patience']
        )
        
        # Step 3: Train optimized model
        optimized_results = train_optimized_vgg16(
            train_loader, val_loader, num_classes, device,
            tuning_results['best_config'],
            max_epochs=config['final_max_epochs']
        )
        
        # Step 4: Save results
        saved_files = save_results(baseline_results, tuning_results, optimized_results)
        
        # Final summary
        print("\n" + "="*60)
        print("FINAL RESULTS SUMMARY")
        print("="*60)
        print(f"Baseline VGG16:")
        print(f"  Best validation accuracy: {baseline_results['best_val_acc']:.4f}")
        print(f"  Training time: {baseline_results['total_time']:.2f}s")
        print(f"  Epochs trained: {baseline_results['epochs_trained']}")
        
        print(f"\nHyperparameter Tuning:")
        print(f"  Trials completed: {len(tuning_results['all_results'])}")
        print(f"  Best score found: {tuning_results['best_score']:.4f}")
        print(f"  Tuning time: {tuning_results['tuning_time']:.2f}s")
        print(f"  Best config: {tuning_results['best_config']}")
        
        print(f"\nOptimized VGG16:")
        print(f"  Best validation accuracy: {optimized_results['best_val_acc']:.4f}")
        print(f"  Training time: {optimized_results['total_time']:.2f}s")
        print(f"  Epochs trained: {optimized_results['epochs_trained']}")
        
        improvement = optimized_results['best_val_acc'] - baseline_results['best_val_acc']
        print(f"\nImprovement: {improvement:+.4f} ({improvement/baseline_results['best_val_acc']*100:+.2f}%)")
        
        print(f"\nFiles saved:")
        for key, filename in saved_files.items():
            print(f"  {key}: {filename}")
        
        print("\nVGG16 hyperparameter tuning completed successfully!")
        
    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)