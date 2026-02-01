import logging
import sqlite3
import os
from pathlib import Path

from app.utils.file_download_utils import FileDownloadUtils
from config import Config

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles migrations for database schema changes"""
    
    @staticmethod
    def run_migrations(db_path):
        """Run any pending migrations on the database"""
        logger.info(f"Checking database migrations for {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if migration_history table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migration_history'")
            if not cursor.fetchone():
                # Create migration tracking table if it doesn't exist
                cursor.execute('''
                CREATE TABLE migration_history (
                    id INTEGER PRIMARY KEY,
                    migration_name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                conn.commit()
            
            # Get list of applied migrations
            cursor.execute("SELECT migration_name FROM migration_history")
            applied_migrations = set(row[0] for row in cursor.fetchall())
            
            # Run migrations that haven't been applied yet
            if 'add_folders_table' not in applied_migrations:
                DatabaseMigrator._add_folders_table(conn, cursor)
                cursor.execute("INSERT INTO migration_history (migration_name) VALUES ('add_folders_table')")
                conn.commit()
                logger.info("Applied migration: add_folders_table")
            
            if 'add_folder_fields_to_playlists' not in applied_migrations:
                DatabaseMigrator._add_folder_fields_to_playlists(conn, cursor)
                cursor.execute("INSERT INTO migration_history (migration_name) VALUES ('add_folder_fields_to_playlists')")
                conn.commit()
                logger.info("Applied migration: add_folder_fields_to_playlists")
            
            if 'add_disabled_field_to_folders' not in applied_migrations:
                DatabaseMigrator._add_disabled_field_to_folders(conn, cursor)
                cursor.execute("INSERT INTO migration_history (migration_name) VALUES ('add_disabled_field_to_folders')")
                conn.commit()
                logger.info("Applied migration: add_disabled_field_to_folders")
            
            if 'add_expanded_field_to_folders' not in applied_migrations:
                DatabaseMigrator._add_expanded_field_to_folders(conn, cursor)
                cursor.execute("INSERT INTO migration_history (migration_name) VALUES ('add_expanded_field_to_folders')")
                conn.commit()
                logger.info("Applied migration: add_expanded_field_to_folders")
            
            if 'convert_absolute_paths_to_relative' not in applied_migrations:
                DatabaseMigrator._convert_absolute_paths_to_relative(conn, cursor)
                cursor.execute("INSERT INTO migration_history (migration_name) VALUES ('convert_absolute_paths_to_relative')")
                conn.commit()
                logger.info("Applied migration: convert_absolute_paths_to_relative")
            
            # Add order_index to tracklist_entries if needed
            if 'add_order_index_to_tracklist_entries' not in applied_migrations:
                DatabaseMigrator._add_order_index_to_tracklist_entries(conn, cursor)
                cursor.execute("INSERT INTO migration_history (migration_name) VALUES ('add_order_index_to_tracklist_entries')")
                conn.commit()
                logger.info("Applied migration: add_order_index_to_tracklist_entries")

            conn.close()
            logger.info("Database migration completed successfully")
            
        except Exception as e:
            logger.error(f"Error during database migration: {str(e)}")
            if conn:
                conn.close()
    
    @staticmethod
    def _add_folders_table(conn, cursor):
        """Add the folders table to the database"""
        # Check if folders table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
        if cursor.fetchone():
            logger.info("Folders table already exists, skipping creation")
            return
        
        # Create the folders table
        cursor.execute('''
        CREATE TABLE folders (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            parent_id INTEGER,
            custom_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES folders (id)
        )
        ''')
        conn.commit()
    
    @staticmethod
    def _add_folder_fields_to_playlists(conn, cursor):
        """Add folder_id and custom_order fields to playlists table"""
        # Check if columns exist
        cursor.execute("PRAGMA table_info(playlists)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # Add folder_id if it doesn't exist
            if 'folder_id' not in columns:
                cursor.execute("ALTER TABLE playlists ADD COLUMN folder_id INTEGER")
                cursor.execute("CREATE INDEX idx_playlists_folder_id ON playlists(folder_id)")
            
            # Add custom_order if it doesn't exist
            if 'custom_order' not in columns:
                cursor.execute("ALTER TABLE playlists ADD COLUMN custom_order INTEGER NOT NULL DEFAULT 0")
                
                # Set initial custom_order based on id to maintain existing order
                cursor.execute("SELECT id FROM playlists ORDER BY id")
                for i, (playlist_id,) in enumerate(cursor.fetchall()):
                    cursor.execute("UPDATE playlists SET custom_order = ? WHERE id = ?", (i, playlist_id))
            
            # Commit transaction
            conn.commit()
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            logger.error(f"Error adding folder fields to playlists: {str(e)}")
            raise
            
    @staticmethod
    def _add_disabled_field_to_folders(conn, cursor):
        """Add disabled field to folders table"""
        # Check if column exists
        cursor.execute("PRAGMA table_info(folders)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add disabled column if it doesn't exist
        if 'disabled' not in columns:
            cursor.execute("ALTER TABLE folders ADD COLUMN disabled BOOLEAN NOT NULL DEFAULT 1")
            conn.commit()
            logger.info("Added disabled field to folders table")
    
    @staticmethod
    def _add_expanded_field_to_folders(conn, cursor):
        """Add expanded field to folders table"""
        # Check if column exists
        cursor.execute("PRAGMA table_info(folders)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add expanded column if it doesn't exist
        if 'expanded' not in columns:
            cursor.execute("ALTER TABLE folders ADD COLUMN expanded BOOLEAN NOT NULL DEFAULT 1")
            conn.commit()
            logger.info("Added expanded field to folders table")
    
    @staticmethod
    def _convert_absolute_paths_to_relative(conn, cursor):
        """Convert absolute download paths to relative paths based on DOWNLOAD_FOLDER"""
        logger.info("Converting absolute paths to relative paths")
        
        # Get the download folder from config
        download_folder = Config.DOWNLOAD_FOLDER
        if not download_folder:
            logger.error("Cannot convert paths: DOWNLOAD_FOLDER is not defined in config")
            return
        
        # Make sure download folder path is normalized
        download_folder = os.path.abspath(download_folder)
        
        # Get all tracks with a download location
        cursor.execute("SELECT id, download_location FROM tracks WHERE download_location IS NOT NULL")
        tracks = cursor.fetchall()
        
        tracks_updated = 0
        for track_id, download_location in tracks:
            if not download_location:  # Skip empty paths
                continue
                
            # Skip if already a relative path
            if not os.path.isabs(download_location):
                continue
                
            try:
                # Convert to relative path
                relative_path = FileDownloadUtils.get_relative_path(download_location)
                
                if relative_path and relative_path != download_location:
                    # If conversion succeeded and path changed, update the database
                    cursor.execute(
                        "UPDATE tracks SET download_location = ? WHERE id = ?", 
                        (relative_path, track_id)
                    )
                    tracks_updated += 1
            except Exception as e:
                logger.error(f"Error converting path for track {track_id}: {e}")
        
        conn.commit()
        logger.info(f"Converted {tracks_updated} track paths from absolute to relative format")


    @staticmethod
    def _add_order_index_to_tracklist_entries(conn, cursor):
        """Add order_index column to tracklist_entries table if it doesn't exist"""
        cursor.execute("PRAGMA table_info(tracklist_entries)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'order_index' not in columns:
            cursor.execute("ALTER TABLE tracklist_entries ADD COLUMN order_index INTEGER")
            conn.commit()
            logger.info("Added order_index field to tracklist_entries table")