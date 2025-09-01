import os
import torch
import pandas as pd
from torch.utils.data import Dataset
from PIL import Image
from sklearn.preprocessing import LabelEncoder
import torchvision.transforms as transforms


class MultiModalMillingDataset(Dataset):
    def __init__(self, root_dir, labels_csv, labels_reg_csv, transform=None):
        """
        Multi-modal milling dataset for classification and regression tasks.
        
        Args:
            root_dir (str): Path to dataset folder
            labels_csv (str): Path to classification labels CSV
            labels_reg_csv (str): Path to regression labels CSV
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

        # Store paths for different modalities
        self.modalities = {
            "chip": os.path.join(root_dir, "chip"),
            "scalx": os.path.join(root_dir, "scal", "x"),
            "scaly": os.path.join(root_dir, "scal", "y"),
            "scalz": os.path.join(root_dir, "scal", "z"),
            "specx": os.path.join(root_dir, "spec", "x"),
            "specy": os.path.join(root_dir, "spec", "y"),
            "specz": os.path.join(root_dir, "spec", "z"),
            "tool": os.path.join(root_dir, "tool"),
            "work": os.path.join(root_dir, "work")
        }

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        # Classification & regression labels
        image_label = torch.tensor(self.labels.iloc[idx]["encoded"], dtype=torch.long)
        tool_label = torch.tensor(self.labels.iloc[idx]["tool_label"], dtype=torch.long)
        flank_wear = torch.tensor(self.reg_labels.iloc[idx]["flank_wear"], dtype=torch.float)

        row = self.labels.iloc[idx]
        file_name = row["id"]
        
        # Load images from modalities
        sample = {}
        for modality, path in self.modalities.items():
            if modality in ["scalx", "scaly", "scalz", "work"]:
                ext = ".png"
            else:
                ext = ".jpg"

            img_path = os.path.join(path, file_name + ext)

            if not os.path.exists(img_path):
                sample[modality] = torch.zeros(3, 224, 224)
            else:
                img = Image.open(img_path).convert("RGB")
                img = self.transform(img)
                sample[modality] = img

        # Add force signals (if needed per sample)
        # Example: force_data['forces'][idx] -> adjust key according to .mat file structure
        # sample['force'] = torch.tensor(self.force_data['forces'][idx], dtype=torch.float)

        return sample, image_label, tool_label, flank_wear

    def get_class_names(self):
        """Get the original class names before encoding"""
        return self.label_encoder.classes_

    def get_dataset_info(self):
        """Get basic information about the dataset"""
        return {
            'total_samples': len(self.labels),
            'num_classes': len(self.label_encoder.classes_),
            'class_names': self.get_class_names(),
            'modalities': list(self.modalities.keys()),
            'image_size': (224, 224)
        }