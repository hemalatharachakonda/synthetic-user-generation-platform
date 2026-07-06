from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey import Survey
from app.repositories.base import BaseRepository


class SurveyRepository(BaseRepository[Survey]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Survey)

    async def list_for_experiment(self, experiment_id: str) -> list[Survey]:
        return await self.list(experiment_id=experiment_id)

    async def delete_for_experiment(self, experiment_id: str) -> None:
        await self.session.execute(delete(Survey).where(Survey.experiment_id == experiment_id))
        await self.session.flush()
