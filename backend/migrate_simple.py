#!/usr/bin/env python3
"""
Simple migration from SQLite to PostgreSQL using psycopg2
"""
import sqlite3
import psycopg2
import json

# Source: SQLite
SQLITE_DB = "podcast_recs.db"

# Destination: PostgreSQL
POSTGRES_URL = "postgresql://podbooks_db_user:6eSXjFNwNvqX8RqNo91J2YbmrXgHv3PW@dpg-d54vc00gjchc73862ubg-a.oregon-postgres.render.com/podbooks_db"

# Parse URL
parts = POSTGRES_URL.replace("postgresql://", "").split("@")
userpass = parts[0].split(":")
hostdb = parts[1].split("/")

user = userpass[0]
password = userpass[1]
host = hostdb[0]
database = hostdb[1]

def migrate():
    print("🚀 Starting migration from SQLite to PostgreSQL...")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )
    pg_cursor = pg_conn.cursor()

    # Migrate podcasts
    print("\n📻 Migrating podcasts...")
    sqlite_cursor.execute("SELECT * FROM podcasts")
    podcasts = sqlite_cursor.fetchall()

    for podcast in podcasts:
        pg_cursor.execute("""
            INSERT INTO podcasts (id, name, youtube_channel_id, rss_feed_url, category, image_url, created_at, last_fetched_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, tuple(podcast))

    pg_conn.commit()
    print(f"✅ Migrated {len(podcasts)} podcasts")

    # Migrate episodes
    print("\n🎙️  Migrating episodes...")
    sqlite_cursor.execute("SELECT * FROM episodes")
    episodes = sqlite_cursor.fetchall()

    for episode in episodes:
        ep_dict = dict(episode)
        # Keep JSON fields as strings
        pg_cursor.execute("""
            INSERT INTO episodes (
                id, podcast_id, title, description, published_date, duration_seconds,
                youtube_url, audio_url, transcript_url, guest_names, transcript_source,
                processing_status, processed_at, created_at, transcript_metadata,
                claude_processing_metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                CAST(%s AS jsonb), CAST(%s AS jsonb)
            ) ON CONFLICT (id) DO NOTHING
        """, (
            ep_dict['id'], ep_dict['podcast_id'], ep_dict['title'], ep_dict['description'],
            ep_dict['published_date'], ep_dict['duration_seconds'], ep_dict['youtube_url'],
            ep_dict['audio_url'], ep_dict['transcript_url'], ep_dict['guest_names'],
            ep_dict['transcript_source'], ep_dict['processing_status'], ep_dict['processed_at'],
            ep_dict['created_at'], ep_dict['transcript_metadata'], ep_dict['claude_processing_metadata']
        ))

    pg_conn.commit()
    print(f"✅ Migrated {len(episodes)} episodes")

    # Migrate recommendations
    print("\n📚 Migrating recommendations...")
    sqlite_cursor.execute("SELECT * FROM recommendations")
    recommendations = sqlite_cursor.fetchall()

    count = 0
    for rec in recommendations:
        rec_dict = dict(rec)

        pg_cursor.execute("""
            INSERT INTO recommendations (
                id, episode_id, type, title, recommendation_context, quote_from_episode,
                timestamp_seconds, recommended_by, confidence_score, model_used,
                extra_metadata, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                CAST(%s AS jsonb), %s, %s
            ) ON CONFLICT (id) DO NOTHING
        """, (
            rec_dict['id'], rec_dict['episode_id'], rec_dict['type'], rec_dict['title'],
            rec_dict['recommendation_context'], rec_dict['quote_from_episode'],
            rec_dict['timestamp_seconds'], rec_dict['recommended_by'], rec_dict['confidence_score'],
            rec_dict['model_used'], rec_dict['extra_metadata'], rec_dict['created_at'],
            rec_dict['updated_at']
        ))

        count += 1
        if count % 100 == 0:
            print(f"   Migrated {count}/{len(recommendations)} recommendations...")
            pg_conn.commit()

    pg_conn.commit()
    print(f"✅ Migrated {len(recommendations)} recommendations")

    # Verify
    print("\n🔍 Verifying migration...")
    pg_cursor.execute("SELECT COUNT(*) FROM recommendations WHERE type = 'book'")
    book_count = pg_cursor.fetchone()[0]
    print(f"   Books in PostgreSQL: {book_count}")

    sqlite_conn.close()
    pg_cursor.close()
    pg_conn.close()

    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate()
