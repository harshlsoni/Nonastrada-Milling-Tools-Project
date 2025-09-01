import torch
import torch.nn as nn
import torchvision.models as models


class MobileNetMultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(MobileNetMultiModal, self).__init__()
        
        # Load pretrained MobileNetV2
        self.backbone = models.mobilenet_v2(pretrained=pretrained)
        self.feature_dim = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()  # Remove final classifier
        
        # Freeze all layers except the last CNN blocks (features[17] and features[18])
        for name, param in self.backbone.named_parameters():
            if 'features.17' in name or 'features.18' in name:  # Last two inverted residual blocks
                param.requires_grad = True
            else:
                param.requires_grad = False
        
        print("MobileNetV2: Frozen all layers except features.17 and features.18 (last CNN blocks)")
        
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