import os
import torch
import torch.nn as nn
import scipy.io as sio
import pandas as pd
from torch.utils.data import Dataset, DataLoader,random_split
from PIL import Image
from sklearn.preprocessing import LabelEncoder
import torchvision.transforms as transforms
import torch.optim as optim
import torchvision.models as models
import torch.nn.functional as F
import time
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
import threading

class MultiModalMillingDataset(Dataset):
    def __init__(self, root_dir, labels_csv, labels_reg_csv,  transform=None):
        """
        Args:
            root_dir (str): Path to dataset folder
            labels_csv (str): Path to classification labels CSV
            labels_reg_csv (str): Path to regression labels CSV
            mat_file (str): Path to raw force .mat file
            transform (callable, optional): Optional transform to be applied on images
        """
        self.root_dir = root_dir
        self.labels = pd.read_csv(labels_csv)
        self.label_encoder = LabelEncoder()
        self.labels["encoded"] = self.label_encoder.fit_transform(self.labels.iloc[:, 1])
        self.reg_labels = pd.read_csv(labels_reg_csv)
        
        self.transform = transform if transform else transforms.Compose([
        transforms.Resize((224, 224)),   # make all images 224x224
        transforms.ToTensor(),
    ])

        # store paths for different modalities
        self.modalities = {
            "chip": os.path.join(root_dir, "chip"),
            "scalx": os.path.join(root_dir, "scal", "x"),
            "scaly": os.path.join(root_dir, "scal", "y"),
            "scalz": os.path.join(root_dir, "scal", "z"),
            "specx": os.path.join(root_dir, "spec", "x"),
            "specy": os.path.join(root_dir, "spec", "y"),
            "specz" : os.path.join(root_dir,"spec","z"),
            "tool": os.path.join(root_dir, "tool"),
            "work": os.path.join(root_dir, "work")
        }

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        # classification & regression labels
        image_label = torch.tensor(self.labels.iloc[idx]["encoded"], dtype=torch.long)  # assuming 2nd column is label
        tool_label = torch.tensor(self.labels.iloc[idx]["tool_label"], dtype=torch.long)
        flank_wear = torch.tensor(self.reg_labels.iloc[idx]["flank_wear"], dtype=torch.float)

        row = self.labels.iloc[idx]
        file_name = row["id"]
        # load images from modalities
        sample = {}
        for modality, path in self.modalities.items():
            if modality in ["scalx", "scaly", "scalz", "work"]:
                ext = ".png"
            else:
                ext = ".jpg"

            img_path = os.path.join(path, file_name + ext)

            if not os.path.exists(img_path):
                sample[modality] = torch.zeros(3, 224, 224)

            img = Image.open(img_path).convert("RGB")
            img = self.transform(img)
            sample[modality] = img

        # add force signals (if needed per sample)
        # Example: force_data['forces'][idx] -> adjust key according to .mat file structure
        # sample['force'] = torch.tensor(self.force_data['forces'][idx], dtype=torch.float)

        return sample, image_label,tool_label, flank_wear



class Network(nn.Module):
    def __init__(self,num_classes : int):
        super(Network,self).__init__()

        self.cnnLayer = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, padding=1),  # -> [B, 32, 224, 224]
            nn.MaxPool2d(kernel_size=2, stride=2),                                # -> [B, 32, 112, 112]

            nn.Conv2d(32, 64, kernel_size=3, padding=1),                          # -> [B, 64, 112, 112]
            nn.MaxPool2d(2, 2),                                                   # -> [B, 64, 56, 56]

            nn.Conv2d(64, 128, kernel_size=3, padding=1),                         # -> [B, 128, 56, 56]
            nn.MaxPool2d(2, 2) 
        )

        dummy = torch.randn(1, 3, 224, 224)   # match your dataset input size
        with torch.no_grad():
            out = self.cnnLayer(dummy)
        self.flatten_size = out.view(1, -1).size(1)

        self.fc = nn.Sequential(
        nn.Linear(9 * self.flatten_size, 256),
        nn.ReLU(),
        nn.Linear(256, num_classes),
        nn.Softmax(dim=1)
        )

        

    def forward(self,x_dict):
        features = []
        for _, x in x_dict.items():
            feat = self.cnnLayer(x) 
            feat = feat.view(feat.size(0), -1)
            features.append(feat)

        
        fused = torch.cat(features, dim=1)  # concatenate along feature dimension
        out = self.fc(fused)
        return out


class ResNetMultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(ResNetMultiModal, self).__init__()
        
        # Load pretrained ResNet18 and remove final classification layer
        self.backbone = models.resnet18(pretrained=pretrained)
        self.feature_dim = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()  # Remove final FC layer
        
        # Unfreeze all layers - enable gradient computation for all parameters
        for param in self.backbone.parameters():
            param.requires_grad = True
        
        # Fusion layer for 9 modalities
        self.fusion_fc = nn.Sequential(
            nn.Linear(9 * self.feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
        
    def forward(self, x_dict):
        features = []
        for _, x in x_dict.items():
            feat = self.backbone(x)  # Extract features using ResNet backbone
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)
        out = self.fusion_fc(fused)
        return out


class EfficientNetMultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(EfficientNetMultiModal, self).__init__()
        
        # Load pretrained EfficientNet-B0
        self.backbone = models.efficientnet_b0(pretrained=pretrained)
        self.feature_dim = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()  # Remove final classifier
        
        # Unfreeze all layers - enable gradient computation for all parameters
        for param in self.backbone.parameters():
            param.requires_grad = True
        
        # Fusion layer for 9 modalities
        self.fusion_fc = nn.Sequential(
            nn.Linear(9 * self.feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
        
    def forward(self, x_dict):
        features = []
        for _, x in x_dict.items():
            feat = self.backbone(x)  # Extract features using EfficientNet backbone
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)
        out = self.fusion_fc(fused)
        return out


class MobileNetMultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(MobileNetMultiModal, self).__init__()
        
        # Load pretrained MobileNetV2
        self.backbone = models.mobilenet_v2(pretrained=pretrained)
        self.feature_dim = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()  # Remove final classifier
        
        # Unfreeze all layers - enable gradient computation for all parameters
        for param in self.backbone.parameters():
            param.requires_grad = True
        
        # Fusion layer for 9 modalities
        self.fusion_fc = nn.Sequential(
            nn.Linear(9 * self.feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
        
    def forward(self, x_dict):
        features = []
        for _, x in x_dict.items():
            feat = self.backbone(x)  # Extract features using MobileNet backbone
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)
        out = self.fusion_fc(fused)
        return out


class MultiTrainer:
    def __init__(self, train_loader, val_loader, num_classes, device, epochs=10):
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.num_classes = num_classes
        self.device = device
        self.epochs = epochs
        self.results = {}
        
        # Initialize all models
        self.models = {
            'Custom_CNN': Network(num_classes),
            'ResNet18': ResNetMultiModal(num_classes),
            'EfficientNet': EfficientNetMultiModal(num_classes),
            'MobileNet': MobileNetMultiModal(num_classes)
        }
        
        # Move models to device and setup optimizers
        self.optimizers = {}
        self.criterions = {}
        
        for name, model in self.models.items():
            model.to(device)
            self.optimizers[name] = optim.Adam(model.parameters(), lr=1e-4)
            self.criterions[name] = nn.CrossEntropyLoss()
    
    def train_single_model(self, model_name):
        """Train a single model and return its results"""
        model = self.models[model_name]
        optimizer = self.optimizers[model_name]
        criterion = self.criterions[model_name]
        
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
        
        return {
            'train_losses': train_losses,
            'train_accs': train_accs,
            'val_losses': val_losses,
            'val_accs': val_accs,
            'training_times': training_times,
            'total_time': sum(training_times),
            'best_val_acc': max(val_accs),
            'final_val_acc': val_accs[-1]
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
        start_time = time.time()
        
        # Use ThreadPoolExecutor for parallel training
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self.train_single_model, name): name 
                      for name in self.models.keys()}
            
            for future in futures:
                model_name = futures[future]
                try:
                    self.results[model_name] = future.result()
                except Exception as e:
                    print(f"Error training {model_name}: {e}")
        
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
        print(f"🏆 WINNER: {best_model} with {best_acc} validation accuracy")
        
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


if __name__ == "__main__":
    # Load dataset
    data = MultiModalMillingDataset("Dataset","Dataset\\labels.csv","Dataset\\labels_reg.csv")
    
    # Train/Validation split
    train_size = int(0.8 * len(data))   # 80% training
    val_size   = len(data) - train_size
    train_dataset, val_dataset = random_split(data, [train_size, val_size])

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader   = DataLoader(val_dataset, batch_size=16, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Initialize MultiTrainer
    trainer = MultiTrainer(
        train_loader=train_loader,
        val_loader=val_loader,
        num_classes=3,
        device=device,
        epochs=10
    )
    
    # Show model architecture summary
    trainer.get_model_summary()
    
    # Choose training mode: 'parallel' or 'sequential'
    training_mode = 'sequential'  # Change to 'parallel' for parallel training
    
    if training_mode == 'parallel':
        # Train all models in parallel (faster but uses more GPU memory)
        print("\n🚀 Starting PARALLEL training...")
        results = trainer.train_all_parallel()
    else:
        # Train all models sequentially (slower but more memory efficient)
        print("\n🚀 Starting SEQUENTIAL training...")
        results = trainer.train_all_sequential()
    
    # Compare results
    comparison = trainer.compare_results()
    
    # Plot training curves
    trainer.plot_training_curves()
    
    # Optional: Save results to CSV
    import pandas as pd
    df_comparison = pd.DataFrame(comparison)
    df_comparison.to_csv('model_comparison_results.csv', index=False)
    print("\nResults saved to 'model_comparison_results.csv'")
        