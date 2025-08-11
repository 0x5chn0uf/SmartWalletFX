import time
from datetime import datetime
from typing import List

from fastapi import APIRouter, Request, status

# Dependency imports
from app.api.dependencies import get_user_id_from_request
from app.domain.schemas.defi import PortfolioSnapshot
from app.domain.schemas.defi_dashboard import DefiKPI, ProtocolBreakdown
from app.domain.schemas.portfolio_timeline import PortfolioTimeline
from app.domain.schemas.wallet import WalletResponse
from app.usecase.wallet_usecase import WalletUsecase
from app.utils.logging import Audit


class DeFi:
    """DeFi endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(tags=["defi"])
    __wallet_uc: WalletUsecase

    def __init__(
        self,
        wallet_usecase: WalletUsecase,
    ):
        """Initialize with injected dependencies."""
        DeFi.__wallet_uc = wallet_usecase

    @staticmethod
    @ep.get(
        "/defi/wallets",
        response_model=List[WalletResponse],
    )
    async def get_wallets(
        request: Request,
    ):
        """Get all wallets for the current user (proxy to existing wallet endpoint)."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info("DeFi wallet listing started", user_id=user_id, client_ip=client_ip)

        try:
            result = await DeFi.__wallet_uc.list_wallets(user_id)

            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "DeFi wallet listing completed",
                user_id=str(user_id),
                wallet_count=len(result),
                duration_ms=duration,
            )

            return result
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "DeFi wallet listing failed",
                user_id=str(user_id),
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    @staticmethod
    @ep.get(
        "/defi/wallets/{wallet_address}",
        response_model=WalletResponse,
    )
    async def get_wallet_details(
        request: Request,
        wallet_address: str,
    ):
        """Get wallet details by address (proxy to verify ownership)."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info(
            "DeFi wallet details started",
            user_id=user_id,
            wallet_address=wallet_address,
            client_ip=client_ip,
        )

        try:
            # Get all user wallets and find the specific one
            wallets = await DeFi.__wallet_uc.list_wallets(user_id)
            wallet = next(
                (w for w in wallets if w.address.lower() == wallet_address.lower()),
                None,
            )

            if not wallet:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found or access denied",
                )

            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "DeFi wallet details completed",
                user_id=str(user_id),
                wallet_address=wallet_address,
                wallet_id=str(wallet.id),
                duration_ms=duration,
            )

            return wallet
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "DeFi wallet details failed",
                user_id=str(user_id),
                wallet_address=wallet_address,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    @staticmethod
    @ep.get(
        "/defi/timeline/{address}",
        response_model=PortfolioTimeline,
    )
    async def get_portfolio_timeline_for_address(
        request: Request,
        address: str,
        interval: str = "daily",
        limit: int = 30,
        offset: int = 0,
        start_date: str = None,
        end_date: str = None,
    ):
        """Get portfolio timeline for a specific wallet address."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info(
            "DeFi portfolio timeline started",
            user_id=user_id,
            wallet_address=address,
            interval=interval,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            client_ip=client_ip,
        )

        try:
            result = await DeFi.__wallet_uc.get_portfolio_timeline(
                user_id, address, interval, limit, offset, start_date, end_date
            )

            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "DeFi portfolio timeline completed",
                user_id=str(user_id),
                wallet_address=address,
                data_points=len(result.timestamps),
                duration_ms=duration,
            )

            return result
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "DeFi portfolio timeline failed",
                user_id=str(user_id),
                wallet_address=address,
                interval=interval,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    @staticmethod
    @ep.get(
        "/defi/portfolio/timeline",
        response_model=PortfolioTimeline,
    )
    async def get_aggregated_portfolio_timeline(
        request: Request,
        interval: str = "daily",
        limit: int = 30,
        offset: int = 0,
    ):
        """Get aggregated portfolio timeline across all user wallets."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info(
            "DeFi aggregated portfolio timeline started",
            user_id=user_id,
            interval=interval,
            limit=limit,
            offset=offset,
            client_ip=client_ip,
        )

        try:
            # Get all user wallets
            wallets = await DeFi.__wallet_uc.list_wallets(user_id)

            # Aggregate timeline data from all wallets
            aggregated_timestamps = []
            aggregated_collateral_usd = []
            aggregated_borrowings_usd = []

            wallet_timelines = []
            for wallet in wallets:
                try:
                    timeline = await DeFi.__wallet_uc.get_portfolio_timeline(
                        user_id, wallet.address, interval, limit, offset
                    )
                    wallet_timelines.append(timeline)
                except Exception as e:
                    # Log but continue with other wallets
                    Audit.warning(
                        "Failed to get timeline for wallet",
                        user_id=str(user_id),
                        wallet_address=wallet.address,
                        error=str(e),
                    )
                    continue

            # Aggregate data across all wallets at each timestamp
            if wallet_timelines:
                # Get all unique timestamps and sort them
                all_timestamps = set()
                for timeline in wallet_timelines:
                    all_timestamps.update(timeline.timestamps)

                sorted_timestamps = sorted(all_timestamps)[:limit]

                for timestamp in sorted_timestamps:
                    total_collateral = 0.0
                    total_borrowings = 0.0

                    for timeline in wallet_timelines:
                        # Find the closest timestamp data point
                        if timestamp in timeline.timestamps:
                            idx = timeline.timestamps.index(timestamp)
                            total_collateral += timeline.collateral_usd[idx]
                            total_borrowings += timeline.borrowings_usd[idx]

                    aggregated_timestamps.append(timestamp)
                    aggregated_collateral_usd.append(total_collateral)
                    aggregated_borrowings_usd.append(total_borrowings)

            result = PortfolioTimeline(
                timestamps=aggregated_timestamps,
                collateral_usd=aggregated_collateral_usd,
                borrowings_usd=aggregated_borrowings_usd,
            )

            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "DeFi aggregated portfolio timeline completed",
                user_id=str(user_id),
                wallet_count=len(wallets),
                data_points=len(aggregated_timestamps),
                duration_ms=duration,
            )

            return result
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "DeFi aggregated portfolio timeline failed",
                user_id=str(user_id),
                interval=interval,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    @staticmethod
    @ep.get(
        "/defi/portfolio/snapshot",
        response_model=PortfolioSnapshot,
    )
    async def get_current_portfolio_snapshot(
        request: Request,
    ):
        """Get current portfolio snapshot aggregated across all user wallets."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info(
            "DeFi portfolio snapshot started",
            user_id=user_id,
            client_ip=client_ip,
        )

        try:
            # Get all user wallets
            wallets = await DeFi.__wallet_uc.list_wallets(user_id)

            # Initialize aggregated values
            total_collateral = 0.0
            total_borrowings = 0.0
            total_collateral_usd = 0.0
            total_borrowings_usd = 0.0
            all_collaterals = []
            all_borrowings = []
            all_staked_positions = []
            all_health_scores = []
            protocol_breakdown = {}

            # Aggregate metrics from all wallets
            for wallet in wallets:
                try:
                    metrics = await DeFi.__wallet_uc.get_portfolio_metrics(
                        user_id, wallet.address
                    )

                    # Aggregate totals
                    total_collateral += metrics.total_collateral
                    total_borrowings += metrics.total_borrowings
                    total_collateral_usd += metrics.total_collateral_usd
                    total_borrowings_usd += metrics.total_borrowings_usd

                    # Aggregate position lists
                    all_collaterals.extend(metrics.collaterals)
                    all_borrowings.extend(metrics.borrowings)
                    all_staked_positions.extend(metrics.staked_positions)
                    all_health_scores.extend(metrics.health_scores)

                    # Aggregate protocol breakdown
                    for protocol, breakdown in metrics.protocol_breakdown.items():
                        if protocol not in protocol_breakdown:
                            protocol_breakdown[protocol] = {
                                "total_collateral": 0.0,
                                "total_borrowings": 0.0,
                                "positions": 0,
                                "health_scores": [],
                                "collaterals": [],
                                "borrowings": [],
                                "staked_positions": [],
                            }

                        # Sum up protocol-specific values
                        if hasattr(breakdown, "total_collateral"):
                            protocol_breakdown[protocol][
                                "total_collateral"
                            ] += breakdown.total_collateral
                        if hasattr(breakdown, "total_borrowings"):
                            protocol_breakdown[protocol][
                                "total_borrowings"
                            ] += breakdown.total_borrowings
                        if hasattr(breakdown, "collaterals"):
                            protocol_breakdown[protocol]["collaterals"].extend(
                                breakdown.collaterals
                            )
                        if hasattr(breakdown, "borrowings"):
                            protocol_breakdown[protocol]["borrowings"].extend(
                                breakdown.borrowings
                            )
                        if hasattr(breakdown, "staked_positions"):
                            protocol_breakdown[protocol]["staked_positions"].extend(
                                breakdown.staked_positions
                            )
                        if hasattr(breakdown, "health_scores"):
                            protocol_breakdown[protocol]["health_scores"].extend(
                                breakdown.health_scores
                            )

                except Exception as e:
                    # Log but continue with other wallets
                    Audit.warning(
                        "Failed to get metrics for wallet",
                        user_id=str(user_id),
                        wallet_address=wallet.address,
                        error=str(e),
                    )
                    continue

            # Calculate aggregate health score (weighted average by collateral)
            aggregate_health_score = None
            if total_collateral_usd > 0 and all_health_scores:
                weighted_score = 0.0
                total_weight = 0.0
                for health_score in all_health_scores:
                    if health_score.total_value and health_score.total_value > 0:
                        weight = health_score.total_value
                        weighted_score += health_score.score * weight
                        total_weight += weight

                if total_weight > 0:
                    aggregate_health_score = weighted_score / total_weight

            # Calculate aggregate APY (weighted average by USD value)
            aggregate_apy = None
            if total_collateral_usd > 0:
                weighted_apy = 0.0
                total_weight = 0.0
                for position in all_staked_positions:
                    if position.apy and position.usd_value > 0:
                        weight = position.usd_value
                        weighted_apy += position.apy * weight
                        total_weight += weight

                if total_weight > 0:
                    aggregate_apy = weighted_apy / total_weight

            snapshot = PortfolioSnapshot(
                user_address=f"aggregated_{len(wallets)}_wallets",
                timestamp=int(datetime.now().timestamp()),
                total_collateral=total_collateral,
                total_borrowings=total_borrowings,
                total_collateral_usd=total_collateral_usd,
                total_borrowings_usd=total_borrowings_usd,
                aggregate_health_score=aggregate_health_score,
                aggregate_apy=aggregate_apy,
                collaterals=all_collaterals,
                borrowings=all_borrowings,
                staked_positions=all_staked_positions,
                health_scores=all_health_scores,
                protocol_breakdown=protocol_breakdown,
            )

            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "DeFi portfolio snapshot completed",
                user_id=str(user_id),
                wallet_count=len(wallets),
                total_collateral_usd=total_collateral_usd,
                total_borrowings_usd=total_borrowings_usd,
                duration_ms=duration,
            )

            return snapshot
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "DeFi portfolio snapshot failed",
                user_id=str(user_id),
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    @staticmethod
    @ep.get(
        "/defi/portfolio/kpi",
        response_model=DefiKPI,
    )
    async def get_portfolio_kpi(
        request: Request,
    ):
        """Get portfolio KPIs with protocol breakdown."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info(
            "DeFi portfolio KPI started",
            user_id=user_id,
            client_ip=client_ip,
        )

        try:
            # Get current portfolio snapshot to calculate KPIs
            snapshot = await DeFi.get_current_portfolio_snapshot(request)

            # Calculate total TVL (Total Value Locked)
            tvl = snapshot.total_collateral_usd

            # Use the aggregate APY from snapshot
            apy = snapshot.aggregate_apy or 0.0

            # Build protocol breakdown for KPIs
            protocol_breakdowns = []
            for protocol_name, breakdown_data in snapshot.protocol_breakdown.items():
                # Calculate protocol-specific metrics
                protocol_tvl = breakdown_data.get("total_collateral", 0.0)
                protocol_positions = len(breakdown_data.get("collaterals", [])) + len(
                    breakdown_data.get("staked_positions", [])
                )

                # Calculate protocol APY
                protocol_apy = 0.0
                staked_positions = breakdown_data.get("staked_positions", [])
                if staked_positions:
                    total_weighted_apy = 0.0
                    total_weight = 0.0
                    for position in staked_positions:
                        if hasattr(position, "apy") and hasattr(position, "usd_value"):
                            if position.apy and position.usd_value > 0:
                                weight = position.usd_value
                                total_weighted_apy += position.apy * weight
                                total_weight += weight

                    if total_weight > 0:
                        protocol_apy = total_weighted_apy / total_weight

                protocol_breakdown = ProtocolBreakdown(
                    name=protocol_name,
                    tvl=protocol_tvl,
                    apy=protocol_apy,
                    positions=protocol_positions,
                )
                protocol_breakdowns.append(protocol_breakdown)

            kpi = DefiKPI(
                tvl=tvl,
                apy=apy,
                protocols=protocol_breakdowns,
                updated_at=datetime.now(),
            )

            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "DeFi portfolio KPI completed",
                user_id=str(user_id),
                tvl=tvl,
                apy=apy,
                protocol_count=len(protocol_breakdowns),
                duration_ms=duration,
            )

            return kpi
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "DeFi portfolio KPI failed",
                user_id=str(user_id),
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise
