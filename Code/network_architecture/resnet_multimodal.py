import torch
import torch.nn as nn
import torchvision.models as models


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