"""Repository package for domain-specific data access.

Create repository classes extending BaseRepository:

    from app.core import BaseRepository
    from app.models.user import User

    class UserRepository(BaseRepository[User, int]):
        async def find_by_email(self, email: str) -> User | None:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
"""
