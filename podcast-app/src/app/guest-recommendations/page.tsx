'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { API_URL } from '@/config/api';
import Navigation from '@/components/Navigation';

interface Book {
  id: string;
  title: string;
  author?: string;
  coverImageUrl?: string;
  description?: string;
  amazonUrl?: string;
  recommendedBy?: string;
  primaryTheme?: string;
}

interface Episode {
  episodeId: string;
  episodeTitle: string;
  episodeDate: string;
  episodeUrl: string;
  podcastName: string;
  podcastId: string;
  guestName: string;
  books: Book[];
  bookCount: number;
}

export default function GuestRecommendationsPage() {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchEpisodes() {
      try {
        const response = await fetch(`${API_URL}/api/books/by-guest?limit=100`);
        const data = await response.json();

        console.log('Fetched episodes:', data);
        setEpisodes(data.episodes || []);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching episodes:', error);
        setLoading(false);
      }
    }

    fetchEpisodes();
  }, []);

  // Filter by search term (guest name, episode title, or book title)
  const filteredEpisodes = episodes.filter(episode =>
    searchTerm === '' ||
    episode.guestName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    episode.episodeTitle?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    episode.books.some(book => book.title?.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <div className="relative h-[60vh] w-full overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent z-10" />
        {episodes[0]?.books[0]?.coverImageUrl && (
          <div className="absolute inset-0 opacity-30">
            <Image
              src={episodes[0].books[0].coverImageUrl}
              alt="Featured book"
              fill
              className="object-cover blur-sm"
              unoptimized
            />
          </div>
        )}
        <div className="relative z-20 h-full flex flex-col justify-between">
          {/* Navigation at top */}
          <div className="pt-8 px-8 relative">
            <Navigation style="pills" />
          </div>

          {/* Tagline and search at bottom */}
          <div className="max-w-4xl px-12 pb-16">
            <p className="text-4xl font-bold text-gray-100 leading-tight mb-4">
              Find your next great read from the books podcast guests can't stop talking about
            </p>
            <p className="text-lg text-gray-400 mb-6">
              {episodes.length} episodes • Chronological timeline of book recommendations
            </p>

            {/* Search */}
            <div className="max-w-2xl">
              <input
                type="text"
                placeholder="Search by guest name, episode, or book title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-6 py-4 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="px-12 pb-20 -mt-10 relative z-30">
        <div className="max-w-7xl mx-auto space-y-8">
          {filteredEpisodes.map((episode) => (
            <EpisodeCard key={episode.episodeId} episode={episode} />
          ))}

          {filteredEpisodes.length === 0 && (
            <div className="text-center text-gray-400 py-20">
              No episodes found matching "{searchTerm}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EpisodeCard({ episode }: { episode: Episode }) {
  const episodeDate = episode.episodeDate ? new Date(episode.episodeDate) : null;
  const formattedDate = episodeDate
    ? episodeDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    : 'Date unknown';

  return (
    <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/30 backdrop-blur-sm border border-white/10 rounded-2xl p-8 hover:border-purple-500/50 transition-all duration-300">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center text-xl font-bold">
              {episode.guestName?.[0] || '?'}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">{episode.guestName}</h2>
              <p className="text-sm text-gray-400">{formattedDate}</p>
            </div>
          </div>

          <a
            href={episode.episodeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-lg text-gray-300 hover:text-purple-400 transition-colors inline-flex items-center gap-2 mt-2"
          >
            <span>{episode.episodeTitle}</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
          <p className="text-sm text-gray-500 mt-1">{episode.podcastName}</p>
        </div>

        <div className="text-right">
          <div className="text-3xl font-bold text-purple-400">{episode.bookCount}</div>
          <div className="text-sm text-gray-400">{episode.bookCount === 1 ? 'book' : 'books'}</div>
        </div>
      </div>

      {/* Books Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 mt-6">
        {episode.books.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
    </div>
  );
}

function BookCard({ book }: { book: Book }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className="group cursor-pointer transition-transform duration-300 hover:scale-105"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-gray-800 shadow-lg">
        {book.coverImageUrl ? (
          <Image
            src={book.coverImageUrl}
            alt={book.title}
            fill
            className="object-cover"
            sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, (max-width: 1024px) 25vw, 16vw"
            unoptimized
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center p-4 text-center">
            <span className="text-sm font-medium line-clamp-4">{book.title}</span>
          </div>
        )}

        {/* Hover Overlay */}
        {isHovered && (
          <div className="absolute inset-0 bg-black/95 p-4 flex flex-col justify-between text-xs overflow-hidden">
            <div>
              <h3 className="font-bold mb-2 line-clamp-3 text-sm">{book.title}</h3>
              {book.author && (
                <p className="text-gray-400 mb-2 line-clamp-2">{book.author}</p>
              )}
              {book.description && (
                <p className="text-gray-300 text-xs line-clamp-4 mb-2">{book.description}</p>
              )}
            </div>
            <div>
              {book.amazonUrl && (
                <a
                  href={book.amazonUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-center bg-orange-600 hover:bg-orange-700 px-3 py-2 rounded text-sm font-semibold"
                  onClick={(e) => e.stopPropagation()}
                >
                  View on Amazon
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
