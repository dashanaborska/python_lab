import logging
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from sport_results import __version__
from sport_results.analytics import RankingCache
from sport_results.config import Settings, get_settings
from sport_results.database import (
    Base,
    make_engine,
    make_session_factory,
    ping,
    session_scope,
)
from sport_results.exceptions import (
    DuplicateError,
    NotFoundError,
    SportResultsError,
    TransactionError,
)
from sport_results.external_api import RankingClient
from sport_results.logging_config import setup_logging
from sport_results.migrate import upgrade
from sport_results.schemas import (
    AggregatedRankings,
    AthleteCreate,
    AthleteRead,
    ErrorResponse,
    HealthResponse,
    ResultCreate,
    ResultRead,
    ResultUpdate,
    SportRanking,
    SportRead,
    SportStatistics,
)
from sport_results.seed import seed
from sport_results.services import SportService

logger = logging.getLogger("sport_results.api")
ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
}


def get_session(request: Request) -> Iterator[Session]:
    yield from session_scope(request.app.state.session_factory)


def get_service(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> SportService:
    return SportService(session, request.app.state.ranking_cache)


def require_admin(
    request: Request,
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    settings: Settings = request.app.state.settings
    if settings.admin_token is None:
        return
    if x_admin_token != settings.admin_token.get_secret_value():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid admin token")


Service = Annotated[SportService, Depends(get_service)]
router = APIRouter(prefix="/api/v1")


def log_record(result: ResultRead) -> None:
    logger.info("New high result: %s %.1f", result.athlete, result.score)


@router.get("/athletes", response_model=list[AthleteRead], tags=["athletes"])
def list_athletes(
    service: Service,
    sport: str | None = None,
    category: str | None = None,
    sort: Annotated[str, Query(pattern="^-?name$")] = "name",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AthleteRead]:
    return service.list_athletes(sport, category, sort, limit, offset)


@router.get(
    "/athletes/{athlete_id}",
    response_model=AthleteRead,
    responses=ERRORS,
    tags=["athletes"],
)
def get_athlete(athlete_id: int, service: Service) -> AthleteRead:
    return service.get_athlete(athlete_id)


@router.post(
    "/athletes",
    response_model=AthleteRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORS,
    tags=["athletes"],
)
def create_athlete(data: AthleteCreate, service: Service) -> AthleteRead:
    return service.create_athlete(data)


@router.get("/sports", response_model=list[SportRead], tags=["sports"])
def list_sports(service: Service) -> list[SportRead]:
    return service.list_sports()


@router.post(
    "/results",
    response_model=ResultRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORS,
    tags=["results"],
)
def create_result(
    data: ResultCreate, service: Service, background: BackgroundTasks
) -> ResultRead:
    result = service.create_result(data)
    if result.score >= 90:
        background.add_task(log_record, result)
    return result


@router.post(
    "/results/batch",
    response_model=list[ResultRead],
    status_code=status.HTTP_201_CREATED,
    responses=ERRORS,
    tags=["results"],
)
def create_results(items: list[ResultCreate], service: Service) -> list[ResultRead]:
    return service.create_results(items)


@router.patch(
    "/results/{result_id}",
    response_model=ResultRead,
    responses=ERRORS,
    tags=["results"],
)
def update_result(result_id: int, data: ResultUpdate, service: Service) -> ResultRead:
    return service.update_result(result_id, data)


@router.delete(
    "/results/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERRORS,
    tags=["results"],
    dependencies=[Depends(require_admin)],
)
def delete_result(result_id: int, service: Service) -> None:
    service.delete_result(result_id)


@router.get(
    "/sports/{sport_id}/results",
    response_model=list[ResultRead],
    responses=ERRORS,
    tags=["sports"],
)
def sport_results(
    sport_id: int,
    service: Service,
    min_score: Annotated[float, Query(ge=0, le=100)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ResultRead]:
    return service.sport_results(sport_id, min_score, limit)


@router.get(
    "/sports/{sport_id}/ranking",
    response_model=SportRanking,
    responses=ERRORS,
    tags=["sports"],
)
def sport_ranking(sport_id: int, service: Service) -> SportRanking:
    return service.ranking(sport_id)


@router.get(
    "/sports/{sport_id}/statistics",
    response_model=SportStatistics,
    responses=ERRORS,
    tags=["sports"],
)
def sport_statistics(sport_id: int, service: Service) -> SportStatistics:
    return service.statistics(sport_id)


@router.get("/rankings", response_model=AggregatedRankings, tags=["async"])
async def aggregated_rankings(
    request: Request,
    sport_id: Annotated[list[int], Query(min_length=1, max_length=10)],
) -> AggregatedRankings:
    client: RankingClient = request.app.state.ranking_client
    return await client.fetch_many(sport_id)


def error_response(code: int, name: str, error: Exception) -> JSONResponse:
    return JSONResponse(status_code=code, content={"error": name, "detail": str(error)})


def create_app(
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    config = settings or get_settings()
    setup_logging(config.log_level, config.is_production)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if config.auto_migrate:
            upgrade(config.database_url)
        engine = make_engine(config.database_url)
        Base.metadata.create_all(engine)
        app.state.engine = engine
        app.state.settings = config
        app.state.ranking_cache = RankingCache()
        app.state.session_factory = make_session_factory(engine)
        if config.seed_data:
            with app.state.session_factory() as session:
                seed(session)
        logger.info("Started sport-results %s in %s mode", __version__, config.app_env)
        async with httpx.AsyncClient(
            base_url=config.api_base_url,
            transport=transport or httpx.AsyncHTTPTransport(),
        ) as client:
            app.state.ranking_client = RankingClient(
                client,
                config.api_timeout,
                config.api_retries,
                config.api_concurrency,
                config.api_backoff,
            )
            yield
        engine.dispose()

    app = FastAPI(
        title="Sport Results API",
        version=__version__,
        description="REST API обліку спортивних результатів (варіант 9).",
        lifespan=lifespan,
        docs_url=None if config.is_production else "/docs",
    )
    app.include_router(router)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health(request: Request) -> HealthResponse | JSONResponse:
        try:
            database = "ok" if ping(request.app.state.engine) else "error"
        except Exception:
            logger.exception("Database health check failed")
            database = "error"
        body = HealthResponse(
            status="ok" if database == "ok" else "degraded",
            version=__version__,
            environment=config.app_env,
            database=database,
        )
        if database != "ok":
            return JSONResponse(status_code=503, content=body.model_dump())
        return body

    @app.exception_handler(NotFoundError)
    async def not_found(request: Request, error: NotFoundError) -> JSONResponse:
        return error_response(404, "not_found", error)

    @app.exception_handler(DuplicateError)
    async def duplicate(request: Request, error: DuplicateError) -> JSONResponse:
        return error_response(409, "conflict", error)

    @app.exception_handler(TransactionError)
    async def rejected(request: Request, error: TransactionError) -> JSONResponse:
        return error_response(422, "transaction_rejected", error)

    @app.exception_handler(SportResultsError)
    async def generic(request: Request, error: SportResultsError) -> JSONResponse:
        return error_response(400, "bad_request", error)

    return app
