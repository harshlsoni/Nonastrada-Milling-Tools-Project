import torch
import torch.nn as nn
import torchvision.models as models


class VGG16MultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(VGG16MultiModal, self).__init__()
        
        # Load pretrained VGG16 and remove final classification layer
        self.backbone = models.vgg16(pretrained=pretrained)
        self.feature_dim = self.backbone.classifier[6].in_features
        self.backbone.classifier[6] = nn.Identity()  # Remove final FC layer
        
        # Freeze all CNN layers except the last CNN block (features[28], features[30])
        for name, param in self.backbone.named_parameters():
            if 'features.28' in name or 'features.30' in name:  # Last conv layers
                param.requires_grad = True
            elif 'classifier' in name:  # Keep classifier layers trainable
                param.requires_grad = True
            else:
                param.requires_grad = False
        
        print("VGG16: Frozen all CNN layers except features.28 and features.30 (last CNN blocks)")
        
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
            feat = self.backbone(x)  # Extract features using VGG16 backbone
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)
        out = self.fusion_fc(fused)
        return out