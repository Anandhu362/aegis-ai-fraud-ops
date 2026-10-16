"""Composition root for api-gateway service."""

from aegis_gateway.adapters.firestore_case_repo import FirestoreCaseRepository
from aegis_gateway.adapters.http_dispatcher import HttpInvestigationDispatcher
from aegis_gateway.adapters.in_memory_case_repo import InMemoryCaseRepository
from aegis_gateway.application.gateway_service import GatewayService
from aegis_gateway.ports.case_repo import CaseRepositoryPort
from aegis_gateway.ports.dispatcher import InvestigationDispatcherPort
from aegis_gateway.settings import GatewaySettings


def build_gateway_service(settings: GatewaySettings) -> GatewayService:
    """Build and wire GatewayService according to active runtime configuration.

    Args:
        settings: Runtime configuration for api-gateway.

    Returns:
        Configured GatewayService instance.
    """
    case_repo: CaseRepositoryPort
    dispatcher: InvestigationDispatcherPort

    if settings.is_mock_mode:
        from aegis_gateway.adapters.mock_dispatcher import (  # noqa: PLC0415
            MockInvestigationDispatcher,
        )

        case_repo = InMemoryCaseRepository()
        dispatcher = MockInvestigationDispatcher()
    else:
        try:
            case_repo = FirestoreCaseRepository(project_id=settings.gcp_project)
        except Exception:
            case_repo = InMemoryCaseRepository()
        dispatcher = HttpInvestigationDispatcher(engine_base_url=settings.aegis_engine_url)

    return GatewayService(dispatcher=dispatcher, case_repo=case_repo)
