import time
import logging
from sqlalchemy.exc import OperationalError


def commit_with_retries(session, max_retries=5, delay=0.5):
    """
    Commit the session with retries if the database is locked.
    """
    for attempt in range(max_retries):
        try:
            session.commit()
            return True
        except OperationalError as e:
            if 'database is locked' in str(e):
                logging.warning(f"SQLite locked, retrying commit (attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
            else:
                raise
    logging.error("Max retries reached. Commit failed due to database lock.")
    return False
