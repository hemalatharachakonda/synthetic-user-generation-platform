from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user_id
from app.core.database import get_db
from app.exceptions.api_exceptions import NotFoundError
from app.schemas.request.experiment import ExperimentCreateRequest, ExperimentUpdateRequest
from app.schemas.response.experiment import ExperimentListResponse, ExperimentResponse
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    payload: ExperimentCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    # Temporarily bypass auth for testing
    from app.api.v1.deps import get_current_user_id
    owner_id = await get_current_user_id(db)
    service = ExperimentService(db)
    experiment = await service.create(owner_id, payload)
    return experiment


@router.get("", response_model=ExperimentListResponse)
async def list_experiments(
    db: AsyncSession = Depends(get_db),
):
    # Temporarily bypass auth for testing
    from app.api.v1.deps import get_current_user_id
    owner_id = await get_current_user_id(db)
    service = ExperimentService(db)
    experiments = await service.list_for_owner(owner_id)
    return ExperimentListResponse(total=len(experiments), items=experiments)


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    service = ExperimentService(db)
    try:
        return await service.get(experiment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: str, payload: ExperimentUpdateRequest, db: AsyncSession = Depends(get_db)
):
    service = ExperimentService(db)
    try:
        return await service.update(experiment_id, payload)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    service = ExperimentService(db)
    try:
        await service.delete(experiment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
