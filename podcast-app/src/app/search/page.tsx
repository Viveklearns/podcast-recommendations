'use client';

import { useState } from "react";
import RecommendationCard from "@/components/RecommendationCard";
import { searchRecommendations } from "@/lib/api";

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (value: string) => {
    setSearchQuery(value);
    setIsSearching(value.trim().length > 0);

    if (value.trim().length === 0) {
      setSearchResults([]);
      return;
    }

    setIsLoading(true);
    try {
      const results = await searchRecommendations(value);
      setSearchResults(results || []);
    } catch (error) {
      console.error("Search failed:", error);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredResults = searchResults;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Search Header */}
      <div className="bg-gradient-to-br from-primary-600 to-primary-800 text-white py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-center">
            Search Recommendations
          </h1>
          <div className="relative">
            <input
              type="text"
              placeholder="Search by title, author, guest, or keyword..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full px-6 py-4 pr-12 rounded-lg text-gray-900 text-lg focus:outline-none focus:ring-4 focus:ring-primary-300"
              autoFocus
            />
            <svg
              className="absolute right-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          {isSearching && (
            <p className="text-primary-100 text-center mt-4">
              {isLoading ? (
                "Searching..."
              ) : (
                <>Found {filteredResults.length} result{filteredResults.length !== 1 ? "s" : ""}</>
              )}
            </p>
          )}
        </div>
      </div>

      {/* Results */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!isSearching ? (
          /* Empty State - Before Search */
          <div className="text-center py-16">
            <div className="text-6xl mb-6">🔍</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Start Searching
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto mb-8">
              Search through hundreds of recommendations from top podcasts. Try searching for
              a book title, movie name, author, or even a topic you're interested in.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              <button
                onClick={() => handleSearch("book")}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:border-primary-400 hover:text-primary-600 transition-colors"
              >
                Books
              </button>
              <button
                onClick={() => handleSearch("Figma")}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:border-primary-400 hover:text-primary-600 transition-colors"
              >
                Figma
              </button>
              <button
                onClick={() => handleSearch("AI")}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:border-primary-400 hover:text-primary-600 transition-colors"
              >
                AI
              </button>
              <button
                onClick={() => handleSearch("product")}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:border-primary-400 hover:text-primary-600 transition-colors"
              >
                Products
              </button>
            </div>
          </div>
        ) : filteredResults.length > 0 ? (
          /* Search Results */
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Search Results for &quot;{searchQuery}&quot;
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {filteredResults.map((rec) => (
                <RecommendationCard key={rec.id} recommendation={rec} />
              ))}
            </div>
          </div>
        ) : (
          /* No Results */
          <div className="text-center py-16">
            <div className="text-6xl mb-6">😕</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              No results found for &quot;{searchQuery}&quot;
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto mb-8">
              Try searching with different keywords, or browse all recommendations.
            </p>
            <button
              onClick={() => handleSearch("")}
              className="px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors"
            >
              Clear Search
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
