import torch
import torch.nn as nn
import torchvision.models as models


class AlexNetMultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(AlexNetMultiModal, self).__init__()
        
        # Load pretrained AlexNet and remove final classification layer
        self.backbone = models.alexnet(pretrained=pretrained)
        self.feature_dim = self.backbone.classifier[6].in_features
        self.backbone.classifier = nn.Identity()  # Remove final classifier completely
        
        # Freeze all CNN layers except the last TWO CNN blocks (features[6], features[8], features[10])
        # Note: AlexNet has conv layers at indices 0, 3, 6, 8, 10 (features.12 is MaxPool2d)
        for name, param in self.backbone.named_parameters():
            if 'features.6' in name or 'features.8' in name or 'features.10' in name:  # Last THREE conv layers
                param.requires_grad = True
            else:
                param.requires_grad = False
        
        print("AlexNet: Frozen all CNN layers except features.6, features.8 and features.10 (last TWO+ CNN blocks)")
        for name, param in self.backbone.named_parameters():
            print(name, param.requires_grad)
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
            feat = self.backbone(x)  # Extract features using AlexNet backbone
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)
        out = self.fusion_fc(fused)
        return out