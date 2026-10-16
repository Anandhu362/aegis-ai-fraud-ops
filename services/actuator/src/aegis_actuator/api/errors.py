"""RFC 7807 problem+json exception handlers."""

from aegis_common.errors import AegisError
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM_JSON = "application/problem+json"


def install_problem_handlers(app: FastAPI) -> None:
    """Register handlers mapping errors to RFC 7807 responses."""

    @app.exception_handler(AegisError)
    async def _aegis_error(request: Request, exc: AegisError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_problem_details(instance=request.url.path),
            media_type=PROBLEM_JSON,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "type": "urn:aegis:error:validation",
                "title": "Validation Failed",
                "status": 422,
                "detail": "Request failed schema validation",
                "instance": request.url.path,
                "details": {"errors": exc.errors()},
            },
            media_type=PROBLEM_JSON,
        )
