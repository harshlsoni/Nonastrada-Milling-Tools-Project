import torch
import torch.nn as nn
import torchvision.models as models


class VGG16MultiModal(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(VGG16MultiModal, self).__init__()
        
        # Load pretrained VGG16 and remove final classification layer
        weights = models.VGG16_Weights.IMAGENET1K_V1 if pretrained else None
        vgg16 = models.vgg16(weights=weights)
        self.backbone = vgg16.features  # Use only feature extraction part
        # VGG16 features output: [batch_size, 512, 7, 7] -> flattened: 512 * 7 * 7 = 25088
        self.feature_dim = 512 * 7 * 7
        
        # Freeze all CNN layers except the last TWO CNN blocks (24, 26, 28)
        # Note: VGG16 has conv layers at indices 0,2,5,7,10,12,14,17,19,21,24,26,28
        for name, param in self.backbone.named_parameters():
            if '24.' in name or '26.' in name or '28.' in name:  # Last THREE conv layers
                param.requires_grad = True
            else:
                param.requires_grad = False
        
        print("VGG16: Frozen all CNN layers except features.24, features.26 and features.28 (last TWO+ CNN blocks)")
        
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
            feat = feat.view(feat.size(0), -1)  # Flatten: [batch_size, 25088]
            features.append(feat)
        
        # Concatenate features from all modalities
        fused = torch.cat(features, dim=1)
        out = self.fusion_fc(fused)
        return out