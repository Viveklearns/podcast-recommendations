#!/usr/bin/env python3
"""
Enhance book themes and categorization using Claude AI
"""
import sys
import os
import json
import time
from anthropic import Anthropic
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

from app.database import SessionLocal
from app.models.recommendation import Recommendation
from sqlalchemy.orm.attributes import flag_modified

# Initialize Claude
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def analyze_book_themes(title, author, description, existing_categories, recommendation_context):
    """Use Claude to analyze book and extract detailed themes"""

    prompt = f"""Analyze this book and provide detailed categorization in JSON format.

Book Information:
- Title: {title}
- Author: {author}
- Description: {description or 'N/A'}
- Existing Categories: {', '.join(existing_categories) if existing_categories else 'None'}
- Recommendation Context: {recommendation_context or 'N/A'}

Please provide a JSON response with the following structure:
{{
  "primaryTheme": "Main genre or theme (e.g., 'Entrepreneurship & Startups', 'Literary Fiction', 'Psychology')",
  "subthemes": ["Array of 2-4 specific subthemes"],
  "topics": ["Array of 3-5 topic keywords"],
  "targetAudience": "Who should read this book",
  "fictionType": "Type of fiction (Sci-Fi, Thriller, Literary, Romance, etc.) or null if non-fiction",
  "businessCategory": "Business category (Strategy, Marketing, Leadership, etc.) or null if not a business book",
  "style": "Writing or content style (e.g., 'Prescriptive', 'Narrative', 'Academic', 'Conversational')"
}}

Rules:
- Be specific and accurate based on the book information
- Use null for fields that don't apply
- Keep categories concise but descriptive
- Focus on what makes this book unique
- Consider the recommendation context to understand why it was recommended

Return ONLY valid JSON, no other text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract JSON from response
        content = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()

        themes = json.loads(content)
        return themes

    except Exception as e:
        print(f"  ⚠️  Claude error: {e}")
        return None


def main():
    db = SessionLocal()

    try:
        # Get all books
        all_books = db.query(Recommendation).filter(
            Recommendation.type == 'book'
        ).all()

        print(f"\n📚 Enhancing themes for {len(all_books)} books\n")
        print(f"⚠️  This will make {len(all_books)} Claude API calls")
        print(f"💰 Estimated cost: ${len(all_books) * 0.02:.2f}\n")

        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

        updated_count = 0
        skipped_count = 0
        error_count = 0

        for i, book in enumerate(all_books, 1):
            print(f"\n[{i}/{len(all_books)}] {book.title}")

            metadata = book.extra_metadata or {}

            # Skip if already has enhanced themes
            if metadata.get('primaryTheme'):
                print(f"  ⏭️  Already enhanced, skipping")
                skipped_count += 1
                continue

            # Get existing data
            description = metadata.get('description', '')
            existing_categories = metadata.get('categories', [])
            author = metadata.get('author', '')

            # Analyze with Claude
            print(f"  🤖 Analyzing with Claude...")
            themes = analyze_book_themes(
                title=book.title,
                author=author,
                description=description,
                existing_categories=existing_categories,
                recommendation_context=book.recommendation_context
            )

            if themes:
                # Update metadata with enhanced themes
                metadata.update(themes)
                book.extra_metadata = metadata
                flag_modified(book, 'extra_metadata')
                updated_count += 1

                print(f"  ✅ Theme: {themes.get('primaryTheme')}")
                if themes.get('fictionType'):
                    print(f"     Fiction Type: {themes.get('fictionType')}")
                if themes.get('businessCategory'):
                    print(f"     Business Category: {themes.get('businessCategory')}")
            else:
                error_count += 1
                print(f"  ❌ Failed to analyze")

            # Rate limiting - be conservative with Claude API
            time.sleep(1)

            # Commit every 10 books
            if i % 10 == 0:
                db.commit()
                print(f"\n💾 Saved progress ({updated_count} books enhanced so far)\n")

        # Final commit
        db.commit()

        print(f"\n" + "="*60)
        print(f"✅ Theme Enhancement Complete!")
        print(f"="*60)
        print(f"Total books processed: {len(all_books)}")
        print(f"Books enhanced: {updated_count}")
        print(f"Already had themes: {skipped_count}")
        print(f"Errors: {error_count}")
        print(f"="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
