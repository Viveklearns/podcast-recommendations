'use client';

import { useState, useEffect } from 'react';

interface Category {
  type: string;
  count: number;
  percentage: number;
}

interface Book {
  title: string;
  timesRecommended: number;
  author?: string;
  coverImageUrl?: string;
  isbn?: string;
  amazonUrl?: string;
}

export default function AnalyticsPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [topBooks, setTopBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalRecs, setTotalRecs] = useState(0);

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch categories
        const categoriesRes = await fetch('http://localhost:8000/api/analytics/categories');
        const categoriesData = await categoriesRes.json();
        setCategories(categoriesData.categories);
        setTotalRecs(categoriesData.total);

        // Fetch top books
        const booksRes = await fetch('http://localhost:8000/api/analytics/top-books?limit=20');
        const booksData = await booksRes.json();
        setTopBooks(booksData.books);

        setLoading(false);
      } catch (error) {
        console.error('Error fetching analytics:', error);
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Podcast Recommendations Analytics
          </h1>
          <p className="text-xl text-gray-600">
            Insights from {totalRecs.toLocaleString()} recommendations across 291 episodes
          </p>
        </div>

        {/* Categories Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Recommendations by Category
          </h2>
          <div className="space-y-4">
            {categories.map((category, index) => (
              <div key={category.type} className="flex items-center">
                <div className="w-32 text-sm font-medium text-gray-700 capitalize">
                  {category.type === 'tv_show' ? 'TV Shows' : category.type}
                </div>
                <div className="flex-1 ml-4">
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-6 mr-4">
                      <div
                        className="bg-blue-600 h-6 rounded-full flex items-center justify-end pr-2"
                        style={{ width: `${category.percentage}%` }}
                      >
                        <span className="text-xs text-white font-semibold">
                          {category.percentage}%
                        </span>
                      </div>
                    </div>
                    <div className="w-16 text-right text-sm font-semibold text-gray-900">
                      {category.count}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Books Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Most Recommended Books
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {topBooks.map((book, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start space-x-4">
                  {/* Book Cover */}
                  {book.coverImageUrl && (
                    <div className="flex-shrink-0">
                      <img
                        src={book.coverImageUrl}
                        alt={book.title}
                        className="w-20 h-28 object-cover rounded shadow-sm"
                      />
                    </div>
                  )}

                  {/* Book Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {book.title}
                        </h3>
                        {book.author && (
                          <p className="text-sm text-gray-600 mb-2">
                            by {book.author}
                          </p>
                        )}
                      </div>
                      <div className="ml-4 flex-shrink-0">
                        <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                          {book.timesRecommended}x
                        </div>
                      </div>
                    </div>

                    {book.amazonUrl && (
                      <a
                        href={book.amazonUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block mt-2 text-sm text-blue-600 hover:text-blue-800"
                      >
                        View on Amazon →
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Navigation */}
        <div className="mt-8 text-center">
          <a
            href="/"
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Home
          </a>
        </div>
      </div>
    </div>
  );
}
