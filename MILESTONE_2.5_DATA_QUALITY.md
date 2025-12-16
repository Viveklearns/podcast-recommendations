# Milestone 2.5: Book Data Quality & Enrichment

**Goal**: Ensure all book recommendations meet quality standards before display

**Duration**: 3-5 days

---

## Overview

Before scaling to more episodes, we need to implement strict data quality controls for book recommendations. This milestone focuses on validation, enrichment, and proper display of book data.

## Success Criteria

- ✅ All displayed books have: title, author, valid ISBN, Amazon link, cover image
- ✅ All recommendations show actual guest names (no "Guest 1", "Guest 2")
- ✅ Book detail pages show complete information
- ✅ ISBN validation using Google Books API
- ✅ Books without required data are filtered out (not displayed)

---

## Tasks

### 2.5.1 Database Schema Updates

**Add required fields for books:**
- [x] `recommended_by` field already exists - needs guest name extraction
- [ ] Add `image_url` to extra_metadata for book cover
- [ ] Add `amazon_url` to extra_metadata
- [ ] Add `isbn` or `isbn13` to extra_metadata
- [ ] Add `google_books_id` for verification

**Data Model Example:**
```json
{
  "type": "book",
  "title": "Atomic Habits",
  "recommended_by": "James Clear",  // Real guest name, not "Guest 1"
  "extra_metadata": {
    "author": "James Clear",
    "isbn": "9780735211292",
    "isbn13": "978-0735211292",
    "google_books_id": "fFCjDQAAQBAJ",
    "image_url": "https://books.google.com/books/content?id=...",
    "amazon_url": "https://www.amazon.com/dp/0735211299",
    "publisher": "Avery",
    "published_year": 2018,
    "page_count": 320,
    "verified": true
  }
}
```

### 2.5.2 Guest Name Extraction

**Problem**: Currently extracting "Guest 1", "Guest 2" instead of real names

**Solution Options:**
1. Parse episode title for guest name
2. Use Claude to extract guest name from transcript intro
3. Manual configuration per episode

**Implementation:**
- [ ] Update Claude prompt to extract actual guest name from intro
- [ ] Add guest name parsing from episode title (e.g., "Episode 123: Interview with James Clear")
- [ ] Fallback: Store episode metadata with guest names
- [ ] Validation: Ensure `recommended_by` is not "Guest X" pattern

### 2.5.3 Google Books API Integration

**Purpose**: Validate books and enrich metadata

**Tasks:**
- [ ] Set up Google Books API credentials
- [ ] Create `GoogleBooksService` class:
  ```python
  class GoogleBooksService:
      def search_book(title: str, author: str) -> dict
      def get_book_by_isbn(isbn: str) -> dict
      def validate_isbn(isbn: str) -> bool
      def extract_metadata(book_data: dict) -> dict
  ```
- [ ] Implement ISBN verification:
  - [ ] Check if ISBN-10 or ISBN-13 is valid
  - [ ] Verify book exists in Google Books
  - [ ] Mark as `verified: true` if found
- [ ] Extract book metadata:
  - [ ] ISBN (10 and 13)
  - [ ] Cover image URL (preferredSize: large)
  - [ ] Author(s)
  - [ ] Publisher
  - [ ] Publication date
  - [ ] Page count
  - [ ] Google Books ID

**API Endpoint:**
```
GET https://www.googleapis.com/books/v1/volumes?q=isbn:{ISBN}
GET https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author}
```

### 2.5.4 Book Image Sourcing Options

**Option 1: Google Books API** (Recommended)
- ✅ Free, no API key required for basic use
- ✅ High-quality cover images
- ✅ Provides multiple sizes (thumbnail, small, medium, large)
- ✅ Reliable and fast
- Example URL: `imageLinks.thumbnail` or `imageLinks.large`

**Option 2: Open Library**
- ✅ Free, open source
- ✅ Good coverage
- ⚠️ Image quality varies
- URL format: `https://covers.openlibrary.org/b/isbn/{ISBN}-L.jpg`

**Option 3: Amazon Product Advertising API**
- ⚠️ Requires API approval and affiliate account
- ⚠️ More complex setup
- ✅ High-quality images
- ✅ Can get Amazon URL simultaneously

**Option 4: Scraping (Not Recommended)**
- ❌ Against Amazon TOS
- ❌ Unreliable
- ❌ Can get IP blocked

**Recommended Strategy:**
1. **Primary**: Google Books API (free, reliable)
2. **Fallback**: Open Library if Google Books doesn't have image
3. **Last Resort**: Placeholder image

### 2.5.5 Amazon Link Generation

**Options:**

**Option 1: Amazon Product Advertising API**
- Requires API credentials
- Can search by ISBN
- Returns product URL
- Can earn affiliate commission

**Option 2: Direct URL Construction** (Simpler)
- Use ISBN to construct Amazon URL
- Format: `https://www.amazon.com/dp/{ISBN10}`
- No API required
- Can add affiliate tag later: `?tag=youraffiliateId`

**Option 3: Affiliate Link Service**
- Use services like Geniuslink or Amazon OneLink
- Automatically handles international redirects

**Implementation:**
- [ ] Implement direct URL construction initially
- [ ] Add ISBN-10 conversion if only ISBN-13 available
- [ ] Validate Amazon URLs (check if product page exists)
- [ ] Add affiliate tag configuration (optional)

### 2.5.6 Book Enrichment Pipeline

**Workflow:**
```
Claude extracts book mention
    ↓
Extract: title, author (approximate)
    ↓
Search Google Books API
    ↓
Match best result (fuzzy matching)
    ↓
Extract: ISBN, cover image URL, verified metadata
    ↓
Generate Amazon URL from ISBN
    ↓
Validate all required fields present
    ↓
If valid: Save to database
If invalid: Log for manual review
```

**Implementation:**
- [ ] Create `BookEnrichmentService`:
  ```python
  class BookEnrichmentService:
      def enrich_book_recommendation(rec: dict) -> dict:
          # 1. Search Google Books
          # 2. Extract ISBN and metadata
          # 3. Get cover image
          # 4. Generate Amazon URL
          # 5. Validate all fields
          # 6. Return enriched data or None
  ```
- [ ] Add fuzzy matching for book titles (handle typos)
- [ ] Handle multiple results (pick best match by score)
- [ ] Add confidence scoring for matches

### 2.5.7 Display Filtering

**Frontend Validation:**
- [ ] Update `getRecommendations` API to filter books
- [ ] Only return books with:
  - ✅ Valid title (not "Not specified")
  - ✅ Valid author (not "Not mentioned")
  - ✅ Valid `recommended_by` (not "Guest X" pattern)
  - ✅ Valid ISBN
  - ✅ Amazon URL present
  - ✅ Cover image URL present

**Backend Filter Logic:**
```python
def filter_valid_books(recommendations):
    valid_books = []
    for rec in recommendations:
        if rec.type != 'book':
            valid_books.append(rec)
            continue

        # Check book-specific requirements
        metadata = rec.extra_metadata or {}
        if (
            rec.title and not rec.title.startswith("Not specified")
            and metadata.get('author') and metadata.get('author') != "Not mentioned"
            and rec.recommended_by and not re.match(r'Guest \d+', rec.recommended_by)
            and metadata.get('isbn')
            and metadata.get('amazon_url')
            and metadata.get('image_url')
        ):
            valid_books.append(rec)
        else:
            logger.info(f"Filtering out invalid book: {rec.title}")

    return valid_books
```

### 2.5.8 Book Detail Page Updates

**Current**: Basic recommendation detail
**Updated**: Comprehensive book page

**Components to add:**
- [ ] Large book cover image (from `image_url`)
- [ ] Book metadata section:
  - [ ] Title
  - [ ] Author(s)
  - [ ] Publisher, publication year
  - [ ] Page count
  - [ ] ISBN display
- [ ] Recommendation context:
  - [ ] Who recommended it (guest name + photo if available)
  - [ ] Podcast name
  - [ ] Episode title and date
  - [ ] Full quote from episode
  - [ ] Context/why it was recommended
- [ ] Call-to-action buttons:
  - [ ] **Primary**: "Buy on Amazon" (opens amazon_url)
  - [ ] **Secondary**: "View on Google Books"
  - [ ] **Tertiary**: "Listen to Episode" (with timestamp)
- [ ] Related recommendations section

**Route**: `/recommendations/[id]/page.tsx`

### 2.5.9 Updated Claude Prompt

**Current issue**: Not extracting complete book information

**Enhanced prompt additions:**
```
For book recommendations, you MUST extract:
1. Exact book title as mentioned
2. Author name (if mentioned)
3. The actual guest name who recommended it (parse from "Hi, I'm [Name]" or episode context)
4. Full context of why they recommended it
5. Direct quote mentioning the book

Format for books:
{
  "type": "book",
  "title": "Exact Title",
  "author_creator": "Author Name",
  "recommended_by": "Guest Name (not 'Guest 1')",
  "context": "Why recommended",
  "quote": "Direct quote",
  "confidence": 0.9
}

IMPORTANT:
- For recommended_by, extract the actual person's name, never use "Guest 1", "Guest 2"
- If you cannot find the guest's actual name in the transcript, mark confidence as low
- Only include books that are explicitly and enthusiastically recommended
```

### 2.5.10 Testing & Validation

**Manual Review Process:**
- [ ] Review all 6 existing book recommendations
- [ ] For each book:
  - [ ] Verify title is correct
  - [ ] Verify author is correct
  - [ ] Find ISBN using Google Books
  - [ ] Get cover image
  - [ ] Verify Amazon link works
  - [ ] Update guest name to real name
- [ ] Create test cases for validation logic
- [ ] Test with various book types (fiction, non-fiction, technical)

**Automated Tests:**
- [ ] Test Google Books API integration
- [ ] Test ISBN validation
- [ ] Test Amazon URL generation
- [ ] Test book filtering logic
- [ ] Test book detail page rendering

---

## Implementation Order

1. **Week 1, Day 1-2**: Google Books API Integration
   - Set up API client
   - ISBN validation
   - Cover image extraction
   - Amazon URL generation

2. **Week 1, Day 3**: Guest Name Extraction
   - Update Claude prompt
   - Add episode title parsing
   - Validate existing data

3. **Week 1, Day 4**: Book Enrichment Pipeline
   - Create enrichment service
   - Update processing script
   - Re-process existing episodes

4. **Week 1, Day 5**: Display Filtering & Book Detail Page
   - Add backend filtering
   - Update frontend to filter books
   - Create/update book detail page

5. **Week 2**: Testing & Cleanup
   - Manual review of all books
   - Fix data quality issues
   - Document process

---

## Metrics to Track

- **Before**: 6 books, many missing data
- **After Target**:
  - 100% of displayed books have all required fields
  - 0 books with "Guest X" as recommender
  - 100% have valid ISBNs
  - 100% have working Amazon links
  - 100% have cover images

---

## Deliverables

1. ✅ Updated database schema with new fields
2. ✅ Google Books API integration working
3. ✅ ISBN validation implemented
4. ✅ Book cover images displaying
5. ✅ Amazon links working
6. ✅ Guest names extracted correctly
7. ✅ Book detail page with all information
8. ✅ Filtering logic removing incomplete books
9. ✅ Updated processing pipeline
10. ✅ Documentation of enrichment process

---

## After This Milestone

- All books displayed will be high-quality, verified data
- Users can click through to Amazon to purchase
- Guest attribution is accurate
- Ready to scale to more episodes and podcasts
