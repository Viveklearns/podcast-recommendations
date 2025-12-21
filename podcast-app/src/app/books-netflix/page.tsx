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

export default function BooksNetflixPage() {
  const [books, setBooks] = useState<BookData[]>([]);
  const [loading, setLoading] = useState(true);

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

  // Group books by different categories
  const recentBooks = books.slice(0, 20);
  const byGuest = books.reduce((acc, book) => {
    const guest = book.guestNames || 'Unknown';
    if (!acc[guest]) acc[guest] = [];
    acc[guest].push(book);
    return acc;
  }, {} as Record<string, BookData[]>);

  const topGuests = Object.entries(byGuest)
    .sort(([, a], [, b]) => b.length - a.length)
    .slice(0, 5);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-2xl text-gray-300">Loading books...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gradient-to-b from-gray-800 to-gray-900 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Podcast Book Recommendations</h1>
              <p className="text-gray-400 mt-1">{books.length} books from episodes</p>
            </div>
            <Link href="/books" className="text-teal-400 hover:text-teal-300 font-medium">
              ← Table View
            </Link>
          </div>
        </div>
      </div>

      {/* Featured/Hero Section */}
      {recentBooks[0] && (
        <div className="relative h-[500px] mb-8">
          <div className="absolute inset-0 bg-gradient-to-r from-gray-900 via-gray-900/70 to-transparent z-10"></div>
          <div
            className="absolute inset-0 bg-cover bg-center blur-sm opacity-30"
            style={{
              backgroundImage: recentBooks[0].coverImageUrl
                ? `url(${recentBooks[0].coverImageUrl})`
                : 'none'
            }}
          ></div>

          <div className="relative z-20 max-w-7xl mx-auto px-6 py-16 h-full flex items-center">
            <div className="max-w-2xl">
              <div className="text-sm text-teal-400 font-semibold mb-2">FEATURED RECOMMENDATION</div>
              <h2 className="text-5xl font-bold mb-4">{recentBooks[0].title}</h2>
              <p className="text-xl text-gray-300 mb-2">by {recentBooks[0].author}</p>
              <div className="bg-gray-800/80 p-4 rounded-lg mb-6 max-w-xl">
                <p className="text-gray-200">{recentBooks[0].recommendationContext?.substring(0, 200)}...</p>
              </div>
              <div className="text-sm text-gray-400 mb-6">
                Recommended by {recentBooks[0].guestNames}
              </div>
              <div className="flex gap-3">
                {recentBooks[0].amazonUrl && (
                  <a
                    href={recentBooks[0].amazonUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-orange-500 hover:bg-orange-600 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
                  >
                    View on Amazon
                  </a>
                )}
                {recentBooks[0].youtubeUrl && (
                  <a
                    href={recentBooks[0].youtubeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-gray-700 hover:bg-gray-600 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
                  >
                    Watch Episode
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recently Added Row */}
      <div className="max-w-7xl mx-auto px-6 mb-12">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Recently Added</h2>
        </div>
        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
          {recentBooks.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      </div>

      {/* Rows by Guest */}
      {topGuests.map(([guest, guestBooks]) => (
        <div key={guest} className="max-w-7xl mx-auto px-6 mb-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Recommended by {guest}</h2>
            <span className="text-gray-400 text-sm">{guestBooks.length} books</span>
          </div>
          <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
            {guestBooks.slice(0, 10).map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        </div>
      ))}

      <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}

function BookCard({ book }: { book: BookData }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div
      className="flex-shrink-0 w-48 cursor-pointer transition-transform hover:scale-105 relative"
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
    >
      {/* Cover */}
      <div className="aspect-[2/3] bg-gray-800 rounded-lg overflow-hidden mb-2 relative">
        {book.coverImageUrl ? (
          <img
            src={book.coverImageUrl}
            alt={book.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-600">
            <div className="text-center">
              <div className="text-4xl mb-2">📖</div>
            </div>
          </div>
        )}

        {/* Hover Overlay */}
        {showDetails && (
          <div className="absolute inset-0 bg-black/90 p-3 flex flex-col justify-between text-xs">
            <div>
              <p className="font-bold mb-1 line-clamp-2">{book.title}</p>
              <p className="text-gray-400 mb-2">{book.author}</p>
              {book.recommendationContext && (
                <p className="text-gray-300 line-clamp-4 text-xs">
                  {book.recommendationContext}
                </p>
              )}
            </div>
            <div className="flex gap-1">
              {book.amazonUrl && (
                <a
                  href={book.amazonUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 bg-orange-500 hover:bg-orange-600 text-white text-xs py-1 rounded text-center"
                  onClick={(e) => e.stopPropagation()}
                >
                  Amazon
                </a>
              )}
              {book.youtubeUrl && (
                <a
                  href={book.youtubeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 bg-red-500 hover:bg-red-600 text-white text-xs py-1 rounded text-center"
                  onClick={(e) => e.stopPropagation()}
                >
                  Watch
                </a>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Title below */}
      <p className="text-sm font-medium line-clamp-2">{book.title}</p>
      <p className="text-xs text-gray-400">{book.author}</p>
    </div>
  );
}
