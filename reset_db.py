import logging
from database import engine, Base
# Import all models so that they are registered with the Base metadata
import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    logger.info("Dropping all tables from the database...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Tables dropped successfully.")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        return

    logger.info("Creating all tables in the database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

if __name__ == "__main__":
    logger.info("Starting database reset process.")
    reset_database()
    logger.info("Database reset process finished.")
