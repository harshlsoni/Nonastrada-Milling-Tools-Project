import torch
import torch.nn as nn


class Network(nn.Module):
    def __init__(self, num_classes: int):
        super(Network, self).__init__()

        # Define CNN layers separately for better control
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, padding=1)  # -> [B, 32, 224, 224]
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)                                # -> [B, 32, 112, 112]
        
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)                          # -> [B, 64, 112, 112]
        self.pool2 = nn.MaxPool2d(2, 2)                                                   # -> [B, 64, 56, 56]
        
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)                         # -> [B, 128, 56, 56]
        self.pool3 = nn.MaxPool2d(2, 2)                                                   # -> [B, 128, 28, 28]
        
        
        # Calculate flatten size
        dummy = torch.randn(1, 3, 224, 224)
        with torch.no_grad():
            out = self._forward_cnn(dummy)
        self.flatten_size = out.view(1, -1).size(1)

        self.fc = nn.Sequential(
            nn.Linear(9 * self.flatten_size, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes)
            # Removed Softmax - CrossEntropyLoss expects raw logits
        )
    
    def _forward_cnn(self, x):
        """Forward pass through CNN layers"""
        x = self.pool1(torch.relu(self.conv1(x)))
        x = self.pool2(torch.relu(self.conv2(x)))
        x = self.pool3(torch.relu(self.conv3(x)))
        return x

    def forward(self, x_dict):
        features = []
        for _, x in x_dict.items():
            feat = self._forward_cnn(x)
            feat = feat.view(feat.size(0), -1)
            features.append(feat)

        fused = torch.cat(features, dim=1)  # concatenate along feature dimension
        out = self.fc(fused)
        return out