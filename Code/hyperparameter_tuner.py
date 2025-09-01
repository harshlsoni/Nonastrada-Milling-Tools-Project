import torch
import torch.nn as nn
import torch.optim as optim
import itertools
import pandas as pd
import time
from early_stopping import EarlyStopping


class HyperparameterTuner:
    """
    Hyperparameter tuning utility for neural networks
    """
    
    def __init__(self, model_class, train_loader, val_loader, num_classes, device):
        """
        Initialize the hyperparameter tuner
        
        Args:
            model_class: The model class to tune
            train_loader: Training data loader
            val_loader: Validation data loader
            num_classes: Number of classes
            device: PyTorch device
        """
        self.model_class = model_class
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.num_classes = num_classes
        self.device = device
        self.results = []
    
    def create_param_grid(self):
        """
        Create a comprehensive parameter grid for hyperparameter tuning
        """
        param_grid = {
            'learning_rate': [1e-5, 5e-5, 1e-4, 5e-4, 1e-3],
            'batch_size': [8, 16, 32],  # Note: This would require recreating data loaders
            'optimizer': ['adam', 'sgd', 'adamw'],
            'weight_decay': [0, 1e-5, 1e-4, 1e-3],
            'dropout_rate': [0.3, 0.5, 0.7],  # For models that support it
            'scheduler': ['none', 'step', 'cosine'],
            'scheduler_params': {
                'step': {'step_size': [10, 20], 'gamma': [0.1, 0.5]},
                'cosine': {'T_max': [50, 100]}
            }
        }
        return param_grid
    
    def get_optimizer(self, model, optimizer_name, learning_rate, weight_decay):
        """Get optimizer based on name and parameters"""
        if optimizer_name == 'adam':
            return optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
        elif optimizer_name == 'sgd':
            return optim.SGD(model.parameters(), lr=learning_rate, weight_decay=weight_decay, momentum=0.9)
        elif optimizer_name == 'adamw':
            return optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
        else:
            raise ValueError(f"Unknown optimizer: {optimizer_name}")
    
    def get_scheduler(self, optimizer, scheduler_name, scheduler_params=None):
        """Get learning rate scheduler"""
        if scheduler_name == 'none':
            return None
        elif scheduler_name == 'step':
            step_size = scheduler_params.get('step_size', 10)
            gamma = scheduler_params.get('gamma', 0.1)
            return optim.lr_scheduler.StepLR(optimizer, step_size=step_size, gamma=gamma)
        elif scheduler_name == 'cosine':
            T_max = scheduler_params.get('T_max', 50)
            return optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=T_max)
        else:
            raise ValueError(f"Unknown scheduler: {scheduler_name}")
    
    def train_single_config(self, config, max_epochs=50, patience=10):
        """
        Train a single configuration
        
        Args:
            config: Dictionary containing hyperparameters
            max_epochs: Maximum number of epochs
            patience: Early stopping patience
            
        Returns:
            Dictionary with training results
        """
        print(f"\n🔧 Training config: {config}")
        
        # Initialize model
        model = self.model_class(self.num_classes).to(self.device)
        
        # Get optimizer
        optimizer = self.get_optimizer(
            model, 
            config['optimizer'], 
            config['learning_rate'], 
            config['weight_decay']
        )
        
        # Get scheduler
        scheduler = self.get_scheduler(
            optimizer, 
            config['scheduler'], 
            config.get('scheduler_params', {})
        )
        
        # Loss function
        criterion = nn.CrossEntropyLoss()
        
        # Early stopping
        early_stopping = EarlyStopping(patience=patience, verbose=False)
        
        # Training loop
        train_losses, train_accs = [], []
        val_losses, val_accs = [], []
        start_time = time.time()
        
        for epoch in range(max_epochs):
            # Training
            train_loss, train_acc = self._train_epoch(model, optimizer, criterion)
            
            # Validation
            val_loss, val_acc = self._evaluate_model(model, criterion)
            
            train_losses.append(train_loss)
            train_accs.append(train_acc)
            val_losses.append(val_loss)
            val_accs.append(val_acc)
            
            # Learning rate scheduling
            if scheduler is not None:
                scheduler.step()
            
            # Early stopping check
            early_stopping(val_loss, model)
            if early_stopping.early_stop:
                print(f"Early stopping at epoch {epoch+1}")
                break
        
        training_time = time.time() - start_time
        
        return {
            'config': config,
            'train_losses': train_losses,
            'train_accs': train_accs,
            'val_losses': val_losses,
            'val_accs': val_accs,
            'best_val_acc': max(val_accs),
            'final_val_acc': val_accs[-1],
            'best_val_loss': min(val_losses),
            'epochs_trained': len(train_losses),
            'training_time': training_time,
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
    
    def tune_hyperparameters(self, max_trials=20, max_epochs=50, patience=10):
        """
        Perform hyperparameter tuning using grid search with random sampling
        
        Args:
            max_trials: Maximum number of configurations to try
            max_epochs: Maximum epochs per configuration
            patience: Early stopping patience
            
        Returns:
            Best configuration and results
        """
        param_grid = self.create_param_grid()
        
        # Generate all possible combinations (excluding scheduler_params for now)
        base_params = {k: v for k, v in param_grid.items() if k != 'scheduler_params'}
        
        # Create parameter combinations
        keys = base_params.keys()
        values = base_params.values()
        combinations = list(itertools.product(*values))
        
        # Randomly sample configurations if too many
        if len(combinations) > max_trials:
            import random
            combinations = random.sample(combinations, max_trials)
        
        print(f"🎯 Starting hyperparameter tuning with {len(combinations)} configurations...")
        
        best_config = None
        best_score = 0
        
        for i, combo in enumerate(combinations):
            config = dict(zip(keys, combo))
            
            # Add scheduler parameters if needed
            if config['scheduler'] in param_grid['scheduler_params']:
                scheduler_options = param_grid['scheduler_params'][config['scheduler']]
                # Take first option for simplicity, could be randomized
                config['scheduler_params'] = {k: v[0] for k, v in scheduler_options.items()}
            
            print(f"\n📊 Trial {i+1}/{len(combinations)}")
            
            try:
                result = self.train_single_config(config, max_epochs, patience)
                self.results.append(result)
                
                if result['best_val_acc'] > best_score:
                    best_score = result['best_val_acc']
                    best_config = config
                    print(f"🏆 New best score: {best_score:.4f}")
                
            except Exception as e:
                print(f"❌ Error in trial {i+1}: {e}")
                continue
        
        return best_config, best_score, self.results
    
    def save_tuning_results(self, filename='hyperparameter_tuning_results.csv'):
        """Save hyperparameter tuning results to CSV"""
        if not self.results:
            print("No results to save")
            return
        
        # Flatten results for CSV
        flattened_results = []
        for result in self.results:
            row = {
                'best_val_acc': result['best_val_acc'],
                'final_val_acc': result['final_val_acc'],
                'best_val_loss': result['best_val_loss'],
                'epochs_trained': result['epochs_trained'],
                'training_time': result['training_time'],
                'early_stopped': result['early_stopped']
            }
            # Add config parameters
            row.update(result['config'])
            flattened_results.append(row)
        
        df = pd.DataFrame(flattened_results)
        df = df.sort_values('best_val_acc', ascending=False)
        df.to_csv(filename, index=False)
        print(f"✅ Hyperparameter tuning results saved to {filename}")
        
        return df