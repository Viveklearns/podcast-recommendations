# Data Quality & Cost Optimization Improvements

## Questions & Solutions

---

## 1. ✅ Transcript Completeness Verification

### Problem
How do we ensure we're extracting the entire transcript and not getting concatenated or truncated data?

### Current Implementation
```python
# youtube_service.py - get_transcript()
transcript_result = api.fetch(video_id, languages=['en'])
full_transcript = " ".join([snippet.text for snippet in transcript_result.snippets])
```

### Issues to Fix
- No verification of completeness
- No logging of segment counts
- No timestamp validation

### Solution: Add Verification Checks

```python
def get_transcript_with_verification(video_id: str) -> Dict[str, any]:
    """
    Fetch transcript with completeness verification
    Returns dict with transcript and metadata
    """
    try:
        api = YouTubeTranscriptApi()
        transcript_result = api.fetch(video_id, languages=['en'])

        # Extract all segments
        segments = list(transcript_result.snippets)

        # Verification checks
        total_segments = len(segments)
        first_segment = segments[0] if segments else None
        last_segment = segments[-1] if segments else None

        # Calculate total duration covered
        start_time = first_segment.start if first_segment else 0
        end_time = (last_segment.start + last_segment.duration) if last_segment else 0
        duration_covered = end_time - start_time

        # Combine text
        full_transcript = " ".join([s.text for s in segments])
        char_count = len(full_transcript)
        word_count = len(full_transcript.split())

        # Check for gaps (segments should be continuous)
        gaps = []
        for i in range(len(segments) - 1):
            current_end = segments[i].start + segments[i].duration
            next_start = segments[i + 1].start
            gap = next_start - current_end
            if gap > 2.0:  # Gap larger than 2 seconds
                gaps.append({
                    'position': i,
                    'gap_seconds': gap,
                    'time': current_end
                })

        # Log verification results
        logger.info(f"Transcript verification for {video_id}:")
        logger.info(f"  - Total segments: {total_segments}")
        logger.info(f"  - First timestamp: {start_time:.2f}s")
        logger.info(f"  - Last timestamp: {end_time:.2f}s")
        logger.info(f"  - Duration covered: {duration_covered:.2f}s ({duration_covered/60:.1f} minutes)")
        logger.info(f"  - Character count: {char_count:,}")
        logger.info(f"  - Word count: {word_count:,}")
        logger.info(f"  - Gaps found: {len(gaps)}")

        if gaps:
            logger.warning(f"  - Large gaps detected at: {[g['time'] for g in gaps[:5]]}")

        # Quality checks
        is_complete = (
            total_segments > 10 and  # At least 10 segments
            char_count > 1000 and    # At least 1000 characters
            len(gaps) < total_segments * 0.1  # Less than 10% gaps
        )

        return {
            'transcript': full_transcript,
            'metadata': {
                'total_segments': total_segments,
                'start_time': start_time,
                'end_time': end_time,
                'duration_covered_seconds': duration_covered,
                'character_count': char_count,
                'word_count': word_count,
                'gaps_detected': len(gaps),
                'is_complete': is_complete,
                'gaps': gaps[:10]  # Store first 10 gaps
            }
        }

    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        return None
```

### Database Schema Addition
Add to `episodes` table:
```sql
ALTER TABLE episodes ADD COLUMN transcript_metadata JSON;

-- Example data:
{
  "total_segments": 1847,
  "start_time": 0.0,
  "end_time": 5421.5,
  "duration_covered_seconds": 5421.5,
  "character_count": 95432,
  "word_count": 18234,
  "gaps_detected": 3,
  "is_complete": true
}
```

---

## 2. ✅ Claude API Chunk Verification

### Problem
How do we know the entire transcript is getting passed to Claude? Need first and last chunk positions.

### Current Implementation
```python
chunks = youtube_service.chunk_transcript(transcript, chunk_size=8000)
recommendations = claude_service.extract_recommendations_from_chunks(chunks, ...)
```

### Solution: Add Chunk Logging

```python
def extract_recommendations_from_chunks(
    self,
    chunks: List[str],
    episode_title: str,
    guest_name: str = ""
) -> List[Dict]:
    """Extract recommendations with chunk position logging"""

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

        # Process with Claude...

    # Summary log
    first_chunk = chunk_metadata[0]
    last_chunk = chunk_metadata[-1]
    total_chars_processed = sum(c['chunk_length'] for c in chunk_metadata)

    logger.info(f"=== CHUNK PROCESSING COMPLETE ===")
    logger.info(f"First chunk started at position: {first_chunk['start_position']}")
    logger.info(f"Last chunk ended at position: {last_chunk['end_position']}")
    logger.info(f"Total characters processed: {total_chars_processed:,}")
    logger.info(f"Coverage verification: {total_chars_processed == last_chunk['end_position']}")

    return recommendations, chunk_metadata
```

### Database Schema Addition
Add to `episodes` table:
```sql
ALTER TABLE episodes ADD COLUMN claude_processing_metadata JSON;

-- Example data:
{
  "total_chunks": 12,
  "total_characters_sent": 95432,
  "first_chunk": {
    "position": 0,
    "first_50": "Welcome to the Huberman Lab podcast where we..."
  },
  "last_chunk": {
    "position": 87432,
    "last_50": "...thank you for joining us today. See you next time."
  },
  "chunks": [
    {"chunk": 1, "start": 0, "end": 8000, "length": 8000},
    {"chunk": 2, "start": 8000, "end": 16000, "length": 8000},
    ...
  ]
}
```

---

## 3. ✅ AI Model Alternatives (Cost Reduction)

### Current Cost: Claude Sonnet 4.5
- Input: $3.00 per million tokens
- Output: $15.00 per million tokens
- Average per episode: ~$0.20

### Alternative 1: Claude Haiku 4 (80% cheaper)
```python
# Cheaper Claude model
MODEL = "claude-haiku-4-20250514"

# Cost comparison:
# Input: $0.40 per million tokens (7.5x cheaper)
# Output: $2.00 per million tokens (7.5x cheaper)
# Average per episode: ~$0.025 (saves $0.175 per episode)

# Trade-offs:
# - Slightly lower accuracy
# - Faster response time
# - Good for product/app recommendations
# - May miss subtle book/movie references
```

### Alternative 2: OpenAI GPT-4o-mini (90% cheaper)
```python
# OpenAI's cheap model
import openai

MODEL = "gpt-4o-mini"

# Cost:
# Input: $0.15 per million tokens
# Output: $0.60 per million tokens
# Average per episode: ~$0.015 (saves $0.185)

# Implementation:
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Extract recommendations from podcast transcripts..."},
        {"role": "user", "content": transcript_chunk}
    ],
    temperature=0,
    response_format={"type": "json_object"}
)

# Trade-offs:
# - Similar quality to Claude Haiku
# - Different strengths (better at structured output)
# - Requires OpenAI account
```

### Alternative 3: Google Gemini 1.5 Flash (95% cheaper)
```python
# Google's fast cheap model
import google.generativeai as genai

MODEL = "gemini-1.5-flash"

# Cost:
# Input: $0.075 per million tokens
# Output: $0.30 per million tokens
# Average per episode: ~$0.008 (saves $0.192)

# Implementation:
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    f"Extract recommendations from this transcript:\n\n{transcript_chunk}"
)

# Trade-offs:
# - Cheapest option
# - Largest context window (1M tokens!)
# - Can process entire transcript in one call (no chunking!)
# - May need prompt tuning
```

### Alternative 4: Local LLM (Free but slower)
```python
# Llama 3.1 70B via Ollama (free)
import ollama

MODEL = "llama3.1:70b"

# Cost: $0 (runs locally)
# Requirements:
# - 64GB+ RAM
# - GPU recommended
# - Slower (10-30 seconds per chunk)

response = ollama.chat(
    model='llama3.1:70b',
    messages=[{'role': 'user', 'content': transcript_chunk}]
)

# Trade-offs:
# - Completely free
# - Full control over model
# - Privacy (no data sent to cloud)
# - Requires powerful hardware
# - Much slower processing
```

### Recommendation: Hybrid Approach

```python
def get_ai_model(recommendation_type: str):
    """Choose model based on recommendation type"""

    if recommendation_type in ['book', 'movie']:
        # Use Claude Sonnet for nuanced content
        return 'claude-sonnet-4-5'
    else:
        # Use Gemini Flash for products/apps (95% cheaper)
        return 'gemini-1.5-flash'
```

**Cost Savings:**
- Current: 247 recommendations × $0.20 = $49.40
- Hybrid: (50 books/movies × $0.20) + (197 others × $0.008) = $10 + $1.58 = **$11.58**
- **Savings: 77% reduction ($37.82 saved)**

---

## 4. ✅ Enhanced Metadata Capture

### Current Missing Fields
- Host name (only capturing guest)
- Exact publish date
- Episode number
- Show notes/description

### Solution: Enhanced Discovery

```python
def get_enhanced_video_metadata(video_id: str) -> Dict:
    """Fetch comprehensive video metadata"""

    url = f"https://www.youtube.com/watch?v={video_id}"
    response = requests.get(url)
    html = response.text

    # Extract from ytInitialData JSON embedded in HTML
    match = re.search(r'var ytInitialData = ({.+?});', html)
    if match:
        data = json.loads(match.group(1))

        # Navigate the JSON structure
        video_details = data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']

        metadata = {
            'title': video_details['title']['runs'][0]['text'],
            'view_count': int(video_details['viewCount']['videoViewCountRenderer']['viewCount']['simpleText'].replace(',', '').split()[0]),
            'publish_date': video_details['dateText']['simpleText'],
            'description': data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']['description']['runs'][0]['text'],
            'channel_name': data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']['owner']['videoOwnerRenderer']['title']['runs'][0]['text'],
            'subscriber_count': data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']['owner']['videoOwnerRenderer']['subscriberCountText']['simpleText']
        }

        return metadata
```

### Extract Host from Description

```python
def extract_host_name(description: str, channel_name: str) -> str:
    """Extract host name from description or channel"""

    # Common patterns in podcast descriptions
    patterns = [
        r'hosted by ([A-Z][a-z]+ [A-Z][a-z]+)',
        r'Host: ([A-Z][a-z]+ [A-Z][a-z]+)',
        r'with your host ([A-Z][a-z]+ [A-Z][a-z]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            return match.group(1)

    # Fallback: Use known hosts
    host_mapping = {
        "Huberman Lab": "Andrew Huberman",
        "Lenny's Podcast": "Lenny Rachitsky",
        "The Tim Ferriss Show": "Tim Ferriss"
    }

    return host_mapping.get(channel_name, "Unknown")
```

### Database Schema Update

```sql
-- Add to episodes table
ALTER TABLE episodes ADD COLUMN host_name VARCHAR;
ALTER TABLE episodes ADD COLUMN publish_date_exact DATE;
ALTER TABLE episodes ADD COLUMN episode_number INTEGER;
ALTER TABLE episodes ADD COLUMN view_count BIGINT;
ALTER TABLE episodes ADD COLUMN description_full TEXT;
```

---

## 5. ✅ Amazon URLs & Book Cover Images

### Problem
- Need Amazon URLs for buy links
- Want to use Amazon images (higher quality than Google Books)

### Solution 1: Generate Amazon URLs from ISBN

```python
def get_amazon_url_from_isbn(isbn: str, isbn_10: str = None) -> str:
    """
    Generate Amazon product URL from ISBN
    Amazon uses ISBN-10 for URLs (ASIN)
    """

    # Prefer ISBN-10, fallback to ISBN-13
    asin = isbn_10 if isbn_10 else isbn

    # Amazon affiliate link format (optional: add affiliate tag)
    affiliate_tag = "youraffid-20"  # Replace with your Amazon Associates ID

    base_url = f"https://www.amazon.com/dp/{asin}"

    # With affiliate tag:
    # base_url = f"https://www.amazon.com/dp/{asin}?tag={affiliate_tag}"

    return base_url
```

### Solution 2: Fetch Amazon Book Cover

```python
def get_amazon_book_cover(isbn_10: str) -> str:
    """
    Get high-quality book cover from Amazon
    Amazon provides predictable image URLs
    """

    # Amazon's image URL pattern
    # Format: https://images-na.ssl-images-amazon.com/images/P/{ASIN}.jpg

    base_url = f"https://images-na.ssl-images-amazon.com/images/P/{isbn_10}"

    # Different sizes available:
    sizes = {
        'small': f"{base_url}._SL75_.jpg",      # 75px
        'medium': f"{base_url}._SL160_.jpg",    # 160px
        'large': f"{base_url}._SL500_.jpg",     # 500px
        'extra_large': f"{base_url}._SL1500_.jpg"  # 1500px
    }

    # Verify image exists
    try:
        response = requests.head(sizes['large'], timeout=5)
        if response.status_code == 200:
            return sizes['large']
    except:
        pass

    # Fallback to Google Books
    return None
```

### Solution 3: Enhanced Book Enrichment

```python
def enrich_book_recommendation_enhanced(self, rec_data: Dict) -> Dict:
    """Enhanced enrichment with Amazon data"""

    # First, get Google Books data (for ISBN)
    google_data = self.search_google_books(
        rec_data.get('title'),
        rec_data.get('author', '')
    )

    if not google_data:
        return rec_data

    # Extract ISBNs
    isbn_13 = google_data.get('isbn_13')
    isbn_10 = google_data.get('isbn_10')

    # Generate Amazon URL
    if isbn_10:
        amazon_url = get_amazon_url_from_isbn(isbn_13, isbn_10)
        amazon_image = get_amazon_book_cover(isbn_10)
    else:
        amazon_url = None
        amazon_image = None

    # Combine data
    enriched = {
        **rec_data,
        **google_data,
        'amazonUrl': amazon_url,
        'amazonImageUrl': amazon_image,
        'coverImageUrl': amazon_image or google_data.get('coverImageUrl'),  # Prefer Amazon
        'buyLinks': {
            'amazon': amazon_url,
            'googleBooks': google_data.get('googleBooksUrl')
        }
    }

    return enriched
```

### Alternative: Open Library API (Free, No Rate Limits)

```python
def get_book_cover_from_open_library(isbn: str) -> str:
    """
    Open Library provides free, high-quality book covers
    No API key required, no rate limits
    """

    # Open Library cover API
    # https://covers.openlibrary.org/b/isbn/{ISBN}-{SIZE}.jpg
    # Sizes: S (small), M (medium), L (large)

    return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

    # Also provides metadata:
    api_url = f"https://openlibrary.org/isbn/{isbn}.json"
    response = requests.get(api_url)
    data = response.json()

    return {
        'title': data.get('title'),
        'authors': [a['name'] for a in data.get('authors', [])],
        'publish_date': data.get('publish_date'),
        'publishers': data.get('publishers', []),
        'cover_url': f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
    }
```

---

## Implementation Priority

### Phase 1: Critical Quality Checks (Week 1)
1. ✅ Add transcript verification to YouTube service
2. ✅ Add chunk logging to Claude service
3. ✅ Update database schema for metadata
4. ✅ Log first/last chunk positions

### Phase 2: Cost Optimization (Week 2)
1. ✅ Test Gemini 1.5 Flash on sample episodes
2. ✅ Compare quality: Claude vs Gemini
3. ✅ Implement hybrid model selection
4. ✅ Measure cost savings

### Phase 3: Enhanced Metadata (Week 3)
1. ✅ Enhanced video metadata extraction
2. ✅ Host name extraction
3. ✅ Exact publish date capture
4. ✅ Database schema updates

### Phase 4: Amazon Integration (Week 4)
1. ✅ Amazon URL generation
2. ✅ Amazon book cover fetching
3. ✅ Open Library integration (backup)
4. ✅ Update book enrichment service

---

## Cost Comparison: 110 Episodes

### Current Setup (All Claude Sonnet)
- 110 episodes × $0.20 = **$22.00**

### Optimized Setup (Hybrid)
- Books/Movies (40%): 44 episodes × $0.20 = $8.80
- Products/Other (60%): 66 episodes × $0.008 = $0.53
- **Total: $9.33 (saves $12.67, 58% reduction)**

### Ultra-Cheap (All Gemini)
- 110 episodes × $0.008 = **$0.88 (saves $21.12, 96% reduction)**

### Free (Local Llama)
- **$0.00** (but requires powerful hardware + time)

---

## Testing Checklist

Before deploying improvements:

- [ ] Test transcript verification on 10 sample videos
- [ ] Verify chunk positions match original transcript
- [ ] Test Gemini Flash on 5 episodes, compare quality
- [ ] Validate Amazon URLs work for all ISBNs
- [ ] Check Amazon images load correctly
- [ ] Test Open Library as fallback
- [ ] Verify host name extraction accuracy
- [ ] Check database migrations work
- [ ] Update frontend to display new fields
- [ ] Document all changes in README

---

## Monitoring & Alerts

### Quality Metrics to Track

```python
# Add to processing logs
quality_metrics = {
    'transcript_completeness': is_complete,  # True/False
    'transcript_length': char_count,
    'chunks_processed': total_chunks,
    'recommendations_found': len(recommendations),
    'books_enriched': enriched_count,
    'amazon_urls_generated': amazon_count,
    'processing_time_seconds': duration,
    'ai_model_used': model_name,
    'cost_estimate': cost
}
```

### Alerts to Configure

- Alert if transcript < 5000 characters (incomplete)
- Alert if no recommendations found
- Alert if 0 books enriched when books detected
- Alert if processing takes > 5 minutes per episode
- Alert if cost per episode > $0.50

---

## Questions Answered Summary

1. **Transcript Completeness**: ✅ Added segment counting, timestamp verification, gap detection
2. **Claude Chunk Verification**: ✅ Log first/last positions, character counts, coverage
3. **Database Tracking**: ✅ New JSON fields for transcript_metadata and claude_processing_metadata
4. **Cheaper AI Options**: ✅ Gemini Flash (96% cheaper), GPT-4o-mini (90% cheaper), Claude Haiku (80% cheaper)
5. **Metadata Capture**: ✅ Host name, exact dates, view counts, full descriptions
6. **Amazon URLs**: ✅ Generate from ISBN, fetch book covers, Open Library backup

Next step: Implement Phase 1 improvements!
