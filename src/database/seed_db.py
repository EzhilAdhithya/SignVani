"""
Seed Database

Populates the SQLite database with initial ISL glosses and HamNoSys mappings.
"""

import logging
from src.database.db_manager import DatabaseManager
from src.utils.exceptions import SeedDataError

logger = logging.getLogger(__name__)

# Placeholder HamNoSys strings (real data to be provided by linguistics team)
# Format: HamNoSys string representation
INITIAL_GLOSSES = {
    'HELLO': 'hamfinger2,hamthumboutmod,hamextfingeru,hampalmd,hamshoulders,hamplus',
    'WORLD': 'hamfist,hamextfingeru,hampalmd,hamchest,hamcircle',
    'WELCOME': 'hamflat,hampalmu,hamchest,hammoveo,hamarcu',
    'GOOD': 'hamfist,hamthumboutmod,hamextfingeru,hampalml,hamchest,hammoveo',
    'MORNING': 'hamflat,hampalmu,hamchest,hammoveu,hamarcr',
    'THANK YOU': 'hamflat,hampalmu,hamchin,hammoveo',
    'PLEASE': 'hamflat,hampalml,hamchest,hamcircle',
    'SORRY': 'hamfist,hamextfingeru,hampalmd,hamchest,hamrepeat',
    'YES': 'hamfist,hamthumboutmod,hamextfingeru,hampalmd,hammoved',
    'NO': 'hamfist,hamthumboutmod,hamextfingeru,hampalmd,hammover',
    'HELP': 'hamflat,hampalml,hamchest,hammoveo',
    'NAME': 'hamfinger2,hamthumboutmod,hamextfingeru,hampalmd,hamchest,hammover',
    'I': 'hamfinger2,hamthumboutmod,hamextfingeru,hampalmd,hamchest',
    'YOU': 'hamfinger2,hamthumboutmod,hamextfingeru,hampalmd,hamshoulders,hammoveo',
}


def seed_database():
    """
    Populate the database with initial gloss mappings.
    """
    db_manager = DatabaseManager()

    try:
        with db_manager.get_connection() as conn:
            count = 0
            for gloss, hamnosys in INITIAL_GLOSSES.items():
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO gloss_mapping (english_gloss, hamnosys_string, category, frequency)
                    VALUES (?, ?, 'common', 100)
                    """,
                    (gloss, hamnosys)
                )
                if cursor.rowcount > 0:
                    count += 1

            conn.commit()
            logger.info(
                f"Database seeded with {count} new glosses (Total: {len(INITIAL_GLOSSES)})")
            print(f"✓ Database seeded with {count} new glosses")

    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
        raise SeedDataError(f"Database seeding failed: {e}")


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    seed_database()
