class WalletTransaction:
    """Representation of wallet transaction for transaction history endpoint."""

    def __init__(self, timestamp: str, type: str, amount_usd: float, amount_btc: float,
                 total_usd_after_transaction: float, total_btc_after_transaction: float):
        self.timestamp: str = timestamp
        self.type: str = type
        self.amount_usd: float = amount_usd
        self.amount_btc: float = amount_btc
        self.total_usd_after_transaction: float = total_usd_after_transaction
        self.total_btc_after_transaction: float = total_btc_after_transaction
