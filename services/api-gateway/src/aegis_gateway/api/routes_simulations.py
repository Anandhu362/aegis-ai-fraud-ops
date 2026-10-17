"""Attack scenario simulation endpoints for interactive demonstrations."""

from typing import Annotated

from aegis_common.schemas.verdict import Verdict
from fastapi import APIRouter, Depends, Query

from aegis_gateway.api.deps import get_gateway_service, verify_auth_or_mock
from aegis_gateway.application.gateway_service import GatewayService

router = APIRouter(prefix="/v1/simulations", tags=["simulations"])


@router.post(
    "/{scenario}",
    response_model=Verdict | dict[str, str],
    summary="Trigger demonstration attack scenario",
)
async def trigger_simulation(
    scenario: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    _caller: Annotated[str, Depends(verify_auth_or_mock)],
    mode: str = Query(default="sync", description="Execution mode: 'sync' or 'async'"),
    tx_id: str | None = Query(default=None, description="Optional custom transaction ID"),
) -> Verdict | dict[str, str]:
    """Trigger predefined fraud attack scenarios: 'coffee' (fast-path),
    'challenge_3ds' (step-up authentication), 'smurfing' (structuring),
    or 'tor_travel' (impossible travel ATO).
    """
    return await service.trigger_simulation_scenario(scenario=scenario, mode=mode, tx_id=tx_id)
