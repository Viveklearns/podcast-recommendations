'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';

interface Book {
  id: string;
  title: string;
  extra_metadata: {
    author?: string;
    coverImageUrl?: string;
    primaryTheme?: string;
    subthemes?: string[];
    description?: string;
    fictionType?: string;
    businessCategory?: string;
  };
}

interface ThemeGroup {
  theme: string;
  books: Book[];
}

export default function BooksNetflixPage() {
  const [themeGroups, setThemeGroups] = useState<ThemeGroup[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchBooks() {
      try {
        const response = await fetch('http://localhost:8000/api/recommendations?type=book&limit=1000');
        const data = await response.json();

        console.log('Fetched data:', data);

        // Group books by primaryTheme
        const grouped: Record<string, Book[]> = {};

        // Handle both array and object with recommendations key
        const books = Array.isArray(data) ? data : (data.recommendations || []);

        books.forEach((book: any) => {
          // Map the flat structure to our Book interface
          const mappedBook: Book = {
            id: book.id,
            title: book.title,
            extra_metadata: {
              author: book.author,
              coverImageUrl: book.coverImageUrl,
              primaryTheme: book.primaryTheme,
              subthemes: book.subthemes,
              description: book.description,
              fictionType: book.fictionType,
              businessCategory: book.businessCategory,
            }
          };

          const theme = mappedBook.extra_metadata?.primaryTheme || 'Other';
          if (!grouped[theme]) {
            grouped[theme] = [];
          }
          grouped[theme].push(mappedBook);
        });

        console.log('Grouped themes:', Object.keys(grouped));

        // Convert to array and sort by number of books
        const themeGroupsArray = Object.entries(grouped)
          .map(([theme, books]) => ({ theme, books }))
          .sort((a, b) => b.books.length - a.books.length)
          .filter(group => group.books.length >= 3); // Only show themes with 3+ books

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

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-2xl">Loading...</div>
      </div>
    );
  }

  if (themeGroups.length === 0) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center flex-col gap-4">
        <div className="text-2xl">No themed books found</div>
        <div className="text-gray-400">Check console for errors</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <div className="relative h-[80vh] w-full overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent z-10" />
        {themeGroups[0]?.books[0]?.extra_metadata?.coverImageUrl && (
          <div className="absolute inset-0 opacity-40">
            <Image
              src={themeGroups[0].books[0].extra_metadata.coverImageUrl}
              alt="Featured book"
              fill
              className="object-cover blur-sm"
            />
          </div>
        )}
        <div className="relative z-20 h-full flex flex-col justify-end p-12 max-w-7xl mx-auto">
          <h1 className="text-6xl font-bold mb-4">Book Recommendations by Theme</h1>
          <p className="text-xl text-gray-300 max-w-2xl mb-8">
            {themeGroups.length} themes • Curated from top podcast conversations
          </p>
        </div>
      </div>

      {/* Theme Rows */}
      <div className="px-12 pb-20 -mt-32 relative z-30">
        {themeGroups.map((group) => (
          <ThemeRow key={group.theme} theme={group.theme} books={group.books} />
        ))}
      </div>
    </div>
  );
}

function ThemeRow({ theme, books }: { theme: string; books: Book[] }) {
  const [scrollPosition, setScrollPosition] = useState(0);
  const containerRef = useState<HTMLDivElement | null>(null)[0];

  const scroll = (direction: 'left' | 'right') => {
    const container = document.getElementById(`scroll-${theme}`);
    if (container) {
      const scrollAmount = direction === 'left' ? -800 : 800;
      container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  return (
    <div className="mb-12">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold">{theme}</h2>
        <span className="text-gray-400 text-sm">{books.length} books</span>
      </div>

      <div className="relative group">
        {/* Left Arrow */}
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-black/80 hover:bg-black p-4 rounded-r-md opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* Books Scroll Container */}
        <div
          id={`scroll-${theme}`}
          className="flex gap-4 overflow-x-auto scrollbar-hide scroll-smooth"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>

        {/* Right Arrow */}
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-black/80 hover:bg-black p-4 rounded-l-md opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function BookCard({ book }: { book: Book }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className="flex-shrink-0 w-48 transition-transform duration-300 hover:scale-110 cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="relative aspect-[2/3] rounded-md overflow-hidden bg-gray-800">
        {book.extra_metadata?.coverImageUrl ? (
          <Image
            src={book.extra_metadata.coverImageUrl}
            alt={book.title}
            fill
            className="object-cover"
            sizes="192px"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center p-4 text-center">
            <span className="text-sm font-medium line-clamp-4">{book.title}</span>
          </div>
        )}

        {/* Hover Overlay */}
        {isHovered && (
          <div className="absolute inset-0 bg-black/90 p-4 flex flex-col justify-end text-xs">
            <h3 className="font-semibold mb-1 line-clamp-2">{book.title}</h3>
            {book.extra_metadata?.author && (
              <p className="text-gray-400 mb-2 line-clamp-1">{book.extra_metadata.author}</p>
            )}
            {book.extra_metadata?.subthemes && (
              <div className="flex flex-wrap gap-1">
                {book.extra_metadata.subthemes.slice(0, 2).map((subtheme, idx) => (
                  <span key={idx} className="bg-white/20 px-2 py-1 rounded text-xs">
                    {subtheme}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
