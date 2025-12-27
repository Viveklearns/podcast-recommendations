export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center space-y-4">
          {/* Brand */}
          <div>
            <div className="flex items-center justify-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                <span className="text-black font-bold text-2xl">📚</span>
              </div>
              <span className="font-bold text-3xl text-white">PodBooks</span>
            </div>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Discover books recommended by your favorite podcast guests
            </p>
          </div>

          <div className="border-t border-white/10 mt-8 pt-8">
            <p className="text-gray-500 text-sm">
              © 2024 PodBooks. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
