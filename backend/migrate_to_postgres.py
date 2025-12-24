#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL
"""
import sqlite3
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Source: SQLite
SQLITE_DB = "podcast_recs.db"

# Destination: PostgreSQL
POSTGRES_URL = "postgresql://podbooks_db_user:6eSXjFNwNvqX8RqNo91J2YbmrXgHv3PW@dpg-d54vc00gjchc73862ubg-a.oregon-postgres.render.com/podbooks_db"

def migrate():
    print("🚀 Starting migration from SQLite to PostgreSQL...")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_engine = create_engine(POSTGRES_URL)

    # Create tables in PostgreSQL
    print("\n📋 Creating tables in PostgreSQL...")
    from app.database import Base
    from app.models import Podcast, Episode, Recommendation
    from app.models.processing_metrics import ProcessingMetrics

    Base.metadata.create_all(bind=pg_engine)
    print("✅ Tables created")

    # Get PostgreSQL session
    Session = sessionmaker(bind=pg_engine)
    pg_session = Session()

    # Migrate podcasts
    print("\n📻 Migrating podcasts...")
    cursor.execute("SELECT * FROM podcasts")
    podcasts = cursor.fetchall()

    for podcast in podcasts:
        pg_session.execute(text("""
            INSERT INTO podcasts (id, name, youtube_channel_id, rss_feed_url, category, image_url, created_at, last_fetched_at)
            VALUES (:id, :name, :youtube_channel_id, :rss_feed_url, :category, :image_url, :created_at, :last_fetched_at)
            ON CONFLICT (id) DO NOTHING
        """), dict(podcast))

    pg_session.commit()
    print(f"✅ Migrated {len(podcasts)} podcasts")

    # Migrate episodes
    print("\n🎙️  Migrating episodes...")
    cursor.execute("SELECT * FROM episodes")
    episodes = cursor.fetchall()

    for episode in episodes:
        ep_dict = dict(episode)
        # Handle JSON fields - convert to JSON string for PostgreSQL
        if ep_dict['transcript_metadata']:
            ep_dict['transcript_metadata'] = ep_dict['transcript_metadata']  # Keep as JSON string
        if ep_dict['claude_processing_metadata']:
            ep_dict['claude_processing_metadata'] = ep_dict['claude_processing_metadata']  # Keep as JSON string

        pg_session.execute(text("""
            INSERT INTO episodes (
                id, podcast_id, title, description, published_date, duration_seconds,
                youtube_url, audio_url, transcript_url, guest_names, transcript_source,
                processing_status, processed_at, created_at, transcript_metadata,
                claude_processing_metadata
            ) VALUES (
                :id, :podcast_id, :title, :description, :published_date, :duration_seconds,
                :youtube_url, :audio_url, :transcript_url, :guest_names, :transcript_source,
                :processing_status, :processed_at, :created_at, CAST(:transcript_metadata AS jsonb),
                CAST(:claude_processing_metadata AS jsonb)
            ) ON CONFLICT (id) DO NOTHING
        """), ep_dict)

    pg_session.commit()
    print(f"✅ Migrated {len(episodes)} episodes")

    # Migrate recommendations
    print("\n📚 Migrating recommendations...")
    cursor.execute("SELECT * FROM recommendations")
    recommendations = cursor.fetchall()

    count = 0
    for rec in recommendations:
        rec_dict = dict(rec)
        # Handle JSON field - keep as JSON string for PostgreSQL
        if rec_dict['extra_metadata']:
            rec_dict['extra_metadata'] = rec_dict['extra_metadata']  # Keep as JSON string

        pg_session.execute(text("""
            INSERT INTO recommendations (
                id, episode_id, type, title, recommendation_context, quote_from_episode,
                timestamp_seconds, recommended_by, confidence_score, model_used,
                extra_metadata, created_at, updated_at
            ) VALUES (
                :id, :episode_id, :type, :title, :recommendation_context, :quote_from_episode,
                :timestamp_seconds, :recommended_by, :confidence_score, :model_used,
                CAST(:extra_metadata AS jsonb), :created_at, :updated_at
            ) ON CONFLICT (id) DO NOTHING
        """), rec_dict)

        count += 1
        if count % 100 == 0:
            print(f"   Migrated {count}/{len(recommendations)} recommendations...")
            pg_session.commit()

    pg_session.commit()
    print(f"✅ Migrated {len(recommendations)} recommendations")

    # Verify
    print("\n🔍 Verifying migration...")
    result = pg_session.execute(text("SELECT COUNT(*) FROM recommendations WHERE type = 'book'")).fetchone()
    print(f"   Books in PostgreSQL: {result[0]}")

    sqlite_conn.close()
    pg_session.close()

    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate()
