# Podcast Recommendations App - Demo

A Next.js demo application for browsing and discovering recommendations from top podcasts.

## What's Been Built (Milestone 1 Complete!)

### ✅ Completed Features

1. **Project Setup**
   - Next.js 16 with TypeScript
   - Tailwind CSS for styling
   - Full project structure with organized folders

2. **Type System**
   - Complete TypeScript types for all data models
   - Podcast, Episode, and Recommendation types
   - Support for Books, Movies, TV Shows, Apps, and more

3. **Mock Data**
   - 5 realistic podcasts (Tim Ferriss, Huberman Lab, Joe Rogan, etc.)
   - 5 sample episodes with real metadata
   - 10 diverse recommendations (books, movies, TV shows, apps)
   - Helper functions for data queries

4. **Reusable Components**
   - `Header` - Navigation with logo and links
   - `Footer` - Site footer with links
   - `RecommendationCard` - Beautiful card component with hover effects
   - `PodcastBadge` - Clickable podcast identifier

5. **Complete Pages**
   - **Homepage** - Hero section, featured recommendations, category browsing, podcast showcase
   - **Browse Page** - Filterable grid with sidebar filters and category tabs
   - **Recommendation Detail Page** - Full details with episode context, ratings, external links
   - **Podcasts List Page** - Grid of all podcasts
   - **Podcast Detail Page** - All episodes and recommendations for a podcast
   - **Search Page** - Live search with suggestions and results

### 📊 Data Dimensions Implemented

**Books:**
- Title, Author, ISBN
- Cover image, Publisher, Year
- Page count, Goodreads rating
- Amazon & Google Books links
- Context, Quote, Timestamp, Recommended by

**Movies & TV Shows:**
- Title, Director/Creator, Year
- Poster images, Genre, Runtime
- IMDB rating, Streaming platforms
- Context, Quote, Timestamp, Recommended by

**Apps & Products:**
- Title, Category, Description
- Logo/image, URL, Price
- Context, Quote, Timestamp, Recommended by

## Running the Demo

```bash
# The dev server is already running at:
http://localhost:3000

# Or start it with:
npm run dev
```

## Project Structure

```
podcast-app/
├── src/
│   ├── app/
│   │   ├── browse/page.tsx         # Browse with filters
│   │   ├── recommendations/[id]/page.tsx  # Detail view
│   │   ├── podcasts/
│   │   │   ├── page.tsx            # Podcast list
│   │   │   └── [id]/page.tsx       # Podcast detail
│   │   ├── search/page.tsx         # Search interface
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Homepage
│   │   └── globals.css             # Global styles
│   ├── components/
│   │   ├── Header.tsx              # Site header
│   │   ├── Footer.tsx              # Site footer
│   │   ├── RecommendationCard.tsx  # Recommendation cards
│   │   └── PodcastBadge.tsx        # Podcast identifiers
│   ├── lib/
│   │   └── mockData.ts             # Mock data & helpers
│   └── types/
│       └── index.ts                # TypeScript types
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## Key Features Demonstrated

1. **Responsive Design** - Works on mobile, tablet, and desktop
2. **Filtering & Search** - Multiple ways to find recommendations
3. **Rich Metadata** - Shows context, quotes, timestamps
4. **External Links** - Jump to Amazon, YouTube, etc.
5. **Clean UI** - Modern design with hover effects and transitions
6. **Type Safety** - Full TypeScript coverage

## Next Steps (Milestone 2)

1. Set up FastAPI backend
2. Implement YouTube transcript extraction
3. Integrate Claude API for recommendation extraction
4. Add data enrichment (Google Books, TMDB APIs)
5. Process real podcast episodes
6. Connect frontend to live backend

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Deployment**: Ready for Vercel

## Demo Data

The app currently uses mock data that includes:
- 5 top US podcasts
- 5 episodes with realistic metadata
- 10 recommendations across different categories
- All with proper context, quotes, and timestamps

---

Built with Claude Code 🤖
