export default function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">P</span>
              </div>
              <span className="font-bold text-xl text-gray-900">PodRecs</span>
            </div>
            <p className="text-gray-600 text-sm">
              Discover books, movies, and recommendations from your favorite podcasts.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Explore</h3>
            <ul className="space-y-2">
              <li>
                <a href="/browse" className="text-gray-600 hover:text-teal-600 text-sm">
                  Browse All
                </a>
              </li>
              <li>
                <a href="/browse?type=book" className="text-gray-600 hover:text-primary-600 text-sm">
                  Books
                </a>
              </li>
              <li>
                <a href="/browse?type=movie" className="text-gray-600 hover:text-primary-600 text-sm">
                  Movies & TV
                </a>
              </li>
              <li>
                <a href="/podcasts" className="text-gray-600 hover:text-primary-600 text-sm">
                  Podcasts
                </a>
              </li>
            </ul>
          </div>

          {/* Podcasts */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Top Podcasts</h3>
            <ul className="space-y-2">
              <li>
                <span className="text-gray-600 text-sm">The Tim Ferriss Show</span>
              </li>
              <li>
                <span className="text-gray-600 text-sm">Huberman Lab</span>
              </li>
              <li>
                <span className="text-gray-600 text-sm">The Joe Rogan Experience</span>
              </li>
              <li>
                <span className="text-gray-600 text-sm">The Diary of a CEO</span>
              </li>
            </ul>
          </div>

          {/* About */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">About</h3>
            <ul className="space-y-2">
              <li>
                <a href="/about" className="text-gray-600 hover:text-primary-600 text-sm">
                  About Us
                </a>
              </li>
              <li>
                <a href="/faq" className="text-gray-600 hover:text-primary-600 text-sm">
                  FAQ
                </a>
              </li>
              <li>
                <a href="/privacy" className="text-gray-600 hover:text-primary-600 text-sm">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="/contact" className="text-gray-600 hover:text-primary-600 text-sm">
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-200 mt-8 pt-8 text-center">
          <p className="text-gray-600 text-sm">
            © 2024 PodRecs. All rights reserved. Built with Claude Code.
          </p>
        </div>
      </div>
    </footer>
  );
}
