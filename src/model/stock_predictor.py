from typing import Optional

import torch
from torch import nn


class StockPredictor(nn.Module):
    """Model used to predict future stock prices."""

    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int, output_dim: int):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.gru = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc_layer = nn.Linear(hidden_dim, output_dim)

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        """
        Defines the forward pass of the neural network.
        """
        initial_hidden_state: torch.Tensor = torch.zeros(  # pylint: disable=no-member
            self.num_layers, input_tensor.size(0), self.hidden_dim
        ).requires_grad_()

        output: Optional[torch.Tensor] = None

        output, _ = self.gru(input_tensor, initial_hidden_state.detach())
        output = self.fc_layer(output[:, -1, :])
        return output
