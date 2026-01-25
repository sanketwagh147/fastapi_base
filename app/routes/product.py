"""Order routes for CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncDBPool
from app.repository.product_repository import ProductRepository

router = APIRouter(
    prefix="/api/product",
    tags=["product"],
)


# Pydantic models for request/response
class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the product")
    department: str = Field(..., min_length=1, max_length=255, description="Department")
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    weight: float = Field(..., gt=0, description="Weight must be greater than 0")

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = Field(None, min_length=1, max_length=255)
    department: str | None = Field(None, min_length=1, max_length=255)
    price: float | None = Field(None, gt=0)
    weight: float | None = Field(None, gt=0)

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    """Schema for product response."""

    id: int
    name: str
    department: str
    price: float
    weight: float

    model_config = {"from_attributes": True}


class ProductSummaryResponse(BaseModel):
    """Schema for product summary response."""

    id: int
    name: str
    department: str
    price: float

    model_config = {"from_attributes": True}


async def get_db_session():
    """Dependency to get database session."""
    async with AsyncDBPool.get_session() as session:
        yield session


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate, session: AsyncSession = Depends(get_db_session)):
    """Create a new product."""
    repo = ProductRepository(session)

    new_product = await repo.create(
        name=product.name, department=product.department, price=product.price, weight=product.weight
    )

    await session.commit()
    return new_product.to_dict()


@router.get("/", response_model=list[ProductSummaryResponse])
async def get_products(
    search: str | None = Query(None, description="Search term for product name"),
    department: str | None = Query(None, description="Filter by department"),
    limit: int | None = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int | None = Query(0, ge=0, description="Records to skip"),
    session: AsyncSession = Depends(get_db_session),
):
    """Get all products with optional filtering."""
    repo = ProductRepository(session)

    if search or department:
        products = await repo.search(
            search_term=search, department=department, limit=limit, offset=offset
        )
    else:
        products = await repo.get_all(limit=limit, offset=offset)

    return [product.to_summary_dict() for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, session: AsyncSession = Depends(get_db_session)):
    """Get a specific product by ID."""
    repo = ProductRepository(session)
    product = await repo.get_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    return product.to_dict()


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, product_update: ProductUpdate, session: AsyncSession = Depends(get_db_session)
):
    """Update an existing product."""
    repo = ProductRepository(session)

    # Check if product exists
    existing_product = await repo.get_by_id(product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    # Update only provided fields
    update_data = product_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    updated_product = await repo.update(product_id, **update_data)
    await session.commit()

    return updated_product.to_dict()


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int, session: AsyncSession = Depends(get_db_session)):
    """Delete a product."""
    repo = ProductRepository(session)

    deleted = await repo.delete(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    await session.commit()


@router.get("/department/{department}", response_model=list[ProductSummaryResponse])
async def get_orders_by_department(
    department: str,
    limit: int | None = Query(100, ge=1, le=1000),
    offset: int | None = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """Get all orders for a specific department."""
    repo = ProductRepository(session)
    orders = await repo.get_by_department(department, limit=limit, offset=offset)

    return [order.to_summary_dict() for order in orders]


@router.get("/price-range/search", response_model=list[ProductSummaryResponse])
async def get_products_by_price_range(
    min_price: float | None = Query(None, ge=0, description="Minimum price"),
    max_price: float | None = Query(None, ge=0, description="Maximum price"),
    limit: int | None = Query(100, ge=1, le=1000),
    offset: int | None = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """Get products within a price range."""
    repo = ProductRepository(session)
    products = await repo.get_products_by_price_range(
        min_price=min_price, max_price=max_price, limit=limit, offset=offset
    )

    return [product.to_summary_dict() for product in products]
