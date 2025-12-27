'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { API_URL } from '@/config/api';
import Navigation from '@/components/Navigation';
// Production deployment with PostgreSQL backend

interface Book {
  id: string;
  title: string;
  author?: string;
  coverImageUrl?: string;
  primaryTheme?: string;
  subthemes?: string[];
  description?: string;
  fictionType?: string;
  businessCategory?: string;
  recommendedBy?: string[];  // Array of recommender names
  recommendationCount?: number;  // Number of times recommended
  amazonUrl?: string;
}

interface ThemeGroup {
  theme: string;
  books: Book[];
}

export default function BooksPage() {
  const [themeGroups, setThemeGroups] = useState<ThemeGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchBooks() {
      try {
        const response = await fetch(`${API_URL}/api/books/aggregated?sort=recommendation_count&order=desc&limit=1000`);
        const data = await response.json();

        console.log('Fetched data:', data);

        // Group books by primaryTheme
        const grouped: Record<string, Book[]> = {};

        // Handle both array and object with recommendations key
        const books = Array.isArray(data) ? data : (data.recommendations || []);

        books.forEach((book: any) => {
          const theme = book.primaryTheme || 'Other';
          if (!grouped[theme]) {
            grouped[theme] = [];
          }
          grouped[theme].push({
            id: book.id,
            title: book.title,
            author: book.author,
            coverImageUrl: book.coverImageUrl,
            primaryTheme: book.primaryTheme,
            subthemes: book.subthemes,
            description: book.description,
            fictionType: book.fictionType,
            businessCategory: book.businessCategory,
            recommendedBy: book.recommendedBy,  // Already an array
            recommendationCount: book.recommendationCount,
            amazonUrl: book.amazonUrl,
          });
        });

        console.log('Grouped themes:', Object.keys(grouped));

        // Convert to array and sort by number of books
        const themeGroupsArray = Object.entries(grouped)
          .map(([theme, books]) => ({ theme, books }))
          .sort((a, b) => b.books.length - a.books.length);

        console.log('Theme groups:', themeGroupsArray.length);
        setThemeGroups(themeGroupsArray);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching books:', error);
        setLoading(false);
      }
    }

    fetchBooks();
  }, []);

  // Filter by search term
  const filteredGroups = themeGroups.map(group => ({
    ...group,
    books: group.books.filter(book =>
      searchTerm === '' ||
      book.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      book.author?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      book.recommendedBy?.some(name => name.toLowerCase().includes(searchTerm.toLowerCase()))
    )
  })).filter(group => group.books.length > 0);

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
        {themeGroups[0]?.books[0]?.coverImageUrl && (
          <div className="absolute inset-0 opacity-30">
            <Image
              src={themeGroups[0].books[0].coverImageUrl}
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
              {themeGroups.reduce((sum, g) => sum + g.books.length, 0)} books from podcast guests • Browse by theme or guest
            </p>

            {/* Search */}
            <div className="max-w-2xl">
              <input
                type="text"
                placeholder="Search by title, author, or recommender..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-6 py-4 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Theme Sections */}
      <div className="px-12 pb-20 -mt-10 relative z-30 space-y-16">
        {filteredGroups.map((group) => (
          <ThemeSection key={group.theme} theme={group.theme} books={group.books} />
        ))}
      </div>
    </div>
  );
}

function ThemeSection({ theme, books }: { theme: string; books: Book[] }) {
  const [showAll, setShowAll] = useState(false);
  const displayBooks = showAll ? books : books.slice(0, 12);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold">{theme}</h2>
        <span className="text-gray-400 text-lg">{books.length} books</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
        {displayBooks.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>

      {books.length > 12 && (
        <div className="flex justify-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
          >
            {showAll ? 'Show Less' : `Show All ${books.length} Books`}
          </button>
        </div>
      )}
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
              {book.recommendedBy && book.recommendedBy.length > 0 && (
                <div className="text-teal-400 text-xs mb-2">
                  <p className="font-semibold">
                    Recommended by {book.recommendationCount || book.recommendedBy.length} {book.recommendationCount === 1 ? 'person' : 'people'}:
                  </p>
                  <p className="mt-1 line-clamp-3">
                    {book.recommendedBy.join(', ')}
                  </p>
                </div>
              )}
            </div>
            <div>
              {book.subthemes && book.subthemes.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {book.subthemes.slice(0, 2).map((subtheme, idx) => (
                    <span key={idx} className="bg-white/20 px-2 py-1 rounded text-xs">
                      {subtheme}
                    </span>
                  ))}
                </div>
              )}
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
