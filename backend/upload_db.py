#!/usr/bin/env python3
"""
Upload local database to Render backend via API
"""
import sqlite3
import requests
import json

# Local database
LOCAL_DB = "podcast_recs.db"
# Your Render backend URL
BACKEND_URL = "https://podcast-recommendations.onrender.com"

def get_local_data():
    """Extract all data from local database"""
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all recommendations
    cursor.execute("""
        SELECT id, episode_id, type, title, recommendation_context,
               quote_from_episode, timestamp_seconds, recommended_by,
               confidence_score, model_used, extra_metadata,
               created_at, updated_at
        FROM recommendations
    """)

    recommendations = []
    for row in cursor.fetchall():
        rec = dict(row)
        # Parse JSON field
        if rec['extra_metadata']:
            rec['extra_metadata'] = json.loads(rec['extra_metadata'])
        recommendations.append(rec)

    conn.close()
    return recommendations

def upload_to_render(recommendations):
    """Upload recommendations to Render backend"""
    print(f"\n📤 Uploading {len(recommendations)} recommendations to Render...\n")

    # Upload in batches of 100
    batch_size = 100
    for i in range(0, len(recommendations), batch_size):
        batch = recommendations[i:i+batch_size]

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/admin/bulk-upload",
                json={"recommendations": batch},
                timeout=30
            )

            if response.status_code == 200:
                print(f"✅ Uploaded batch {i//batch_size + 1} ({len(batch)} items)")
            else:
                print(f"❌ Failed batch {i//batch_size + 1}: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error uploading batch {i//batch_size + 1}: {e}")

if __name__ == "__main__":
    print("🚀 Starting database upload to Render...")
    data = get_local_data()
    print(f"📊 Found {len(data)} recommendations locally")

    # For now, just save to JSON file - we'll upload via different method
    output_file = "recommendations_export.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Exported data to {output_file}")
    print(f"📁 File size: {len(json.dumps(data)) / 1024 / 1024:.2f} MB")
    print("\nNext: We'll need to copy your local database file to Render")
