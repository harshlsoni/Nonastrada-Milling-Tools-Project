import torch
import torch.nn as nn
import torchvision.models as models


class AlexNetMultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(AlexNetMultiModal, self).__init__()
        
        # Load pretrained AlexNet
        weights = models.AlexNet_Weights.IMAGENET1K_V1 if pretrained else None
        alexnet = models.alexnet(weights=weights)
        
        # Extract only the feature extraction part (CNN layers)
        self.backbone = alexnet.features
        
        # Calculate feature dimension after CNN layers
        # AlexNet features output: [batch_size, 256, 6, 6] -> flattened: 256 * 6 * 6 = 9216
        self.feature_dim = 256 * 6 * 6  # AlexNet's final conv layer output
        
        # Freeze all CNN layers except the last TWO CNN blocks
        # AlexNet features: conv layers at indices 0, 3, 6, 8, 10
        # Last TWO blocks: features[8] (conv4) and features[10] (conv5)
        for name, param in self.backbone.named_parameters():
            if '8.' in name or '10.' in name:  # Last TWO conv layers (conv4 and conv5)
                param.requires_grad = True
            else:
                param.requires_grad = False
        
        # Optional: Print freezing status (can be removed for production)
        # print("AlexNet: Frozen all CNN layers except features.8 and features.10 (last TWO CNN blocks)")
        
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
        
    def forward(self, x_dict):
        features = []
        for _, x in x_dict.items():
            # Extract features using AlexNet backbone (CNN layers only)
            feat = self.backbone(x)  # Output shape: [batch_size, 256, 6, 6]
            feat = feat.view(feat.size(0), -1)  # Flatten: [batch_size, 9216]
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)  # Shape: [batch_size, 9 * 9216]
        out = self.fusion_fc(fused)
        return out