import os
import torch
import torch.nn as nn
import scipy.io as sio
import pandas as pd
from torch.utils.data import Dataset, DataLoader,random_split
from PIL import Image
from sklearn.preprocessing import LabelEncoder
import torchvision.transforms as transforms
import torch.optim as optim

class MultiModalMillingDataset(Dataset):
    def __init__(self, root_dir, labels_csv, labels_reg_csv,  transform=None):
        """
        Args:
            root_dir (str): Path to dataset folder
            labels_csv (str): Path to classification labels CSV
            labels_reg_csv (str): Path to regression labels CSV
            mat_file (str): Path to raw force .mat file
            transform (callable, optional): Optional transform to be applied on images
        """
        self.root_dir = root_dir
        self.labels = pd.read_csv(labels_csv)
        self.label_encoder = LabelEncoder()
        self.labels["encoded"] = self.label_encoder.fit_transform(self.labels.iloc[:, 1])
        self.reg_labels = pd.read_csv(labels_reg_csv)
        
        self.transform = transform if transform else transforms.Compose([
        transforms.Resize((224, 224)),   # make all images 224x224
        transforms.ToTensor(),
    ])

        # store paths for different modalities
        self.modalities = {
            "chip": os.path.join(root_dir, "chip"),
            "scalx": os.path.join(root_dir, "scal", "x"),
            "scaly": os.path.join(root_dir, "scal", "y"),
            "scalz": os.path.join(root_dir, "scal", "z"),
            "specx": os.path.join(root_dir, "spec", "x"),
            "specy": os.path.join(root_dir, "spec", "y"),
            "specz" : os.path.join(root_dir,"spec","z"),
            "tool": os.path.join(root_dir, "tool"),
            "work": os.path.join(root_dir, "work")
        }

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        # classification & regression labels
        image_label = torch.tensor(self.labels.iloc[idx]["encoded"], dtype=torch.long)  # assuming 2nd column is label
        tool_label = torch.tensor(self.labels.iloc[idx]["tool_label"], dtype=torch.long)
        flank_wear = torch.tensor(self.reg_labels.iloc[idx]["flank_wear"], dtype=torch.float)

        row = self.labels.iloc[idx]
        file_name = row["id"]
        # load images from modalities
        sample = {}
        for modality, path in self.modalities.items():
            if modality in ["scalx", "scaly", "scalz", "work"]:
                ext = ".png"
            else:
                ext = ".jpg"

            img_path = os.path.join(path, file_name + ext)

            if not os.path.exists(img_path):
                sample[modality] = torch.zeros(3, 224, 224)

            img = Image.open(img_path).convert("RGB")
            img = self.transform(img)
            sample[modality] = img

        # add force signals (if needed per sample)
        # Example: force_data['forces'][idx] -> adjust key according to .mat file structure
        # sample['force'] = torch.tensor(self.force_data['forces'][idx], dtype=torch.float)

        return sample, image_label,tool_label, flank_wear



class Network(nn.Module):
    def __init__(self,num_classes : int):
        super(Network,self).__init__()

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

        

    def forward(self,x_dict):
        features = []
        for _, x in x_dict.items():
            feat = self.cnnLayer(x) 
            feat = feat.view(feat.size(0), -1)
            features.append(feat)

        
        fused = torch.cat(features, dim=1)  # concatenate along feature dimension
        out = self.fc(fused)
        return out




if __name__ == "__main__":
    data = MultiModalMillingDataset("Dataset","Dataset\\labels.csv","Dataset\\labels_reg.csv")
    
    # Train/Validation split
    train_size = int(0.8 * len(data))   # 80% training
    val_size   = len(data) - train_size
    train_dataset, val_dataset = random_split(data, [train_size, val_size])

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader   = DataLoader(val_dataset, batch_size=16, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Network(3).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)


    #Training loop
    def train_one_epoch(model, dataloader, optimizer, criterion, device):
        model.train()
        running_loss, correct, total = 0.0, 0, 0

        for x_dict, image_labels ,_ , _ in dataloader:  # x_dict is dict of 9 modalities
            # move all modalities to device
            for key in x_dict:
                x_dict[key] = x_dict[key].to(device)

            image_labels = image_labels.to(device)

            # forward
            outputs = model(x_dict)
            loss = criterion(outputs, image_labels)

            # backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # metrics
            running_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            correct += (preds == image_labels).sum().item()
            total += image_labels.size(0)

        epoch_loss = running_loss / len(dataloader)
        epoch_acc = correct / total
        return epoch_loss, epoch_acc


    # ----------------------------
    # 4. Validation Loop
    # ----------------------------
    def evaluate(model, dataloader, criterion, device):
        model.eval()
        running_loss, correct, total = 0.0, 0, 0

        with torch.no_grad():
            for x_dict, labels , _ , _ in dataloader:
                for key in x_dict:
                    x_dict[key] = x_dict[key].to(device)
                labels = labels.to(device)

                outputs = model(x_dict)
                loss = criterion(outputs, labels)

                running_loss += loss.item()
                _, preds = torch.max(outputs, 1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        epoch_loss = running_loss / len(dataloader)
        epoch_acc = correct / total
        return epoch_loss, epoch_acc
    

    EPOCHS = 10
    for epoch in range(EPOCHS):
        train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)

        print(f"Epoch {epoch+1}/{EPOCHS} | "
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
        