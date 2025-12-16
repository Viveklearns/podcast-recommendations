from anthropic import Anthropic
from app.config import settings
import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for using Claude API to extract recommendations from podcast transcripts"""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = model

    def extract_recommendations(self, transcript: str, episode_title: str = "", guest_name: str = "") -> List[Dict]:
        """
        Extract recommendations from a podcast transcript using Claude

        Args:
            transcript: The podcast transcript text
            episode_title: Title of the episode (for context)
            guest_name: Name of the guest (for context)

        Returns:
            List of recommendation dictionaries
        """
        system_prompt = """You are an expert at analyzing podcast transcripts and extracting recommendations.
Your task is to identify when a podcast guest or host explicitly recommends books, movies, TV shows, products, apps, or other resources.

Focus on clear recommendations, not just casual mentions. Look for phrases like:
- "I highly recommend..."
- "You should check out..."
- "My favorite book is..."
- "This changed my life..."
- "I use [product] every day..."

CRITICAL: You MUST return ONLY valid JSON. Do NOT include any explanatory text, markdown, or commentary.
Your entire response must be parseable JSON starting with { and ending with }."""

        user_prompt = f"""Analyze the following podcast transcript and extract all recommendations.

Episode Title: {episode_title}
Guest Name (from title): {guest_name or "To be determined from transcript"}

Transcript:
{transcript}

CRITICAL INSTRUCTIONS FOR GUEST NAME EXTRACTION:
1. The guest name is provided above from the episode title. USE IT for all recommendations.
2. If the guest name above is empty, look at the beginning of the transcript for introductions:
   - "Hi, I'm [Full Name]"
   - "My name is [Full Name]"
   - "This is [Full Name]"
   - "I'm joined by [Full Name]"
   - "Today's guest is [Full Name]"
3. Extract the FULL NAME (first and last name), not just first name
4. NEVER use placeholder names like "Guest 1", "Guest 2", "Guest 3", "Host", "Guest"
5. If you cannot determine a real full name, use "Unknown" and mark confidence as low

For each recommendation found, return a JSON object with:
{{
  "recommendations": [
    {{
      "type": "book|movie|tv_show|podcast|product|app|website|course|other",
      "title": "exact title mentioned (not 'this book' or 'that movie')",
      "author_creator": "author or creator if mentioned (not 'not mentioned')",
      "context": "1-2 sentence summary of why it was recommended",
      "quote": "direct quote from transcript showing the recommendation",
      "confidence": 0.0-1.0,
      "recommended_by": "Use the guest name from above. If guest recommended it, use guest name. If host recommended it, use 'Lenny Rachitsky' (the host's name). NEVER use 'Guest 1', 'Host', etc."
    }}
  ]
}}

CRITICAL REQUIREMENTS FOR BOOKS:
- title: Must be the actual book title, NOT "this book", "that book", "Not specified"
- author_creator: Must be actual author name if mentioned, NOT "Not mentioned", "Not specified"
- recommended_by: Must be real guest name, NOT "Guest 1", "Guest 2", etc.
- If book title is unclear/not mentioned, DO NOT include it

Guidelines:
- Only include items that were EXPLICITLY recommended or highly praised
- Exclude casual mentions or neutral references
- For books, MUST include exact title and author if mentioned
- For movies/TV, include director/creator if mentioned
- Mark confidence as:
  - High (0.9-1.0): Clear, enthusiastic recommendation with exact title
  - Medium (0.6-0.9): Likely recommendation, title mostly clear
  - Low (0.3-0.6): Uncertain mention or unclear title

IMPORTANT: Return ONLY the JSON object. Do NOT include any explanatory text before or after the JSON.
Your response must start with {{ and end with }}. Nothing else."""

        try:
            logger.info(f"Calling Claude API to analyze transcript (length: {len(transcript)})")

            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract the response text
            response_text = message.content[0].text

            logger.info(f"Received response from Claude API")
            logger.debug(f"Claude response: {response_text[:500]}...")

            # Parse JSON response
            try:
                # Strip markdown code blocks if present
                json_text = response_text.strip()
                if json_text.startswith('```json'):
                    json_text = json_text[7:]  # Remove ```json
                if json_text.startswith('```'):
                    json_text = json_text[3:]  # Remove ```
                if json_text.endswith('```'):
                    json_text = json_text[:-3]  # Remove trailing ```
                json_text = json_text.strip()

                result = json.loads(json_text)
                recommendations = result.get('recommendations', [])
                logger.info(f"Extracted {len(recommendations)} recommendations")
                return recommendations
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                logger.error(f"Response was: {response_text}")
                return []

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return []

    def extract_recommendations_smart(
        self,
        transcript: str,
        episode_title: str = "",
        guest_name: str = ""
    ) -> tuple[List[Dict], Dict]:
        """
        Intelligently extract recommendations using single-pass or chunking based on transcript size.

        Decision logic:
        - If transcript < 100,000 characters: Use single-pass (faster, better context)
        - If transcript >= 100,000 characters: Use chunking with 100K chunks

        Args:
            transcript: The full podcast transcript text
            episode_title: Title of the episode (for context)
            guest_name: Name of the guest (for context)

        Returns:
            Tuple of (list of recommendations, processing metadata)
        """
        transcript_length = len(transcript)
        threshold = 100_000  # 100K characters

        logger.info(f"=== SMART PROCESSING START ===")
        logger.info(f"Transcript length: {transcript_length:,} characters")

        if transcript_length < threshold:
            # Single-pass processing
            logger.info(f"Using SINGLE-PASS processing (transcript < {threshold:,} chars)")

            recommendations = self.extract_recommendations(transcript, episode_title, guest_name)

            # Create metadata similar to chunked processing for consistency
            metadata = {
                'processing_mode': 'single_pass',
                'total_chunks': 1,
                'total_characters_sent': transcript_length,
                'first_chunk': {
                    'position': 0,
                    'first_50': transcript[:50] if transcript else ''
                },
                'last_chunk': {
                    'position': 0,
                    'last_50': transcript[-50:] if transcript else ''
                },
                'chunks': [
                    {
                        'chunk': 1,
                        'start': 0,
                        'end': transcript_length,
                        'length': transcript_length
                    }
                ],
                'total_recommendations_found': len(recommendations),
                'unique_recommendations': len(recommendations)
            }

            logger.info(f"Single-pass complete: Found {len(recommendations)} recommendations")
            logger.info(f"=== SMART PROCESSING COMPLETE ===")

            return recommendations, metadata
        else:
            # Chunked processing with larger chunks
            logger.info(f"Using CHUNKED processing (transcript >= {threshold:,} chars)")

            # Import here to avoid circular dependency
            from app.services.youtube_service import YouTubeService

            # Use larger chunks for better context
            chunks = YouTubeService.chunk_transcript(transcript, chunk_size=100_000, overlap=2000)
            logger.info(f"Split into {len(chunks)} chunks of ~100K characters each")

            recommendations, metadata = self.extract_recommendations_from_chunks(
                chunks, episode_title, guest_name
            )

            # Add processing mode to metadata
            metadata['processing_mode'] = 'chunked'

            logger.info(f"=== SMART PROCESSING COMPLETE ===")

            return recommendations, metadata

    def extract_recommendations_from_chunks(
        self,
        chunks: List[str],
        episode_title: str = "",
        guest_name: str = ""
    ) -> tuple[List[Dict], Dict]:
        """
        Process multiple transcript chunks and aggregate recommendations

        Args:
            chunks: List of transcript chunks
            episode_title: Episode title for context
            guest_name: Guest name for context

        Returns:
            Tuple of (deduplicated list of recommendations, processing metadata)
        """
        all_recommendations = []
        total_chunks = len(chunks)
        chunk_metadata = []

        logger.info(f"=== CHUNK PROCESSING START ===")
        logger.info(f"Total chunks to process: {total_chunks}")

        for i, chunk in enumerate(chunks):
            chunk_num = i + 1
            chunk_start_pos = sum(len(chunks[j]) for j in range(i))
            chunk_end_pos = chunk_start_pos + len(chunk)

            # Log chunk details
            chunk_info = {
                'chunk_number': chunk_num,
                'total_chunks': total_chunks,
                'start_position': chunk_start_pos,
                'end_position': chunk_end_pos,
                'chunk_length': len(chunk),
                'first_50_chars': chunk[:50],
                'last_50_chars': chunk[-50:],
                'word_count': len(chunk.split())
            }
            chunk_metadata.append(chunk_info)

            logger.info(f"Processing chunk {chunk_num}/{total_chunks}:")
            logger.info(f"  Position: {chunk_start_pos:,} - {chunk_end_pos:,}")
            logger.info(f"  Length: {len(chunk):,} characters")
            logger.info(f"  Starts: '{chunk[:50]}'...")
            logger.info(f"  Ends: '...{chunk[-50:]}'")

            # Process with Claude
            recs = self.extract_recommendations(chunk, episode_title, guest_name)
            all_recommendations.extend(recs)
            logger.info(f"  Found {len(recs)} recommendations in this chunk")

        # Summary log
        first_chunk = chunk_metadata[0]
        last_chunk = chunk_metadata[-1]
        total_chars_processed = sum(c['chunk_length'] for c in chunk_metadata)

        logger.info(f"=== CHUNK PROCESSING COMPLETE ===")
        logger.info(f"First chunk started at position: {first_chunk['start_position']}")
        logger.info(f"Last chunk ended at position: {last_chunk['end_position']}")
        logger.info(f"Total characters processed: {total_chars_processed:,}")
        logger.info(f"Coverage verification: {total_chars_processed == last_chunk['end_position']}")

        # Deduplicate recommendations based on title
        seen_titles = set()
        unique_recommendations = []

        for rec in all_recommendations:
            title = rec.get('title', '').lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_recommendations.append(rec)

        logger.info(f"After deduplication: {len(unique_recommendations)} unique recommendations")

        # Build processing metadata
        processing_metadata = {
            'total_chunks': total_chunks,
            'total_characters_sent': total_chars_processed,
            'first_chunk': {
                'position': first_chunk['start_position'],
                'first_50': first_chunk['first_50_chars']
            },
            'last_chunk': {
                'position': last_chunk['start_position'],
                'last_50': last_chunk['last_50_chars']
            },
            'chunks': [
                {
                    'chunk': c['chunk_number'],
                    'start': c['start_position'],
                    'end': c['end_position'],
                    'length': c['chunk_length']
                }
                for c in chunk_metadata
            ],
            'total_recommendations_found': len(all_recommendations),
            'unique_recommendations': len(unique_recommendations)
        }

        return unique_recommendations, processing_metadata
