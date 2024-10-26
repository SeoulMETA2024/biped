import torch
from torch import nn

class DistanceSumLoss(nn.Module):
    def __init__(self):
        super().__init__()
