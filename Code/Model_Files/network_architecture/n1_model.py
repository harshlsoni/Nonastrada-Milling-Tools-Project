import torch
import torch.nn as nn
import torch.nn.functional as F


class N1MultiModal(nn.Module):
    """
    N1 CNN MultiModal Model for multimodal milling dataset classification
    
    This model adapts the N1 CNN architecture to work with multiple modalities
    following the same pattern as other models in the network_architecture module.
    """
    
    def __init__(self, num_classes: int):
        super(N1MultiModal, self).__init__()
        
        # N1 CNN backbone for feature extraction
        self.backbone = N1_CNN_Backbone()
        
        # Calculate feature dimension from backbone
        # N1 CNN backbone with global average pooling produces 32 features per modality
        self.feature_dim = 32
        
        # Fusion layer for 9 modalities
        self.fusion_fc = nn.Sequential(
            nn.Linear(9 * self.feature_dim, 1024),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
        
        print("N1 CNN: Custom lightweight architecture for multimodal learning")
        
    def forward(self, x_dict):
        features = []
        for _, x in x_dict.items():
            feat = self.backbone(x)  # Extract features using N1 CNN backbone
            feat = feat.view(feat.size(0), -1)  # Flatten
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)
        out = self.fusion_fc(fused)
        return out


class N1_CNN_Backbone(nn.Module):
    """
    N1 CNN Backbone for feature extraction
    Based on the original N1 CNN architecture but adapted for feature extraction
    """
    
    def __init__(self, input_channels=3):
        super(N1_CNN_Backbone, self).__init__()
        
        # Conv2D Layer 1: 3x3, 16 filters
        self.conv1 = nn.Conv2d(input_channels, 16, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Conv2D Layer 2: 3x3, 16 filters
        self.conv2 = nn.Conv2d(16, 16, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(16)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Conv2D Layer 3: 3x3, 32 filters
        self.conv3 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(32)
        
        # Global Average Pooling to reduce spatial dimensions
        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        
    def forward(self, x):
        # Conv1 -> BatchNorm -> ReLU -> MaxPool
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool1(x)
        
        # Conv2 -> BatchNorm -> ReLU -> MaxPool
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool2(x)
        
        # Conv3 -> BatchNorm -> ReLU
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        
        # Global Average Pooling to get fixed-size features
        x = self.global_avg_pool(x)  # Output: [batch_size, 32, 1, 1]
        
        return x


class N1_CNN(nn.Module):
    """
    Original N1 CNN Model for single-modal classification
    Kept for backward compatibility and standalone use
    """
    
    def __init__(self, input_channels=3, num_classes=10):
        super(N1_CNN, self).__init__()
        
        # Use the same backbone
        self.backbone = N1_CNN_Backbone(input_channels)
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(32, 128),  # 32 features from global avg pooling
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
        
    def forward(self, x):
        # Extract features
        x = self.backbone(x)
        x = x.view(x.size(0), -1)  # Flatten: [batch_size, 32]
        
        # Classification
        x = self.classifier(x)
        
        return x