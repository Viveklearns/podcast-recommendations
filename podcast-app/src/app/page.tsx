'use client';

import Link from "next/link";
import RecommendationCard from "@/components/RecommendationCard";
import PodcastBadge from "@/components/PodcastBadge";
import { useApi } from "@/hooks/useApi";
import { getRecommendations, getPodcasts, getStats } from "@/lib/api";

export default function Home() {
  // Fetch data from backend API (fetch more for better variety)
  const { data: allRecommendations, loading: recsLoading } = useApi(() => getRecommendations({ limit: 100 }));
  const { data: podcasts, loading: podcastsLoading } = useApi(getPodcasts);
  const { data: stats } = useApi(getStats);

  // Show loading state
  if (recsLoading || podcastsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-semibold text-gray-700">Loading recommendations...</div>
        </div>
      </div>
    );
  }

  const recommendations = allRecommendations || [];
  const podcastList = podcasts || [];

  const featuredRecommendations = recommendations.slice(0, 4);
  const bookRecommendations = recommendations.filter(r => r.type === 'book').slice(0, 3);
  const movieRecommendations = recommendations.filter(r => r.type === 'movie' || r.type === 'tv_show').slice(0, 3);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-teal-600 to-teal-900 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            Discover What Experts Recommend
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-teal-100 max-w-3xl mx-auto">
            Books, movies, apps, and more—curated from the top podcasts in the US
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/browse"
              className="bg-white text-teal-700 px-8 py-4 rounded-lg font-semibold hover:bg-teal-50 transition-colors text-lg"
            >
              Browse All Recommendations
            </Link>
            <Link
              href="/search"
              className="bg-teal-700 text-white px-8 py-4 rounded-lg font-semibold hover:bg-teal-800 transition-colors text-lg border-2 border-white"
            >
              Search
            </Link>
          </div>

          {/* Stats */}
          <div className="mt-12 grid grid-cols-3 gap-8 max-w-2xl mx-auto">
            <div>
              <div className="text-4xl font-bold">{stats?.total_recommendations || 0}</div>
              <div className="text-teal-200 text-sm">Recommendations</div>
            </div>
            <div>
              <div className="text-4xl font-bold">{stats?.total_podcasts || 0}</div>
              <div className="text-teal-200 text-sm">Podcasts</div>
            </div>
            <div>
              <div className="text-4xl font-bold">{stats?.total_episodes || 0}</div>
              <div className="text-teal-200 text-sm">Episodes</div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Recommendations */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold text-gray-900">Featured Recommendations</h2>
            <Link href="/browse" className="text-teal-600 hover:text-teal-700 font-semibold">
              View All →
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredRecommendations.map((rec) => (
              <RecommendationCard key={rec.id} recommendation={rec} />
            ))}
          </div>
        </div>
      </section>

      {/* Browse by Category */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Browse by Category</h2>

          {/* Books */}
          <div className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-semibold text-gray-800">📚 Books</h3>
              <Link href="/browse?type=book" className="text-teal-600 hover:text-teal-700 font-semibold">
                View All Books →
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {bookRecommendations.map((rec) => (
                <RecommendationCard key={rec.id} recommendation={rec} />
              ))}
            </div>
          </div>

          {/* Movies & TV */}
          <div className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-semibold text-gray-800">🎬 Movies & TV Shows</h3>
              <Link href="/browse?type=movie" className="text-teal-600 hover:text-teal-700 font-semibold">
                View All →
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {movieRecommendations.map((rec) => (
                <RecommendationCard key={rec.id} recommendation={rec} />
              ))}
            </div>
          </div>

          {/* Category Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-12">
            <Link
              href="/browse?type=book"
              className="bg-teal-50 border-2 border-teal-200 rounded-lg p-6 text-center hover:border-teal-400 hover:shadow-lg transition-all"
            >
              <div className="text-4xl mb-2">📚</div>
              <div className="font-semibold text-gray-900">Books</div>
              <div className="text-sm text-gray-600">{recommendations.filter(r => r.type === 'book').length} items</div>
            </Link>
            <Link
              href="/browse?type=movie"
              className="bg-purple-50 border-2 border-purple-200 rounded-lg p-6 text-center hover:border-purple-400 hover:shadow-lg transition-all"
            >
              <div className="text-4xl mb-2">🎬</div>
              <div className="font-semibold text-gray-900">Movies</div>
              <div className="text-sm text-gray-600">{recommendations.filter(r => r.type === 'movie').length} items</div>
            </Link>
            <Link
              href="/browse?type=tv_show"
              className="bg-pink-50 border-2 border-pink-200 rounded-lg p-6 text-center hover:border-pink-400 hover:shadow-lg transition-all"
            >
              <div className="text-4xl mb-2">📺</div>
              <div className="font-semibold text-gray-900">TV Shows</div>
              <div className="text-sm text-gray-600">{recommendations.filter(r => r.type === 'tv_show').length} items</div>
            </Link>
            <Link
              href="/browse?type=app"
              className="bg-green-50 border-2 border-green-200 rounded-lg p-6 text-center hover:border-green-400 hover:shadow-lg transition-all"
            >
              <div className="text-4xl mb-2">📱</div>
              <div className="font-semibold text-gray-900">Apps</div>
              <div className="text-sm text-gray-600">{recommendations.filter(r => r.type === 'app').length} items</div>
            </Link>
          </div>
        </div>
      </section>

      {/* Browse by Podcast */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold text-gray-900">Browse by Podcast</h2>
            <Link href="/podcasts" className="text-teal-600 hover:text-teal-700 font-semibold">
              View All Podcasts →
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {podcastList.slice(0, 6).map((podcast) => (
              <PodcastBadge key={podcast.id} podcast={podcast} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-teal-600 to-teal-700">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Never Miss a Great Recommendation
          </h2>
          <p className="text-xl text-teal-100 mb-8">
            We automatically extract and organize recommendations from every episode
          </p>
          <Link
            href="/browse"
            className="bg-white text-teal-700 px-8 py-4 rounded-lg font-semibold hover:bg-teal-50 transition-colors inline-block text-lg"
          >
            Start Exploring
          </Link>
        </div>
      </section>
    </div>
  );
}
