from dataclasses import dataclass


@dataclass(frozen=True)
class StockPredictorConfig:
    """Class to store the configuration parameters for the StockPredictor model."""

    input_dim: int = 1
    hidden_dim: int = 32
    num_layers: int = 2
    output_dim: int = 1

    seq_length: int = 16
    batch_size: int = 32

    epochs: int = 1000
    patience: int = 10
    min_delta: float = 0.00001
    learning_rate: float = 0.001
