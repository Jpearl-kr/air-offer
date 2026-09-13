from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Route


async def get_or_create_route_id(db: AsyncSession, origin: str, destination: str) -> int:
    route = await db.scalar(select(Route).where(Route.origin == origin, Route.destination == destination))
    if route is None:
        route = Route(origin=origin, destination=destination)
        db.add(route)
        await db.flush()
    return route.id
