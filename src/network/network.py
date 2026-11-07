from pathlib import Path

import torch
import torch.nn as nn

from .input_data import InputData

MODEL_DIR = Path(__file__).resolve().parents[2] / "locations"


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
    def __init__(self, location: str, path: str | Path | None = None):
        self.location = location
        self.path = Path(path) if path else MODEL_DIR / f"{location}.net"

        if not self.path.exists():
            raise FileNotFoundError(f"No trained model at {self.path}")

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

        self.net.eval()


    def guess(self, inputs: InputData) -> int:
        raw = torch.tensor(
            inputs.create_input_array(),
            dtype=torch.float32
        )

        with torch.no_grad():
            results = self.net(raw)

        return round(float(results[0]) * inputs.normal_capacity)



