# Scripts Directory

This directory contains utility scripts for database management and data operations.

## Available Scripts

### `migrate_data.py`

Async script to migrate data from JSON files to the database.

**Usage:**
```bash
# Make sure you're in the fastapi-backend directory
uv run python scripts/migrate_data.py
```

**Requirements:**
- JSON data files in `../backend/data/events.json` and `../backend/data/images.json`
- Database connection configured in the script

**What it does:**
1. Initializes async database connection
2. Loads events and images from JSON files
3. Creates database records using repositories
4. Shows migration summary

## Creating New Scripts

When creating new scripts:

1. Import from `app.core` for database access
2. Use async/await patterns
3. Use repositories for data operations
4. Handle errors gracefully
5. Provide clear console output

**Example template:**
```python
import asyncio
from app.core import AsyncDBPool, DBConfig
from app.repository import EventRepository

async def main():
    # Initialize database
    config = DBConfig(database_url="...")
    await AsyncDBPool.init(config)
    
    try:
        # Your logic here
        async with AsyncDBPool.get_session() as session:
            repo = EventRepository(session)
            # ...
    finally:
        await AsyncDBPool.dispose()

if __name__ == "__main__":
    asyncio.run(main())
```
