import os
import torch
import torch.nn as nn

from .input_data import InputData


class InternalNeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()

        self.layers = nn.Sequential(
            nn.Linear(17, 128),
            nn.ReLU(),

            nn.Linear(128, 128),
            nn.ReLU(),

            nn.Linear(128, 64),
            nn.ReLU(),

            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.layers(x)



class Network:
    def __init__(self, location: str):
        self.location = location
        self.path = f"locations/{location}.net"

        device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.net = InternalNeuralNetwork().to(device)

        self.net.load_state_dict(
            torch.load(
                self.path,
                map_location=device,
                weights_only=True
            )
        )


    def guess(self, inputs: InputData) -> int:
        raw = torch.tensor(
            inputs.create_input_array(),
            dtype=torch.float32
        )

        results = self.net.forward(raw)

        return round(float(results[0] * inputs.normal_capacity))



