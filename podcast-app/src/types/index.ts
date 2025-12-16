export interface Podcast {
  id: string;
  name: string;
  youtubeChannelId: string;
  rssFeedUrl: string;
  category: string;
  imageUrl: string;
  createdAt: string;
  lastFetchedAt: string;
}

export interface Episode {
  id: string;
  podcastId: string;
  title: string;
  description: string;
  publishedDate: string;
  durationSeconds: number;
  youtubeUrl?: string;
  audioUrl?: string;
  transcriptUrl?: string;
  guestNames: string[];
  transcriptSource: 'youtube' | 'rss' | 'manual';
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  processedAt?: string;
  createdAt: string;
}

export interface BookRecommendation {
  id: string;
  episodeId: string;
  type: 'book';
  title: string;
  author: string;
  isbn?: string;
  description?: string;
  coverImageUrl?: string;
  publisher?: string;
  publishedYear?: number;
  pageCount?: number;
  goodreadsRating?: number;
  amazonUrl?: string;
  googleBooksUrl?: string;

  // Context fields
  recommendationContext: string;
  quoteFromEpisode: string;
  timestampSeconds: number;
  recommendedBy: string;
  confidenceScore: number;

  createdAt: string;
  updatedAt: string;
}

export interface MovieTVRecommendation {
  id: string;
  episodeId: string;
  type: 'movie' | 'tv_show';
  title: string;
  creatorDirector?: string;
  releaseYear?: number;
  tmdbId?: number;
  imdbId?: string;
  posterUrl?: string;
  backdropUrl?: string;
  genre?: string[];
  runtimeMinutes?: number;
  seasons?: number;
  episodes?: number;
  rating?: number;
  streamingPlatforms?: string[];
  trailerUrl?: string;

  // Context fields
  recommendationContext: string;
  quoteFromEpisode: string;
  timestampSeconds: number;
  recommendedBy: string;
  confidenceScore: number;

  createdAt: string;
  updatedAt: string;
}

export interface OtherRecommendation {
  id: string;
  episodeId: string;
  type: 'podcast' | 'product' | 'app' | 'website' | 'course' | 'other';
  title: string;
  category?: string;
  description?: string;
  url?: string;
  imageUrl?: string;
  price?: string;

  // Context fields
  recommendationContext: string;
  quoteFromEpisode: string;
  timestampSeconds: number;
  recommendedBy: string;
  confidenceScore: number;

  createdAt: string;
  updatedAt: string;
}

export type Recommendation = BookRecommendation | MovieTVRecommendation | OtherRecommendation;

export interface RecommendationWithDetails extends Recommendation {
  episode: Episode;
  podcast: Podcast;
}

// Filter types
export interface FilterOptions {
  type?: 'book' | 'movie' | 'tv_show' | 'podcast' | 'product' | 'app' | 'website' | 'course' | 'other';
  podcastId?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  sort?: 'recent' | 'popular' | 'rating';
  search?: string;
}
