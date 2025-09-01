import torch
import torch.nn as nn


class Network(nn.Module):
    def __init__(self, num_classes: int):
        super(Network, self).__init__()

        self.cnnLayer = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, padding=1),  # -> [B, 32, 224, 224]
            nn.MaxPool2d(kernel_size=2, stride=2),                                # -> [B, 32, 112, 112]

            nn.Conv2d(32, 64, kernel_size=3, padding=1),                          # -> [B, 64, 112, 112]
            nn.MaxPool2d(2, 2),                                                   # -> [B, 64, 56, 56]

            nn.Conv2d(64, 128, kernel_size=3, padding=1),                         # -> [B, 128, 56, 56]
            nn.MaxPool2d(2, 2) 
        )

        dummy = torch.randn(1, 3, 224, 224)   # match your dataset input size
        with torch.no_grad():
            out = self.cnnLayer(dummy)
        self.flatten_size = out.view(1, -1).size(1)

        self.fc = nn.Sequential(
            nn.Linear(9 * self.flatten_size, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes),
            nn.Softmax(dim=1)
        )

    def forward(self, x_dict):
        features = []
        for _, x in x_dict.items():
            feat = self.cnnLayer(x) 
            feat = feat.view(feat.size(0), -1)
            features.append(feat)

        fused = torch.cat(features, dim=1)  # concatenate along feature dimension
        out = self.fc(fused)
        return out