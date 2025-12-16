import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">P</span>
            </div>
            <span className="font-bold text-xl text-gray-900">PodRecs</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link
              href="/browse"
              className="text-gray-700 hover:text-teal-600 font-medium transition-colors"
            >
              Browse
            </Link>
            <Link
              href="/podcasts"
              className="text-gray-700 hover:text-teal-600 font-medium transition-colors"
            >
              Podcasts
            </Link>
            <Link
              href="/search"
              className="text-gray-700 hover:text-teal-600 font-medium transition-colors"
            >
              Search
            </Link>
            <Link
              href="/data"
              className="text-gray-700 hover:text-teal-600 font-medium transition-colors"
            >
              Data
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button className="md:hidden p-2 rounded-lg hover:bg-gray-100">
            <svg
              className="w-6 h-6 text-gray-700"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
