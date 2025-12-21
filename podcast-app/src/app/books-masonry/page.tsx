'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface BookData {
  id: string;
  title: string;
  recommendedBy: string;
  episodeId: string;
  episodeTitle?: string;
  podcastName?: string;
  youtubeUrl?: string;
  recommendationContext?: string;
  author?: string;
  amazonUrl?: string;
  coverImageUrl?: string;
  guestNames?: string;
}

export default function BooksMasonryPage() {
  const [books, setBooks] = useState<BookData[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchData() {
      try {
        const [recsRes, epsRes, podsRes] = await Promise.all([
          fetch('http://localhost:8000/api/recommendations?limit=5000'),
          fetch('http://localhost:8000/api/episodes?limit=500'),
          fetch('http://localhost:8000/api/podcasts')
        ]);

        const recsData = await recsRes.json();
        const epsData = await epsRes.json();
        const podsData = await podsRes.json();

        const booksOnly = recsData.filter((rec: any) => rec.type === 'book');

        const enriched = booksOnly.map((book: any) => {
          const episode = epsData.find((ep: any) => ep.id === book.episodeId);
          const podcast = episode ? podsData.find((p: any) => p.id === episode.podcastId) : null;

          return {
            ...book,
            episodeTitle: episode?.title,
            podcastName: podcast?.name,
            youtubeUrl: episode?.youtubeUrl,
            guestNames: episode?.guestNames?.join(', ') || 'N/A'
          };
        });

        setBooks(enriched);
        setLoading(false);
      } catch (error) {
        console.error('Error:', error);
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const filteredBooks = books.filter(book => {
    const search = searchTerm.toLowerCase();
    return searchTerm === '' ||
      book.title?.toLowerCase().includes(search) ||
      book.author?.toLowerCase().includes(search) ||
      book.guestNames?.toLowerCase().includes(search);
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-amber-50">
        <div className="text-2xl text-gray-600">Loading books...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <div className="bg-white border-b border-amber-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900" style={{fontFamily: 'Georgia, serif'}}>
                Book Collection
              </h1>
              <p className="text-gray-600 mt-1 italic">{books.length} curated recommendations</p>
            </div>
            <Link href="/books" className="text-teal-600 hover:text-teal-700 font-medium">
              ← Table View
            </Link>
          </div>

          <div className="max-w-xl">
            <input
              type="text"
              placeholder="Search collection..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent bg-white"
            />
          </div>

          <div className="mt-3 text-sm text-gray-600">
            {filteredBooks.length} items
          </div>
        </div>
      </div>

      {/* Masonry Grid */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="columns-1 md:columns-2 lg:columns-3 xl:columns-4 gap-6">
          {filteredBooks.map((book) => (
            <div
              key={book.id}
              className="break-inside-avoid mb-6 bg-white rounded-lg shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden"
            >
              {/* Cover Image */}
              <div className="relative">
                {book.coverImageUrl ? (
                  <img
                    src={book.coverImageUrl}
                    alt={book.title}
                    className="w-full h-auto"
                    onError={(e) => {
                      e.currentTarget.src = '';
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-full aspect-[2/3] bg-gradient-to-br from-amber-100 to-amber-200 flex items-center justify-center">
                    <div className="text-center p-4">
                      <div className="text-6xl mb-2">📖</div>
                      <div className="text-sm text-gray-600">No cover available</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="p-5">
                {/* Title & Author */}
                <h3 className="font-bold text-xl text-gray-900 mb-2" style={{fontFamily: 'Georgia, serif'}}>
                  {book.title}
                </h3>
                <p className="text-gray-600 italic mb-4">
                  {book.author || 'Unknown Author'}
                </p>

                {/* Full Context - Always Visible */}
                {book.recommendationContext && (
                  <div className="mb-4 p-4 bg-amber-50 rounded-lg border-l-4 border-amber-400">
                    <div className="flex items-start gap-2 mb-2">
                      <span className="text-amber-600 text-lg">💭</span>
                      <p className="text-sm font-semibold text-amber-900">Why this book?</p>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {book.recommendationContext}
                    </p>
                  </div>
                )}

                {/* Recommender Info */}
                <div className="mb-4 pb-4 border-b border-gray-200">
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                    <span>👤</span>
                    <span className="font-medium">Recommended by</span>
                  </div>
                  <p className="text-sm text-gray-900 font-medium ml-6">{book.guestNames}</p>
                  {book.episodeTitle && (
                    <p className="text-xs text-gray-500 ml-6 mt-1">
                      {book.episodeTitle}
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {book.amazonUrl && (
                    <a
                      href={book.amazonUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium px-4 py-2 rounded-lg text-center transition-colors"
                    >
                      Get Book
                    </a>
                  )}
                  {book.youtubeUrl && (
                    <a
                      href={book.youtubeUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 border-2 border-amber-500 text-amber-700 hover:bg-amber-50 text-sm font-medium px-4 py-2 rounded-lg text-center transition-colors"
                    >
                      Listen
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredBooks.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📚</div>
            <p className="text-xl text-gray-600">No books found</p>
            <p className="text-gray-500 mt-2">Try a different search</p>
          </div>
        )}
      </div>
    </div>
  );
}
