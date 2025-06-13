from app.adapters.protocols import (
    AaveContractAdapter,
    CompoundContractAdapter,
    RadiantContractAdapter,
)
from app.aggregators.protocol_aggregator import (
    aggregate_portfolio_metrics_from_adapters,
)
from app.schemas.portfolio_metrics import PortfolioMetrics


class PortfolioAggregationUsecase:
    def __init__(self):
        self.adapters = [
            AaveContractAdapter(),
            CompoundContractAdapter(),
            RadiantContractAdapter(),
        ]

    async def aggregate_portfolio_metrics(
        self, address: str
    ) -> PortfolioMetrics:
        return await aggregate_portfolio_metrics_from_adapters(
            address, self.adapters
        )
