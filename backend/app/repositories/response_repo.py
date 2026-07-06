from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.response import Response
from app.repositories.base import BaseRepository


class ResponseRepository(BaseRepository[Response]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Response)

    async def list_for_survey(self, survey_id: str) -> list[Response]:
        return await self.list(survey_id=survey_id)

    async def list_for_persona(self, persona_id: str) -> list[Response]:
        return await self.list(persona_id=persona_id)

    async def delete_for_survey(self, survey_id: str) -> None:
        await self.session.execute(delete(Response).where(Response.survey_id == survey_id))
        await self.session.flush()

    async def delete_for_persona(self, persona_id: str) -> None:
        await self.session.execute(delete(Response).where(Response.persona_id == persona_id))
        await self.session.flush()
