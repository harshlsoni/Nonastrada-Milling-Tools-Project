"""
Network Architecture Module

This module contains all neural network architectures for multi-modal milling dataset classification.
"""

from .custom_cnn import Network
from .resnet_multimodal import ResNetMultiModal
from .efficientnet_multimodal import EfficientNetMultiModal
from .mobilenet_multimodal import MobileNetMultiModal
from .alexnet_multimodal import AlexNetMultiModal
from .vgg16_multimodal import VGG16MultiModal
from .n1_model import N1MultiModal, N1_CNN

__all__ = [
    'Network',
    'ResNetMultiModal', 
    'EfficientNetMultiModal',
    'MobileNetMultiModal',
    'AlexNetMultiModal',
    'VGG16MultiModal',
    'N1MultiModal',
    'N1_CNN'
]