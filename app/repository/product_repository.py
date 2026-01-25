"""Order repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_repository import BaseRepository
from app.models.product import Product


class ProductRepository(BaseRepository[Product, int]):
    """Repository for Product entity operations.

    Provides database access methods specific to Product entities,
    including search and filtering capabilities.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize ProductRepository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        super().__init__(Product, session)

    async def search(
        self,
        search_term: str | None = None,
        department: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Product]:
        """Search products by name or department.

        Args:
            search_term: Text to search for in name
            department: Filter by specific department
            limit: Maximum number of results to return
            offset: Number of records to skip

        Returns:
            List of matching Product instances
        """
        query = select(self.model).order_by(self.model.created_at.desc())

        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(self.model.name.ilike(search_pattern))

        if department:
            query = query.where(self.model.department == department)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_department(
        self, department: str, limit: int | None = None, offset: int | None = None
    ) -> list[Product]:
        """Get products by department.

        Args:
            department: Department name to filter by
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of Product instances in the specified department
        """
        return await self.filter(department=department, limit=limit, offset=offset)

    async def get_products_by_price_range(
        self,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Product]:
        """Get products within a price range.

        Args:
            min_price: Minimum price (inclusive)
            max_price: Maximum price (inclusive)
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of Product instances within the price range
        """
        query = select(self.model).order_by(self.model.price)

        if min_price is not None:
            query = query.where(self.model.price >= min_price)
        if max_price is not None:
            query = query.where(self.model.price <= max_price)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
