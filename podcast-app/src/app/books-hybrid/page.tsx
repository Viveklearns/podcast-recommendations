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

export default function BooksHybridPage() {
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

  const recentBooks = books.slice(0, 12);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-2xl text-gray-600">Loading books...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Book Recommendations</h1>
              <p className="text-gray-600 mt-1">{books.length} books from podcast episodes</p>
            </div>
            <Link href="/books" className="text-teal-600 hover:text-teal-700 font-medium">
              ← Table View
            </Link>
          </div>

          <div className="max-w-xl">
            <input
              type="text"
              placeholder="Search books, authors, or guests..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent text-lg"
            />
          </div>
        </div>
      </div>

      {/* Featured Carousel */}
      {!searchTerm && (
        <div className="bg-gradient-to-b from-white to-gray-50 border-b border-gray-200 pb-8">
          <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Top Picks</h2>
              <span className="text-sm text-gray-500">Recently added recommendations</span>
            </div>

            <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
              {recentBooks.map((book) => (
                <div
                  key={book.id}
                  className="flex-shrink-0 w-56 bg-white rounded-lg shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden group"
                >
                  <div className="relative aspect-[2/3] bg-gray-100 overflow-hidden">
                    {book.coverImageUrl ? (
                      <img
                        src={book.coverImageUrl}
                        alt={book.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <div className="text-5xl">📖</div>
                      </div>
                    )}
                  </div>

                  <div className="p-3">
                    <h3 className="font-bold text-sm text-gray-900 line-clamp-2 mb-1">
                      {book.title}
                    </h3>
                    <p className="text-xs text-gray-600 mb-2">{book.author}</p>
                    <div className="flex gap-1">
                      {book.amazonUrl && (
                        <a
                          href={book.amazonUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-1 bg-teal-500 hover:bg-teal-600 text-white text-xs font-medium px-2 py-1.5 rounded text-center"
                        >
                          View
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            {searchTerm ? 'Search Results' : 'All Books'}
          </h2>
          <span className="text-sm text-gray-600">{filteredBooks.length} books</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredBooks.map((book) => (
            <div
              key={book.id}
              className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden"
            >
              {/* Cover */}
              <div className="relative aspect-[2/3] bg-gray-100">
                {book.coverImageUrl ? (
                  <img
                    src={book.coverImageUrl}
                    alt={book.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <div className="text-6xl">📖</div>
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="p-4">
                <h3 className="font-bold text-lg text-gray-900 line-clamp-2 mb-1">
                  {book.title}
                </h3>
                <p className="text-gray-600 text-sm mb-3">
                  {book.author || 'Unknown Author'}
                </p>

                {/* Context */}
                {book.recommendationContext && (
                  <div className="mb-3 p-3 bg-teal-50 rounded-lg border-l-4 border-teal-500">
                    <div className="flex items-start gap-2">
                      <span className="text-teal-600 text-sm flex-shrink-0">💬</span>
                      <p className="text-sm text-gray-700 line-clamp-3">
                        {book.recommendationContext}
                      </p>
                    </div>
                  </div>
                )}

                {/* Recommender */}
                <div className="mb-3 text-sm">
                  <span className="text-gray-600">👤 </span>
                  <span className="text-gray-900 font-medium">{book.guestNames}</span>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {book.amazonUrl && (
                    <a
                      href={book.amazonUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium px-4 py-2 rounded-lg text-center transition-colors"
                    >
                      Amazon
                    </a>
                  )}
                  {book.youtubeUrl && (
                    <a
                      href={book.youtubeUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 bg-red-500 hover:bg-red-600 text-white text-sm font-medium px-4 py-2 rounded-lg text-center transition-colors"
                    >
                      Watch
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
            <p className="text-gray-500 mt-2">Try adjusting your search</p>
          </div>
        )}
      </div>

      <style jsx>{`
        .scrollbar-thin::-webkit-scrollbar {
          height: 8px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: #cbd5e0;
          border-radius: 10px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: #a0aec0;
        }
      `}</style>
    </div>
  );
}
