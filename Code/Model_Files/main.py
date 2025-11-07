import os
import torch
import torch.nn as nn
import torch.optim as optim
import warnings
import time
import matplotlib.pyplot as plt
import pandas as pd
from torch.utils.data import DataLoader, random_split
from Code.Model_Files.MultiModalMillingDataset import MultiModalMillingDataset
from network_architecture.vgg16_multimodal import VGG16MultiModal
from early_stopping import EarlyStopping

# Ignore warnings
warnings.filterwarnings('ignore')


def train_epoch(model, train_loader, optimizer, criterion, device):
    """Train model for one epoch"""
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
    
    return running_loss / len(train_loader), correct / total


def evaluate_model(model, val_loader, criterion, device):
    """Evaluate model on validation set"""
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
    
    return running_loss / len(val_loader), correct / total


if __name__ == "__main__":
    # Load dataset
    data = MultiModalMillingDataset("Files", 
                                   os.path.join("Files", "labels.csv"), 
                                   os.path.join("Files", "labels_reg.csv"))
    
    # Train/Validation split
    train_size = int(0.8 * len(data))   # 80% training
    val_size = len(data) - train_size
    train_dataset, val_dataset = random_split(data, [train_size, val_size])

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Initialize MobileNet model
    model = VGG16MultiModal(num_classes=3, pretrained=True).to(device)
    
    # Training parameters
    epochs = 20
    learning_rate = 0.001
    early_stopping_patience = 4
    
    # Initialize optimizer, criterion, and early stopping
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()
    early_stopping = EarlyStopping(patience=early_stopping_patience, verbose=True)
    
    # Training tracking
    train_losses, train_accs = [], []
    val_losses, val_accs = [], []
    training_times = []
    
    print(f"\n=== Training VGG16 MultiModal Model ===")
    print(f"Epochs: {epochs}")
    print(f"Learning Rate: {learning_rate}")
    print(f"Early Stopping Patience: {early_stopping_patience}")
    print(f"Batch Size: 16")
    print("="*50)
    
    # Training loop
    for epoch in range(epochs):
        start_time = time.time()
        
        # Training
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device)
        
        # Validation
        val_loss, val_acc = evaluate_model(model, val_loader, criterion, device)
        
        epoch_time = time.time() - start_time
        training_times.append(epoch_time)
        
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        
        print(f"Epoch {epoch+1}/{epochs} | "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f} | "
              f"Time: {epoch_time:.2f}s")
        
        # Early stopping check
        early_stopping(val_loss, model)
        if early_stopping.early_stop:
            print(f"Early stopping triggered at epoch {epoch+1}")
            break
    
    # Training results
    results = {
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
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Best Validation Accuracy: {results['best_val_acc']:.4f}")
    print(f"Final Validation Accuracy: {results['final_val_acc']:.4f}")
    print(f"Total Training Time: {results['total_time']:.2f}s")
    print(f"Epochs Trained: {results['epochs_trained']}/{epochs}")
    if results['early_stopped']:
        print("Training stopped early due to no improvement")
    print("="*60)
    
    # Plot training curves
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.title('MobileNet Model - Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    plt.plot(train_accs, label='Train Acc')
    plt.plot(val_accs, label='Val Acc')
    plt.title('VGG16 Model - Training Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('vgg16_curves.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Save results to CSV
    results_df = pd.DataFrame({
        'epoch': range(1, len(train_losses) + 1),
        'train_loss': train_losses,
        'train_acc': train_accs,
        'val_loss': val_losses,
        'val_acc': val_accs,
        'epoch_time': training_times
    })
    
    results_df.to_csv('Vgg16.csv', index=False)
    print(f"\nTraining results saved to 'vgg16.csv'")
    
    # Save trained model
    os.makedirs('saved_models', exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'results': results,
        'model_config': {
            'num_classes': 3,
            'learning_rate': learning_rate,
            'epochs': epochs
        }
    }, 'saved_models/Vgg16.pth')
    
    print(f"Model saved to 'saved_models/n1_model.pth'")
    print(f"Training curves saved to 'n1_model_training_curves.png'")