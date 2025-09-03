import torch
import torch.nn as nn
import torchvision.models as models


class EfficientNetMultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(EfficientNetMultiModal, self).__init__()
        
        # Load pretrained EfficientNet-B0
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        efficientnet = models.efficientnet_b0(weights=weights)
        # Get feature dimension before removing classifier
        self.feature_dim = efficientnet.classifier[1].in_features  # EfficientNet-B0: 1280
        # Use only feature extraction part
        self.backbone = efficientnet.features
        # Add adaptive pooling to ensure consistent output size
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Freeze all layers except the last TWO CNN blocks (6, 7, and 8)
        for name, param in self.backbone.named_parameters():
            if '6.' in name or '7.' in name or '8.' in name:  # Last three blocks for better coverage
                param.requires_grad = True
            else:
                param.requires_grad = False
        
        print("EfficientNet-B0: Frozen all layers except features.6, features.7 and features.8 (last TWO+ CNN blocks)")
        
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
            feat = self.avgpool(feat)  # Apply adaptive pooling: [batch_size, 1280, 1, 1]
            feat = feat.view(feat.size(0), -1)  # Flatten: [batch_size, 1280]
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)  # Shape: [batch_size, 9 * 1280]
        out = self.fusion_fc(fused)
        return out