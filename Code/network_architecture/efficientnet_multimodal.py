import torch
import torch.nn as nn
import torchvision.models as models


class EfficientNetMultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(EfficientNetMultiModal, self).__init__()
        
        # Load pretrained EfficientNet-B0
        self.backbone = models.efficientnet_b0(pretrained=pretrained)
        self.feature_dim = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()  # Remove final classifier completely
        
        # Freeze all layers except the last TWO CNN blocks (features[6], features[7], and features[8])
        for name, param in self.backbone.named_parameters():
            if 'features.6' in name or 'features.7' in name or 'features.8' in name:  # Last three blocks for better coverage
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
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)
        out = self.fusion_fc(fused)
        return out