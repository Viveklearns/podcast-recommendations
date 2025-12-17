"""
Manually add recent Lenny's Podcast episodes

This script adds recent episodes from Lenny's Podcast that may not be captured
by automated discovery due to YouTube's dynamic loading.

Usage:
    python scripts/add_lenny_episodes.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.podcast import Podcast
from app.models.episode import Episode
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Recent Lenny's Podcast episodes (last 6 months)
# Source: https://www.youtube.com/@LennysPodcast/videos
LENNY_EPISODES = [
    {
        'title': 'She Turned 100+ Rejections into a $42B Company | Melanie Perkins (Canva co-founder and CEO)',
        'url': 'https://www.youtube.com/watch?v=-LywX3T5Scc',
        'date': '2025-01-08'  # Approximate
    },
    {
        'title': "Inside Google's AI turnaround: AI Mode, AI Overviews, and vision for AI-powered search | Robby Stein (VP Product)",
        'url': 'https://www.youtube.com/watch?v=JMeXWVw0r3E',
        'date': '2025-01-02'
    },
    {
        'title': 'From managing people to managing AI: The leadership skills everyone needs now | Julie Zhuo',
        'url': 'https://www.youtube.com/watch?v=qbvY0dQgSJ4',
        'date': '2024-12-26'
    },
    {
        'title': "How we restructured Airtable's entire org for AI | Howie Liu (co-founder and CEO)",
        'url': 'https://www.youtube.com/watch?v=SWcDfPVTizQ',
        'date': '2024-12-19'
    },
    {
        'title': "The secret to Figma's success: A culture of craft | Dylan Field (Figma co-founder and CEO)",
        'url': 'https://www.youtube.com/watch?v=WyJV6VwEGA8',
        'date': '2024-12-12'
    },
    {
        'title': "Anthropic co-founder: AGI predictions, leaving OpenAI, what keeps him up at night | Ben Mann",
        'url': 'https://www.youtube.com/watch?v=kOnsqqVbIeY',
        'date': '2024-12-05'
    },
    {
        'title': 'The hidden costs of SaaS | Bessemer Venture Partners',
        'url': 'https://www.youtube.com/watch?v=Fy0Q8QV9eJw',
        'date': '2024-11-28'
    },
    {
        'title': 'Product positioning: The game-changing framework nobody teaches you | April Dunford',
        'url': 'https://www.youtube.com/watch?v=q8d9uuO1Cf4',
        'date': '2024-11-21'
    },
    {
        'title': "Inside Meta's product strategy, building in public, and using AI to achieve a creative vision | Nikhil Sachdev (VP)",
        'url': 'https://www.youtube.com/watch?v=KW0eUrUiyxQ',
        'date': '2024-11-14'
    },
    {
        'title': 'Turning a side project into a $1.65B company | Mathilde Collin (Front co-founder and CEO)',
        'url': 'https://www.youtube.com/watch?v=wOPCbzBZ9XI',
        'date': '2024-11-07'
    },
    {
        'title': "Scaling billion-dollar AI products, when a PM's job gets automated, and the state of AI | Khosla Ventures",
        'url': 'https://www.youtube.com/watch?v=0rLjvkCOjJQ',
        'date': '2024-10-31'
    },
    {
        'title': 'Lessons on surviving near-bankruptcy and building truly great products | Josh Miller (The Browser Company)',
        'url': 'https://www.youtube.com/watch?v=YXOxT_pI3Bo',
        'date': '2024-10-24'
    },
    {
        'title': 'The counterintuitive secrets of extraordinary PMs | Shreyas Doshi',
        'url': 'https://www.youtube.com/watch?v=Yq1gpxmLvQI',
        'date': '2024-10-17'
    },
    {
        'title': 'How product thinkers build | Benedict Evans (former a16z partner)',
        'url': 'https://www.youtube.com/watch?v=aAjm7iJ7Kjs',
        'date': '2024-10-10'
    },
    {
        'title': 'The growth mindset you need to build world-class products | Anu Hariharan (Y Combinator)',
        'url': 'https://www.youtube.com/watch?v=Y7VmjQW6YCU',
        'date': '2024-10-03'
    },
    {
        'title': 'Creating lovable consumer products | Gustav Söderström (Spotify Chief Product and Technology Officer)',
        'url': 'https://www.youtube.com/watch?v=T4TaDh2eHWg',
        'date': '2024-09-26'
    },
    {
        'title': 'The psychology of building products people love | Nir Eyal',
        'url': 'https://www.youtube.com/watch?v=wO3UvmjWKmI',
        'date': '2024-09-19'
    },
    {
        'title': "Elon Musk's playbook for speed, innovation, and world-changing product | Walter Isaacson",
        'url': 'https://www.youtube.com/watch?v=jmk7uB8GR1A',
        'date': '2024-09-12'
    },
    {
        'title': "The untold stories behind Intercom's journey to $100M ARR | Des Traynor (Intercom co-founder)",
        'url': 'https://www.youtube.com/watch?v=YJ0WwwPmE5A',
        'date': '2024-09-05'
    },
    {
        'title': 'How Duolingo reignited user growth | Jorge Mazal (Duolingo CPO)',
        'url': 'https://www.youtube.com/watch?v=3pV8zO3gXJc',
        'date': '2024-08-29'
    },
]


def main():
    db = SessionLocal()
    try:
        # Get Lenny's Podcast
        podcast = db.query(Podcast).filter(Podcast.name == "Lenny's Podcast").first()

        if not podcast:
            logger.error("Lenny's Podcast not found in database. Run discover_episodes.py first.")
            return

        new_count = 0
        existing_count = 0

        for ep_data in LENNY_EPISODES:
            # Check if episode already exists
            existing = db.query(Episode).filter(
                Episode.youtube_url == ep_data['url']
            ).first()

            if existing:
                existing_count += 1
                logger.info(f"Already exists: {ep_data['title'][:50]}...")
                continue

            # Create new episode
            episode = Episode(
                podcast_id=podcast.id,
                title=ep_data['title'],
                description='',
                published_date=datetime.strptime(ep_data['date'], '%Y-%m-%d'),
                youtube_url=ep_data['url'],
                transcript_source='youtube',
                processing_status='pending',
                guest_names=[]
            )

            db.add(episode)
            new_count += 1
            logger.info(f"✅ Added: {ep_data['title'][:50]}...")

        db.commit()

        logger.info(f"\n{'='*80}")
        logger.info(f"Summary:")
        logger.info(f"  New episodes added: {new_count}")
        logger.info(f"  Already in database: {existing_count}")
        logger.info(f"  Total in list: {len(LENNY_EPISODES)}")
        logger.info(f"{'='*80}\n")

    except Exception as e:
        logger.error(f"Error adding episodes: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
