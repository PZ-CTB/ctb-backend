import datetime
import sys
from typing import Optional

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import MinMaxScaler
from torch import nn, optim
from torch.utils.data import DataLoader, TensorDataset

from ..server.constants import QUERIES
from ..server.database import DatabaseProvider
from .stock_predictor import StockPredictor
from .stock_predictor_config import StockPredictorConfig


class StockPredictorManager:
    """Class for managing StockPredictor GRU model"""

    def __init__(self) -> None:
        self.config = StockPredictorConfig()

        self._initialize_model()

        self.train_size_pct: float = 0.8
        self.scaler: MinMaxScaler = MinMaxScaler()

        self.criterion: nn.MSELoss = nn.MSELoss()
        self.optimizer: optim.adam.Adam = optim.Adam(  # pylint: disable=no-member
            self.stock_predictor.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )

    def _initialize_model(self) -> None:
        """Initializing model with parameters from config dataclass."""
        self.stock_predictor: StockPredictor = StockPredictor(
            self.config.input_dim,
            self.config.hidden_dim,
            self.config.num_layers,
            self.config.output_dim,
        )

    def _get_data(self) -> pd.DataFrame:
        """Return all data from the stock values table."""
        data: list = []

        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_ALL_RATE_HISTORY)
            data = handler().fetchall()
            data = [{"date": date.strftime("%Y-%m-%d"), "avg": avg} for date, avg in data]

        data_frame = pd.DataFrame(data, columns=["date", "value"])
        data_frame["date"] = pd.to_datetime(data_frame["date"])
        data_frame.set_index("date", inplace=True)

        return data_frame

    def _get_newest_dates(self) -> pd.DataFrame:
        """Return last 'seq_length' dates to predict future value"""
        data: list = []

        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_ALL_RATE_HISTORY_DESC, [self.config.seq_length])
            data = handler().fetchall()
            data = [{"date": date.strftime("%Y-%m-%d"), "avg": avg} for date, avg in data]

        data_frame = pd.DataFrame(data, columns=["date", "value"])
        data_frame["date"] = pd.to_datetime(data_frame["date"])
        data_frame.set_index("date", inplace=True)

        return data_frame

    def _get_train_val_data(self) -> tuple[np.ndarray, np.ndarray]:
        """Split data into train and validation dataset."""
        data: pd.DataFrame = self._get_data()

        train_size: int = int(len(data) * self.train_size_pct)
        val_size: int = int(len(data) * (1 - self.train_size_pct))

        data_scaled = self.scaler.fit_transform(data)

        train_data: np.ndarray = data_scaled[:train_size]
        val_data: np.ndarray = data_scaled[train_size : train_size + val_size]

        return train_data, val_data

    def _get_data_loader(self, data: np.ndarray) -> DataLoader:
        """Create dataloader for given dataset."""
        data_tensor: torch.Tensor = torch.tensor(data).float()  # pylint: disable=no-member

        sequence: list = []
        for i in range(len(data_tensor) - self.config.seq_length):
            sequence.append(
                (
                    data_tensor[i : i + self.config.seq_length],
                    data_tensor[i + self.config.seq_length : i + self.config.seq_length + 1],
                )
            )

        data_loader: DataLoader = DataLoader(
            TensorDataset(
                torch.stack([i[0] for i in sequence]),  # pylint: disable=no-member
                torch.stack([i[1] for i in sequence]),  # pylint: disable=no-member
            ),
            batch_size=self.config.batch_size,
        )

        return data_loader

    def train_model(self, verbose: bool = False) -> None:
        """Train model"""

        train_data: Optional[np.ndarray] = None
        val_data: Optional[np.ndarray] = None
        train_data, val_data = self._get_train_val_data()

        train_loader: DataLoader = self._get_data_loader(train_data)
        val_loader: DataLoader = self._get_data_loader(val_data)

        no_improvement_count: int = 0
        best_val_loss: float = sys.float_info.max
        loss: torch.Tensor = torch.tensor(0)  # pylint: disable=no-member

        for epoch in range(self.config.max_epochs):
            self.stock_predictor.train()
            for _, (inputs, targets) in enumerate(train_loader):
                self.optimizer.zero_grad()
                outputs: torch.Tensor = self.stock_predictor(inputs)
                loss = self.criterion(outputs[:, -1], targets[:, -1, 0])
                loss.backward()
                self.optimizer.step()

            self.stock_predictor.eval()
            val_loss: float = 0
            with torch.no_grad():
                for inputs, targets in val_loader:
                    outputs = self.stock_predictor(inputs)
                    val_loss += self.criterion(outputs[:, -1], targets[:, -1, 0])
            val_loss /= len(val_loader)

            if verbose:
                print(
                    f"Epoch {epoch + 1}: Train Loss = {loss:.6f}, Validation Loss = {val_loss:.6f}"
                )

            if val_loss + self.config.min_delta >= best_val_loss:
                no_improvement_count += 1
                if no_improvement_count == self.config.patience:
                    if verbose:
                        print(
                            f"No improvement in validation loss after {self.config.patience} \
                                epochs. Stopping training..."
                        )
                    break
            else:
                best_val_loss = val_loss
                no_improvement_count = 0

    def predict_values(self, days: int) -> pd.DataFrame:
        """Predict stock value for next x days"""

        # Gets newest seq_length dates from the data source.
        data: pd.DataFrame = self._get_newest_dates()

        # Get first date for which the stock value will be predicted.
        current_date: datetime.date = pd.to_datetime(data.index[0]).date() + datetime.timedelta(
            days=1
        )

        date_to_predict: datetime.date = pd.to_datetime(data.index[0]).date() + datetime.timedelta(
            days=days
        )

        date_index: pd.DatetimeIndex = pd.date_range(
            start=current_date, end=date_to_predict, freq="D"
        )
        predicted_values: pd.DataFrame = pd.DataFrame(index=date_index, columns=["value"])

        # Predict values until date reaches date_to_predict.
        while current_date <= date_to_predict:
            # Scale data and convert it to tensor
            input_seq_scaled: np.ndarray = self.scaler.fit_transform(data)
            input_seq_tensor: torch.Tensor = (
                torch.tensor(input_seq_scaled).float().unsqueeze(0)  # pylint: disable=no-member
            )

            # Predict output for the next date
            self.stock_predictor.eval()
            with torch.no_grad():
                predicted_output_tensor: torch.Tensor = self.stock_predictor(input_seq_tensor)

            # Convert predicted output from tensor and scale it back.
            predicted_output_scaled: np.ndarray = predicted_output_tensor.numpy().squeeze()
            predicted_output: np.ndarray = self.scaler.inverse_transform(
                predicted_output_scaled.reshape(-1, 1)
            )
            # Create pd.DataFrame with predicted output.
            new_data: pd.DataFrame = pd.DataFrame(
                predicted_output, columns=["value"], index=[pd.to_datetime(current_date)]
            )

            # Create new sequence in order to predict value for the next date.
            data = pd.concat([new_data, data])
            # Delete oldest date from the dataframe
            data.drop(data.index[self.config.seq_length - 1], inplace=True)

            # Update value
            predicted_values.loc[pd.to_datetime(current_date), "value"] = predicted_output[0][0]

            # Increment date.
            current_date += datetime.timedelta(days=1)

        return predicted_values

    def load_model(self, path: str = "stock_predictor_model.pt") -> None:
        """Load saved model."""
        self.stock_predictor.load_state_dict(torch.load(path))

    def save_model(self, path: str = "stock_predictor_model.pt") -> None:
        """Save current loaded model."""
        torch.save(self.stock_predictor.state_dict(), path)
