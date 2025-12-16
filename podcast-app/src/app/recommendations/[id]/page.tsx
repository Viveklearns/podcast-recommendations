import { notFound } from "next/navigation";
import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getRecommendationWithDetails(id: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/recommendations/${id}`, {
      cache: 'no-store'
    });

    if (!res.ok) {
      return null;
    }

    return res.json();
  } catch (error) {
    console.error('Error fetching recommendation:', error);
    return null;
  }
}

export default async function RecommendationDetailPage({ params }: { params: { id: string } }) {
  const data = await getRecommendationWithDetails(params.id);

  if (!data) {
    notFound();
  }

  const recommendation = data;
  const episode = data.episode;
  const podcast = data.podcast;

  const getImageUrl = () => {
    if (recommendation.type === "book") {
      return recommendation.coverImageUrl;
    } else if (recommendation.type === "movie" || recommendation.type === "tv_show") {
      return recommendation.posterUrl;
    } else {
      return recommendation.imageUrl;
    }
  };

  const getTypeLabel = () => {
    switch (recommendation.type) {
      case "book":
        return "Book";
      case "movie":
        return "Movie";
      case "tv_show":
        return "TV Show";
      case "app":
        return "App";
      case "podcast":
        return "Podcast";
      case "product":
        return "Product";
      default:
        return "Other";
    }
  };

  const formatTimestamp = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Breadcrumbs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <nav className="flex items-center space-x-2 text-sm text-gray-600">
            <Link href="/" className="hover:text-primary-600">
              Home
            </Link>
            <span>/</span>
            <Link href="/browse" className="hover:text-primary-600">
              Browse
            </Link>
            <span>/</span>
            <span className="text-gray-900">{recommendation.title}</span>
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Image Section */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg border border-gray-200 p-6 sticky top-20">
              <div className="relative aspect-[2/3] bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg overflow-hidden mb-4">
                {getImageUrl() ? (
                  <img
                    src={getImageUrl()}
                    alt={recommendation.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <span className="text-gray-400 text-6xl">📚</span>
                  </div>
                )}
              </div>

              {/* External Links */}
              <div className="space-y-2">
                {recommendation.type === "book" && "amazonUrl" in recommendation && recommendation.amazonUrl && (
                  <a
                    href={recommendation.amazonUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full px-4 py-3 bg-yellow-500 text-white rounded-lg font-semibold text-center hover:bg-yellow-600 transition-colors"
                  >
                    View on Amazon
                  </a>
                )}
                {recommendation.type === "book" && "googleBooksUrl" in recommendation && recommendation.googleBooksUrl && (
                  <a
                    href={recommendation.googleBooksUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full px-4 py-3 bg-teal-600 text-white rounded-lg font-semibold text-center hover:bg-teal-700 transition-colors"
                  >
                    View on Google Books
                  </a>
                )}
                {recommendation.type !== "book" && "url" in recommendation && recommendation.url && (
                  <a
                    href={recommendation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full px-4 py-3 bg-primary-600 text-white rounded-lg font-semibold text-center hover:bg-primary-700 transition-colors"
                  >
                    Visit Website
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Content Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-gray-200 p-8">
              {/* Header */}
              <div className="mb-6">
                <span className="inline-block px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-semibold mb-4">
                  {getTypeLabel()}
                </span>
                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                  {recommendation.title}
                </h1>
                {recommendation.type === "book" && "author" in recommendation && recommendation.author && (
                  <p className="text-xl text-gray-600 mb-4">by {recommendation.author}</p>
                )}
                {(recommendation.type === "movie" || recommendation.type === "tv_show") && "creatorDirector" in recommendation && recommendation.creatorDirector && (
                  <p className="text-xl text-gray-600 mb-4">
                    Directed by {recommendation.creatorDirector}
                  </p>
                )}
              </div>

              {/* Ratings */}
              <div className="flex items-center space-x-6 mb-6">
                {recommendation.type === "book" && "goodreadsRating" in recommendation && recommendation.goodreadsRating && (
                  <div className="flex items-center">
                    <span className="text-yellow-500 text-2xl mr-2">★</span>
                    <span className="text-2xl font-bold text-gray-900">
                      {recommendation.goodreadsRating.toFixed(2)}
                    </span>
                    <span className="text-gray-500 ml-2">Goodreads</span>
                  </div>
                )}
                {((recommendation.type === "movie" || recommendation.type === "tv_show") && "rating" in recommendation && recommendation.rating) && (
                  <div className="flex items-center">
                    <span className="text-yellow-500 text-2xl mr-2">★</span>
                    <span className="text-2xl font-bold text-gray-900">
                      {recommendation.rating.toFixed(1)}
                    </span>
                    <span className="text-gray-500 ml-2">IMDB</span>
                  </div>
                )}
                <div className="flex items-center">
                  <span className="text-green-500 text-2xl mr-2">✓</span>
                  <span className="text-gray-700">
                    {(recommendation.confidenceScore * 100).toFixed(0)}% Confidence
                  </span>
                </div>
              </div>

              <hr className="my-6" />

              {/* Description */}
              {"description" in recommendation && recommendation.description && (
                <div className="mb-6">
                  <h2 className="text-2xl font-semibold text-gray-900 mb-3">About</h2>
                  <p className="text-gray-700 leading-relaxed">{recommendation.description}</p>
                </div>
              )}

              {/* Why Recommended */}
              <div className="mb-6 bg-primary-50 border-l-4 border-primary-600 p-6 rounded-r-lg">
                <h2 className="text-xl font-semibold text-gray-900 mb-3">
                  Why it was recommended
                </h2>
                <p className="text-gray-700 leading-relaxed mb-4">
                  {recommendation.recommendationContext}
                </p>
                <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600">
                  &quot;{recommendation.quoteFromEpisode}&quot;
                </blockquote>
                <p className="text-sm text-gray-600 mt-3">
                  — {recommendation.recommendedBy}
                </p>
              </div>

              {/* Episode Info */}
              {episode && podcast && (
                <div className="mb-6 bg-gray-50 rounded-lg p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    From the Episode
                  </h2>
                  <div className="flex items-start space-x-4">
                    <img
                      src={podcast.imageUrl}
                      alt={podcast.name}
                      className="w-16 h-16 rounded-lg object-cover"
                    />
                    <div className="flex-1">
                      <Link
                        href={`/podcasts/${podcast.id}`}
                        className="text-primary-600 hover:text-primary-700 font-semibold"
                      >
                        {podcast.name}
                      </Link>
                      <p className="text-gray-900 font-medium mt-1">{episode.title}</p>
                      <p className="text-sm text-gray-600 mt-1">
                        {new Date(episode.publishedDate).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                      <div className="mt-3">
                        <a
                          href={episode.youtubeUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-semibold"
                        >
                          <span>▶</span>
                          <span>Watch on YouTube</span>
                          <span className="text-xs opacity-80">
                            @ {formatTimestamp(recommendation.timestampSeconds)}
                          </span>
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Additional Details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                {recommendation.type === "book" && (
                  <>
                    {"publisher" in recommendation && recommendation.publisher && (
                      <div>
                        <span className="text-gray-600">Publisher:</span>
                        <span className="ml-2 text-gray-900 font-medium">{recommendation.publisher}</span>
                      </div>
                    )}
                    {"publishedYear" in recommendation && recommendation.publishedYear && (
                      <div>
                        <span className="text-gray-600">Published:</span>
                        <span className="ml-2 text-gray-900 font-medium">{recommendation.publishedYear}</span>
                      </div>
                    )}
                    {"pageCount" in recommendation && recommendation.pageCount && (
                      <div>
                        <span className="text-gray-600">Pages:</span>
                        <span className="ml-2 text-gray-900 font-medium">{recommendation.pageCount}</span>
                      </div>
                    )}
                    {"isbn" in recommendation && recommendation.isbn && (
                      <div>
                        <span className="text-gray-600">ISBN:</span>
                        <span className="ml-2 text-gray-900 font-medium">{recommendation.isbn}</span>
                      </div>
                    )}
                  </>
                )}
                {(recommendation.type === "movie" || recommendation.type === "tv_show") && (
                  <>
                    {"releaseYear" in recommendation && recommendation.releaseYear && (
                      <div>
                        <span className="text-gray-600">Release Year:</span>
                        <span className="ml-2 text-gray-900 font-medium">{recommendation.releaseYear}</span>
                      </div>
                    )}
                    {"genre" in recommendation && recommendation.genre && (
                      <div>
                        <span className="text-gray-600">Genre:</span>
                        <span className="ml-2 text-gray-900 font-medium">{recommendation.genre.join(', ')}</span>
                      </div>
                    )}
                    {"streamingPlatforms" in recommendation && recommendation.streamingPlatforms && recommendation.streamingPlatforms.length > 0 && (
                      <div className="col-span-2">
                        <span className="text-gray-600">Available on:</span>
                        <span className="ml-2 text-gray-900 font-medium">
                          {recommendation.streamingPlatforms.join(', ')}
                        </span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
