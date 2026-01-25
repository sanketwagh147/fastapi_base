"""
Async script to migrate data from JSON files to SQLAlchemy database.
Run this once to populate the database with existing data.

Usage:
    uv run python scripts/migrate_data.py
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.core import AsyncDBPool, DBConfig
from app.models import Event, Image
from app.repository import EventRepository, ImageRepository


async def load_json_data(file_path: str):
    """Load data from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


async def migrate_events(json_file: str):
    """Migrate events from JSON file to database."""
    print(f"Loading events from {json_file}...")
    events_data = await load_json_data(json_file)
    
    migrated_count = 0
    async with AsyncDBPool.get_session() as session:
        repo = EventRepository(session)
        
        for event_data in events_data:
            # Parse date and time
            date_str = event_data.get('date')
            time_str = event_data.get('time')
            
            event = await repo.create(
                title=event_data['title'],
                description=event_data['description'],
                date=datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None,
                time=datetime.strptime(time_str, '%H:%M').time() if time_str else None,
                location=event_data['location'],
                image=event_data['image']
            )
            
            migrated_count += 1
        
        await session.commit()
    
    print(f"✓ Migrated {migrated_count} events")


async def migrate_images(json_file: str):
    """Migrate images from JSON file to database."""
    print(f"Loading images from {json_file}...")
    images_data = await load_json_data(json_file)
    
    migrated_count = 0
    async with AsyncDBPool.get_session() as session:
        repo = ImageRepository(session)
        
        for image_data in images_data:
            # Check if image already exists
            if await repo.path_exists(image_data['path']):
                print(f"  Skipping {image_data['path']} (already exists)")
                continue
            
            await repo.create(
                path=image_data['path'],
                caption=image_data.get('caption', '')
            )
            
            migrated_count += 1
        
        await session.commit()
    
    print(f"✓ Migrated {migrated_count} images")


async def main():
    """Main migration function."""
    print("=" * 60)
    print("Eventually App - Data Migration")
    print("=" * 60)
    
    # Get the path to the data files
    backend_dir = Path(__file__).parent.parent / 'backend'
    events_file = backend_dir / 'data' / 'events.json'
    images_file = backend_dir / 'data' / 'images.json'
    
    # Check if files exist
    if not events_file.exists():
        print(f"Error: Events file not found at {events_file}")
        return
    
    if not images_file.exists():
        print(f"Error: Images file not found at {images_file}")
        return
    
    # Initialize database
    print("\nInitializing database...")
    config = DBConfig(
        url="sqlite+aiosqlite:///./eventually.db",
        echo=True
    )
    await AsyncDBPool.init(config)
    
    # Create tables (you'll need to add this to your Base class)
    # from app.models.base import Base
    # async with AsyncDBPool._engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    try:
        # Migrate data
        print("\nMigrating data...\n")
        await migrate_images(str(images_file))
        await migrate_events(str(events_file))
        
        # Show summary
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
        async with AsyncDBPool.get_session() as session:
            event_repo = EventRepository(session)
            image_repo = ImageRepository(session)
            
            event_count = await event_repo.count()
            image_count = await image_repo.count()
            
            print(f"\nDatabase summary:")
            print(f"  Events: {event_count}")
            print(f"  Images: {image_count}")
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        raise
    
    finally:
        await AsyncDBPool.dispose()


if __name__ == "__main__":
    asyncio.run(main())
