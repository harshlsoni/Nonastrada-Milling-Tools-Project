import os
import torch
import torch.nn as nn
import pandas as pd
import torch.optim as optim
import time
import matplotlib.pyplot as plt
import warnings
from concurrent.futures import ThreadPoolExecutor

from network_architecture import Network, ResNetMultiModal, EfficientNetMultiModal, MobileNetMultiModal, AlexNetMultiModal, VGG16MultiModal, N1MultiModal
from early_stopping import EarlyStopping

# Ignore warnings
warnings.filterwarnings('ignore')


class MultiTrainer:
    """
    Multi-model trainer for comparing different neural network architectures
    on multi-modal milling dataset classification tasks.
    """
    
    def __init__(self, train_loader, val_loader, num_classes, device, epochs=10, early_stopping_patience=10):
        """
        Initialize the MultiTrainer with data loaders and training parameters.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_classes (int): Number of classes for classification
            device: PyTorch device (cuda/cpu)
            epochs (int): Number of training epochs
            early_stopping_patience (int): Patience for early stopping
        """
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.num_classes = num_classes
        self.device = device
        self.epochs = epochs
        self.early_stopping_patience = early_stopping_patience
        self.results = {}
        
        # Initialize all models (all now have frozen CNN layers except last TWO blocks)
        self.models = {
            'Custom_CNN': Network(num_classes),  # Custom CNN unchanged
            'ResNet18_Last2Blocks': ResNetMultiModal(num_classes),
            'EfficientNet_Last2Blocks': EfficientNetMultiModal(num_classes),
            'MobileNet_Last2Blocks': MobileNetMultiModal(num_classes),
            'AlexNet_Last2Blocks': AlexNetMultiModal(num_classes),
            'VGG16_Last2Blocks': VGG16MultiModal(num_classes)
        }
        
        # Move models to device and setup optimizers
        self.optimizers = {}
        self.criterions = {}
        self.early_stoppers = {}
        
        for name, model in self.models.items():
            model.to(device)
            self.optimizers[name] = optim.Adam(model.parameters(), lr=1e-4)
            self.criterions[name] = nn.CrossEntropyLoss()
            self.early_stoppers[name] = EarlyStopping(patience=early_stopping_patience, verbose=True)
    
    def train_single_model(self, model_name):
        """Train a single model and return its results"""
        model = self.models[model_name]
        optimizer = self.optimizers[model_name]
        criterion = self.criterions[model_name]
        early_stopping = self.early_stoppers[model_name]
        
        train_losses, train_accs = [], []
        val_losses, val_accs = [], []
        training_times = []
        
        print(f"\n=== Training {model_name} ===")
        
        for epoch in range(self.epochs):
            start_time = time.time()
            
            # Training
            train_loss, train_acc = self._train_epoch(model, optimizer, criterion)
            
            # Validation
            val_loss, val_acc = self._evaluate_model(model, criterion)
            
            epoch_time = time.time() - start_time
            training_times.append(epoch_time)
            
            train_losses.append(train_loss)
            train_accs.append(train_acc)
            val_losses.append(val_loss)
            val_accs.append(val_acc)
            
            print(f"{model_name} - Epoch {epoch+1}/{self.epochs} | "
                  f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
                  f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f} | "
                  f"Time: {epoch_time:.2f}s")
            
            # Early stopping check
            early_stopping(val_loss, model)
            if early_stopping.early_stop:
                print(f"Early stopping triggered for {model_name} at epoch {epoch+1}")
                break
        
        return {
            'train_losses': train_losses,
            'train_accs': train_accs,
            'val_losses': val_losses,
            'val_accs': val_accs,
            'training_times': training_times,
            'total_time': sum(training_times),
            'best_val_acc': max(val_accs),
            'final_val_acc': val_accs[-1],
            'epochs_trained': len(train_losses),
            'early_stopped': early_stopping.early_stop
        }
    
    def _train_epoch(self, model, optimizer, criterion):
        """Train model for one epoch"""
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        
        for x_dict, image_labels, _, _ in self.train_loader:
            # Move data to device
            for key in x_dict:
                x_dict[key] = x_dict[key].to(self.device)
            image_labels = image_labels.to(self.device)
            
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
        
        return running_loss / len(self.train_loader), correct / total
    
    def _evaluate_model(self, model, criterion):
        """Evaluate model on validation set"""
        model.eval()
        running_loss, correct, total = 0.0, 0, 0
        
        with torch.no_grad():
            for x_dict, labels, _, _ in self.val_loader:
                for key in x_dict:
                    x_dict[key] = x_dict[key].to(self.device)
                labels = labels.to(self.device)
                
                outputs = model(x_dict)
                loss = criterion(outputs, labels)
                
                running_loss += loss.item()
                _, preds = torch.max(outputs, 1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
        
        return running_loss / len(self.val_loader), correct / total
    
    def train_all_parallel(self):
        """Train all models in parallel using threading"""
        print("Starting parallel training of all models...")
        print("WARNING: Parallel training may cause GPU memory issues.")
        print("   Consider using sequential training if you encounter CUDA out of memory errors.")
        start_time = time.time()
        
        # Use ThreadPoolExecutor for parallel training with reduced workers for GPU safety
        max_workers = min(2, len(self.models))  # Limit to 2 workers to prevent GPU memory issues
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.train_single_model, name): name 
                      for name in self.models.keys()}
            
            for future in futures:
                model_name = futures[future]
                try:
                    self.results[model_name] = future.result()
                    # Clear GPU cache after each model
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception as e:
                    print(f"Error training {model_name}: {e}")
                    # Clear GPU cache on error
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
        
        total_time = time.time() - start_time
        print(f"\nAll models trained in {total_time:.2f} seconds")
        
        return self.results
    
    def train_all_sequential(self):
        """Train all models sequentially"""
        print("Starting sequential training of all models...")
        start_time = time.time()
        
        for model_name in self.models.keys():
            self.results[model_name] = self.train_single_model(model_name)
        
        total_time = time.time() - start_time
        print(f"\nAll models trained in {total_time:.2f} seconds")
        
        return self.results
    
    def compare_results(self):
        """Compare and display results from all models"""
        if not self.results:
            print("No results to compare. Train models first.")
            return
        
        print("\n" + "="*80)
        print("MODEL COMPARISON RESULTS")
        print("="*80)
        
        # Create comparison table
        comparison_data = []
        for model_name, results in self.results.items():
            comparison_data.append({
                'Model': model_name,
                'Best Val Acc': f"{results['best_val_acc']:.4f}",
                'Final Val Acc': f"{results['final_val_acc']:.4f}",
                'Total Time (s)': f"{results['total_time']:.2f}",
                'Avg Time/Epoch (s)': f"{results['total_time']/self.epochs:.2f}"
            })
        
        # Sort by best validation accuracy
        comparison_data.sort(key=lambda x: float(x['Best Val Acc']), reverse=True)
        
        # Print table
        headers = ['Model', 'Best Val Acc', 'Final Val Acc', 'Total Time (s)', 'Avg Time/Epoch (s)']
        col_widths = [max(len(str(row[col])) for row in comparison_data + [dict(zip(headers, headers))]) 
                     for col in headers]
        
        # Print header
        header_row = " | ".join(f"{header:<{width}}" for header, width in zip(headers, col_widths))
        print(header_row)
        print("-" * len(header_row))
        
        # Print data rows
        for row in comparison_data:
            data_row = " | ".join(f"{row[col]:<{width}}" for col, width in zip(headers, col_widths))
            print(data_row)
        
        print("\n" + "="*80)
        
        # Find best model
        best_model = comparison_data[0]['Model']
        best_acc = comparison_data[0]['Best Val Acc']
        print(f"WINNER: {best_model} with {best_acc} validation accuracy")
        
        return comparison_data
    
    def plot_training_curves(self):
        """Plot training curves for all models"""
        if not self.results:
            print("No results to plot. Train models first.")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        for model_name, results in self.results.items():
            epochs_range = range(1, self.epochs + 1)
            
            # Training Loss
            ax1.plot(epochs_range, results['train_losses'], label=model_name, marker='o')
            ax1.set_title('Training Loss')
            ax1.set_xlabel('Epoch')
            ax1.set_ylabel('Loss')
            ax1.legend()
            ax1.grid(True)
            
            # Validation Loss
            ax2.plot(epochs_range, results['val_losses'], label=model_name, marker='s')
            ax2.set_title('Validation Loss')
            ax2.set_xlabel('Epoch')
            ax2.set_ylabel('Loss')
            ax2.legend()
            ax2.grid(True)
            
            # Training Accuracy
            ax3.plot(epochs_range, results['train_accs'], label=model_name, marker='^')
            ax3.set_title('Training Accuracy')
            ax3.set_xlabel('Epoch')
            ax3.set_ylabel('Accuracy')
            ax3.legend()
            ax3.grid(True)
            
            # Validation Accuracy
            ax4.plot(epochs_range, results['val_accs'], label=model_name, marker='d')
            ax4.set_title('Validation Accuracy')
            ax4.set_xlabel('Epoch')
            ax4.set_ylabel('Accuracy')
            ax4.legend()
            ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig('model_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("Training curves saved as 'model_comparison.png'")
    
    def save_detailed_results_to_csv(self):
        """Save detailed epoch-wise results to CSV files"""
        if not self.results:
            print("No results to save. Train models first.")
            return
        
        # Create results directory if it doesn't exist
        os.makedirs('training_results', exist_ok=True)
        
        # Save epoch-wise results for each model
        for model_name, results in self.results.items():
            epoch_data = []
            for epoch in range(self.epochs):
                epoch_data.append({
                    'Model': model_name,
                    'Epoch': epoch + 1,
                    'Train_Loss': results['train_losses'][epoch],
                    'Train_Accuracy': results['train_accs'][epoch],
                    'Val_Loss': results['val_losses'][epoch],
                    'Val_Accuracy': results['val_accs'][epoch],
                    'Epoch_Time_Seconds': results['training_times'][epoch]
                })
            
            # Save individual model results
            df_model = pd.DataFrame(epoch_data)
            csv_filename = f'training_results/{model_name}_detailed_results.csv'
            df_model.to_csv(csv_filename, index=False)
            print(f"Saved {model_name} detailed results to {csv_filename}")
        
        # Save combined results
        all_data = []
        for model_name, results in self.results.items():
            for epoch in range(self.epochs):
                all_data.append({
                    'Model': model_name,
                    'Epoch': epoch + 1,
                    'Train_Loss': results['train_losses'][epoch],
                    'Train_Accuracy': results['train_accs'][epoch],
                    'Val_Loss': results['val_losses'][epoch],
                    'Val_Accuracy': results['val_accs'][epoch],
                    'Epoch_Time_Seconds': results['training_times'][epoch]
                })
        
        df_combined = pd.DataFrame(all_data)
        combined_filename = 'training_results/all_models_detailed_results.csv'
        df_combined.to_csv(combined_filename, index=False)
        print(f"Saved combined detailed results to {combined_filename}")
        
        # Save summary results
        summary_data = []
        for model_name, results in self.results.items():
            summary_data.append({
                'Model': model_name,
                'Best_Val_Accuracy': results['best_val_acc'],
                'Final_Val_Accuracy': results['final_val_acc'],
                'Best_Train_Accuracy': max(results['train_accs']),
                'Final_Train_Accuracy': results['train_accs'][-1],
                'Min_Train_Loss': min(results['train_losses']),
                'Final_Train_Loss': results['train_losses'][-1],
                'Min_Val_Loss': min(results['val_losses']),
                'Final_Val_Loss': results['val_losses'][-1],
                'Total_Training_Time_Seconds': results['total_time'],
                'Average_Epoch_Time_Seconds': results['total_time'] / self.epochs,
                'Total_Parameters': sum(p.numel() for p in self.models[model_name].parameters()),
                'Trainable_Parameters': sum(p.numel() for p in self.models[model_name].parameters() if p.requires_grad)
            })
        
        df_summary = pd.DataFrame(summary_data)
        summary_filename = 'training_results/models_summary_results.csv'
        df_summary.to_csv(summary_filename, index=False)
        print(f"Saved summary results to {summary_filename}")
        
        return df_combined, df_summary
    
    def save_trained_models(self):
        """Save all trained models with their state dictionaries and metadata"""
        if not self.results:
            print("No trained models to save. Train models first.")
            return
        
        # Create models directory if it doesn't exist
        os.makedirs('saved_models', exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        for model_name, model in self.models.items():
            # Prepare model save data
            model_save_data = {
                'model_state_dict': model.state_dict(),
                'model_name': model_name,
                'num_classes': self.num_classes,
                'epochs_trained': self.epochs,
                'device': str(self.device),
                'optimizer_state_dict': self.optimizers[model_name].state_dict(),
                'training_results': self.results[model_name] if model_name in self.results else None,
                'timestamp': timestamp,
                'model_architecture': str(model)
            }
            
            # Save model
            model_filename = f'saved_models/{model_name}_{timestamp}.pth'
            torch.save(model_save_data, model_filename)
            print(f"Saved {model_name} to {model_filename}")
            
            # Save model architecture as text file
            arch_filename = f'saved_models/{model_name}_{timestamp}_architecture.txt'
            with open(arch_filename, 'w') as f:
                f.write(f"Model: {model_name}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Number of Classes: {self.num_classes}\n")
                f.write(f"Epochs Trained: {self.epochs}\n")
                f.write(f"Device: {self.device}\n")
                f.write(f"Total Parameters: {sum(p.numel() for p in model.parameters()):,}\n")
                f.write(f"Trainable Parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}\n")
                if model_name in self.results:
                    f.write(f"Best Validation Accuracy: {self.results[model_name]['best_val_acc']:.4f}\n")
                    f.write(f"Final Validation Accuracy: {self.results[model_name]['final_val_acc']:.4f}\n")
                f.write(f"\nModel Architecture:\n{str(model)}\n")
            
            print(f"Saved {model_name} architecture to {arch_filename}")
        
        # Create a loading script
        loading_script = f'''# Model Loading Script - Generated on {timestamp}
        import torch
        import torch.nn as nn
        from network_architecture import Network, ResNetMultiModal, EfficientNetMultiModal, MobileNetMultiModal

        def load_model(model_path, model_class, num_classes):
            """
            Load a saved model
            
            Args:
                model_path (str): Path to the saved model file
                model_class: The model class (e.g., ResNetMultiModal)
                num_classes (int): Number of classes
            
            Returns:
                model: Loaded model
                metadata: Model metadata
            """
            # Load the saved data
            checkpoint = torch.load(model_path, map_location='cpu')
            
            # Initialize the model
            model = model_class(num_classes)
            
            # Load the state dictionary
            model.load_state_dict(checkpoint['model_state_dict'])
            
            # Set to evaluation mode
            model.eval()
            
            print(f"Loaded model: {{checkpoint['model_name']}}")
            print(f"Trained for: {{checkpoint['epochs_trained']}} epochs")
            if checkpoint['training_results']:
                print(f"Best validation accuracy: {{checkpoint['training_results']['best_val_acc']:.4f}}")
            
            return model, checkpoint

        # Example usage:
        # model, metadata = load_model('saved_models/ResNet18_{timestamp}.pth', ResNetMultiModal, 3)
        '''
        
        script_filename = f'saved_models/load_models_{timestamp}.py'
        with open(script_filename, 'w') as f:
            f.write(loading_script)
        
        print(f"Created model loading script: {script_filename}")
        print(f"\nAll models saved in 'saved_models/' directory")
        print(f"All training results saved in 'training_results/' directory")
    
    def get_model_summary(self):
        """Get parameter count and model size for each model"""
        print("\n" + "="*60)
        print("MODEL ARCHITECTURE SUMMARY")
        print("="*60)
        
        for name, model in self.models.items():
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            
            print(f"\n{name}:")
            print(f"  Total Parameters: {total_params:,}")
            print(f"  Trainable Parameters: {trainable_params:,}")
            print(f"  Model Size (MB): {total_params * 4 / (1024**2):.2f}")
    
    def add_custom_model(self, model_name, model_instance, learning_rate=1e-4):
        """
        Add a custom model to the trainer
        
        Args:
            model_name (str): Name for the model
            model_instance: Initialized model instance
            learning_rate (float): Learning rate for the optimizer
        """
        self.models[model_name] = model_instance.to(self.device)
        self.optimizers[model_name] = optim.Adam(model_instance.parameters(), lr=learning_rate)
        self.criterions[model_name] = nn.CrossEntropyLoss()
        print(f"Added custom model: {model_name}")
    
    def remove_model(self, model_name):
        """Remove a model from the trainer"""
        if model_name in self.models:
            del self.models[model_name]
            del self.optimizers[model_name]
            del self.criterions[model_name]
            if model_name in self.results:
                del self.results[model_name]
            print(f"Removed model: {model_name}")
        else:
            print(f"Model {model_name} not found")
    
    def get_best_model(self):
        """Get the best performing model based on validation accuracy"""
        if not self.results:
            print("No results available. Train models first.")
            return None
        
        best_model_name = max(self.results.keys(), 
                             key=lambda x: self.results[x]['best_val_acc'])
        best_model = self.models[best_model_name]
        best_results = self.results[best_model_name]
        
        print(f"Best model: {best_model_name}")
        print(f"   Best validation accuracy: {best_results['best_val_acc']:.4f}")
        print(f"   Training time: {best_results['total_time']:.2f}s")
        
        return best_model, best_model_name, best_results
    
    def tune_best_model_hyperparameters(self, max_trials=20, max_epochs=50, patience=15):
        """
        Perform hyperparameter tuning on the best performing model
        
        Args:
            max_trials: Maximum number of hyperparameter configurations to try
            max_epochs: Maximum epochs per configuration
            patience: Early stopping patience for hyperparameter tuning
            
        Returns:
            Best hyperparameter configuration and results
        """
        if not self.results:
            print("No results available. Train models first.")
            return None
        
        # Get the best model
        _, best_model_name, _ = self.get_best_model()
        
        print(f"\nStarting hyperparameter tuning for {best_model_name}...")
        print("="*60)
        
        # Import hyperparameter tuner
        from Code.Model_Files.hyperparameter_tuner import HyperparameterTuner
        
        # Get the model class
        model_class_map = {
            'Custom_CNN': Network,
            'ResNet18_Last2Blocks': ResNetMultiModal,
            'EfficientNet_Last2Blocks': EfficientNetMultiModal,
            'MobileNet_Last2Blocks': MobileNetMultiModal,
            'AlexNet_Last2Blocks': AlexNetMultiModal,
            'VGG16_Last2Blocks': VGG16MultiModal
        }
        
        model_class = model_class_map[best_model_name]
        
        # Initialize tuner
        tuner = HyperparameterTuner(
            model_class=model_class,
            train_loader=self.train_loader,
            val_loader=self.val_loader,
            num_classes=self.num_classes,
            device=self.device
        )
        
        # Perform hyperparameter tuning
        best_config, best_score, all_results = tuner.tune_hyperparameters(
            max_trials=max_trials,
            max_epochs=max_epochs,
            patience=patience
        )
        
        # Save results
        tuning_df = tuner.save_tuning_results(f'{best_model_name}_hyperparameter_tuning_results.csv')
        
        print(f"\nHYPERPARAMETER TUNING COMPLETE!")
        print("="*60)
        print(f"Best model: {best_model_name}")
        print(f"Best configuration: {best_config}")
        print(f"Best validation accuracy: {best_score:.4f}")
        print(f"Results saved to: {best_model_name}_hyperparameter_tuning_results.csv")
        
        return best_config, best_score, all_results, tuning_df