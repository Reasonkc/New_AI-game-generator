import { useState, useEffect } from "react";
import { Search, Gamepad2, Loader, Clock, Trash2 } from "lucide-react";

export default function Gallery() {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchGames = async () => {
      try {
        const res = await fetch("http://127.0.0.1:5000/list_games");
        if (res.ok) {
          const data = await res.json();
          setGames(data.games || []);
        }
      } catch (err) {
        console.error("Failed to load games:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchGames();
  }, []);

  const filtered = games.filter(
    (g) =>
      g.title?.toLowerCase().includes(search.toLowerCase()) ||
      g.genre?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Game Gallery</h1>
          <p className="text-gray-600">Browse all generated games</p>
        </div>

        <div className="relative max-w-md mx-auto mb-10">
          <input
            type="text"
            placeholder="Search by title or genre..."
            className="w-full p-4 pl-12 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Search className="absolute left-4 top-4 text-gray-400" size={20} />
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="text-center">
              <Loader size={40} className="text-indigo-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-500">Loading games...</p>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <Gamepad2 size={48} className="text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              {search ? "No games match your search" : "No games created yet"}
            </h3>
            <p className="text-gray-500 mb-6">
              {search
                ? "Try a different search term"
                : "Head to the Create page to generate your first game!"}
            </p>
            {!search && (
              <a
                href="/create"
                className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors"
              >
                Create Your First Game
              </a>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((game) => (
              <div
                key={game.id}
                onClick={() => (window.location.href = `/game/${game.id}`)}
                className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-200 cursor-pointer border border-gray-100 overflow-hidden group"
              >
                <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-4 text-white">
                  <h3 className="font-bold text-lg truncate">{game.title || "Untitled Game"}</h3>
                  <span className="text-xs bg-white/20 px-2 py-1 rounded-full">
                    {game.genre || "Game"}
                  </span>
                </div>
                <div className="p-4">
                  <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                    {game.description?.slice(0, 120) || "AI-generated game"}...
                  </p>
                  <div className="flex items-center text-xs text-gray-400">
                    <Clock size={12} className="mr-1" />
                    {game.created_at
                      ? new Date(game.created_at).toLocaleDateString()
                      : "Unknown date"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
