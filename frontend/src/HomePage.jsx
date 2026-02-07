import { useState, useEffect } from 'react';
import { Search, Plus, ChevronRight, Sparkles, Code, Gamepad2, Zap, Star, Clock } from 'lucide-react';

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all'); 
  
  // Sample featured games data with enhanced information
  const featuredGames = [
    { 
      id: 1, 
      title: "Space Explorer", 
      creator: "AI Generated", 
      thumbnail: "/1.png",
      description: "Navigate through asteroid fields and collect power-ups in this thrilling space adventure",
      category: "action",
      rating: 4.8,
      playTime: "5-10 min",
      difficulty: "Medium"
    },
    { 
      id: 2, 
      title: "Jungle Adventure", 
      creator: "AI Generated", 
      thumbnail: "/2.png",
      description: "Platform game with jungle theme and collectible items for endless fun",
      category: "platform",
      rating: 4.6,
      playTime: "10-15 min",
      difficulty: "Easy"
    },
    { 
      id: 3, 
      title: "Racing Challenge", 
      creator: "AI Generated", 
      thumbnail: "/3.png",
      description: "Fast-paced racing game with multiple tracks and competitive gameplay",
      category: "racing",
      rating: 4.7,
      playTime: "3-8 min",
      difficulty: "Hard"
    },
    { 
      id: 4, 
      title: "Puzzle Master", 
      creator: "AI Generated", 
      thumbnail: "/4.png",
      description: "Mind-bending puzzles with increasing difficulty to test your skills",
      category: "puzzle",
      rating: 4.9,
      playTime: "15-30 min",
      difficulty: "Hard"
    },
    { 
      id: 5, 
      title: "Fantasy Quest", 
      creator: "AI Generated", 
      thumbnail: "/5.png",
      description: "RPG adventure with magic and mythical creatures in an enchanted world",
      category: "rpg",
      rating: 4.5,
      playTime: "20-45 min",
      difficulty: "Medium"
    },
    { 
      id: 6, 
      title: "Tower Defense", 
      creator: "AI Generated", 
      thumbnail: "/6.png",
      description: "Strategic tower placement to defend your base against enemy waves",
      category: "strategy",
      rating: 4.4,
      playTime: "10-25 min",
      difficulty: "Medium"
    }
  ];

  const categories = [
    { id: 'all', name: 'All Games', icon: Gamepad2 },
    { id: 'action', name: 'Action', icon: Zap },
    { id: 'puzzle', name: 'Puzzle', icon: Search },
    { id: 'platform', name: 'Platform', icon: Plus },
    { id: 'racing', name: 'Racing', icon: ChevronRight },
    { id: 'rpg', name: 'RPG', icon: Star },
    { id: 'strategy', name: 'Strategy', icon: Code }
  ];

  useEffect(() => {
    // Load saved games from localStorage
    const savedGames = localStorage.getItem("generatedGames");
    if (savedGames) {
      setGames(JSON.parse(savedGames));
    }
  }, []);

  const filteredGames = featuredGames.filter(game => {
    const matchesSearch = game.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         game.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = activeCategory === 'all' || game.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <div className="mb-8">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white to-purple-200">
              AI Game Generator
            </h1>
            <p className="text-xl md:text-2xl text-indigo-100 mb-8 max-w-3xl mx-auto">
              Turn your imagination into playable games in seconds. Powered by cutting-edge AI technology.
            </p>
          </div>
          
          <div className="flex flex-col md:flex-row gap-4 justify-center items-center mb-12">
            <div className="relative flex-1 max-w-lg">
              <input
                type="text"
                placeholder="Search amazing games..."
                className="w-full p-4 pl-12 rounded-2xl border-0 text-gray-900 placeholder-gray-500 shadow-xl focus:ring-4 focus:ring-purple-300 focus:outline-none transition-all duration-200"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <Search className="absolute left-4 top-4 text-gray-400" size={24} />
            </div>
            <button 
              onClick={() => window.location.href = "/create"} 
              className="px-8 py-4 bg-white text-purple-600 rounded-2xl font-bold text-lg flex items-center hover:bg-purple-50 transition-all duration-200 transform hover:scale-105 shadow-xl"
            >
              <Sparkles size={24} className="mr-3" />
              Create Game
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <div className="text-3xl font-bold mb-2">1000+</div>
              <div className="text-indigo-200">Games Created</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <div className="text-3xl font-bold mb-2">50K+</div>
              <div className="text-indigo-200">Players Worldwide</div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <div className="text-3xl font-bold mb-2">5 sec</div>
              <div className="text-indigo-200">Average Creation Time</div>
            </div>
          </div>
        </div>
      </section>

      <main className="container mx-auto px-4 py-12">
        {/* Category Filters */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-8">Browse by Category</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {categories.map((category) => {
              const IconComponent = category.icon;
              return (
                <button
                  key={category.id}
                  onClick={() => setActiveCategory(category.id)}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-2xl font-medium transition-all duration-200 transform hover:scale-105 ${
                    activeCategory === category.id
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg'
                      : 'bg-white text-gray-700 hover:bg-gray-50 shadow-md border border-gray-200'
                  }`}
                >
                  <IconComponent size={20} />
                  <span>{category.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Games Grid */}
        <section className="mb-16">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              {activeCategory === 'all' ? 'Featured AI Games' : `${categories.find(c => c.id === activeCategory)?.name} Games`}
            </h2>
            <p className="text-gray-600 text-lg">Discover amazing games created by AI in seconds</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredGames.map((game) => (
              <div
                onClick={() => window.location.href = "/game/" + game.id}
                key={game.id}
                className="group bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 cursor-pointer border border-gray-100"
              >
                <div className="relative overflow-hidden">
                  <img
                    src={game.thumbnail}
                    alt="Game Thumbnail"
                    className="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-300"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/400x300/6366f1/ffffff?text=' + encodeURIComponent(game.title);
                    }}
                  />
                  <div className="absolute top-4 left-4">
                    <span className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                      AI Generated
                    </span>
                  </div>
                  <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-full px-2 py-1 flex items-center space-x-1">
                    <Star className="text-yellow-500" size={14} fill="currentColor" />
                    <span className="text-sm font-medium text-gray-700">{game.rating}</span>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-bold text-xl text-gray-900 group-hover:text-indigo-600 transition-colors">
                      {game.title}
                    </h3>
                    <div className="flex items-center text-gray-500 text-sm ml-2">
                      <Clock size={14} className="mr-1" />
                      {game.playTime}
                    </div>
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-4 leading-relaxed">{game.description}</p>
                  
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        game.difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
                        game.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {game.difficulty}
                      </span>
                    </div>
                    <div className="text-indigo-600 group-hover:text-indigo-800 transition-colors font-medium">
                      Play Now →
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {filteredGames.length === 0 && (
            <div className="text-center py-16">
              <div className="mb-4">
                <Search className="mx-auto text-gray-400" size={48} />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No games found</h3>
              <p className="text-gray-600 mb-6">Try adjusting your search terms or category filter</p>
              <button 
                onClick={() => {setSearchQuery(''); setActiveCategory('all');}}
                className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors"
              >
                View All Games
              </button>
            </div>
          )}
        </section>

        {/* How It Works Section */}
        <section className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-3xl p-8 md:p-12 text-white mb-16">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-xl text-indigo-100">From idea to playable game in 3 simple steps</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="text-center">
              <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-6 mb-6 mx-auto w-fit">
                <Sparkles size={48} className="text-white" />
              </div>
              <div className="bg-white text-purple-700 rounded-full w-8 h-8 flex items-center justify-center font-bold text-lg mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-bold mb-2">Describe Your Game</h3>
              <p className="text-indigo-100">Tell us your game idea in plain English. Be as creative as you want!</p>
            </div>
            
            <div className="text-center">
              <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-6 mb-6 mx-auto w-fit">
                <Code size={48} className="text-white" />
              </div>
              <div className="bg-white text-purple-700 rounded-full w-8 h-8 flex items-center justify-center font-bold text-lg mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-bold mb-2">AI Enhancement</h3>
              <p className="text-indigo-100">Gemini AI refines your idea and Claude generates the game code.</p>
            </div>
            
            <div className="text-center">
              <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-6 mb-6 mx-auto w-fit">
                <Gamepad2 size={48} className="text-white" />
              </div>
              <div className="bg-white text-purple-700 rounded-full w-8 h-8 flex items-center justify-center font-bold text-lg mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-bold mb-2">Play & Share</h3>
              <p className="text-indigo-100">Your game is ready! Play it instantly and share with friends.</p>
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 text-center border border-white/20">
            <h3 className="text-3xl font-bold mb-4">Ready to Create Magic?</h3>
            <p className="text-xl mb-8 text-indigo-100">Join thousands of creators making amazing games with AI</p>
            <button
              className="px-12 py-4 bg-white text-purple-700 font-bold rounded-2xl hover:bg-purple-50 transition-all duration-200 text-lg transform hover:scale-105 shadow-xl"
              onClick={() => window.location.href = "/create"}
            >
              <Sparkles className="inline mr-3" size={24} />
              Start Creating Now
            </button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div className="md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-2">
                  <Sparkles size={24} className="text-white" />
                </div>
                <h2 className="text-2xl font-bold">AI Game Generator</h2>
              </div>
              <p className="text-gray-400 mb-4 max-w-md">
                Revolutionizing game creation with cutting-edge AI technology. 
                Turn your wildest game ideas into reality in seconds.
              </p>
              <div className="flex space-x-4">
                <div className="bg-gray-800 rounded-xl px-4 py-2">
                  <div className="text-sm text-gray-400">Powered by</div>
                  <div className="font-semibold">Gemini & Claude AI</div>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="/" className="hover:text-white transition-colors">Home</a></li>
                <li><a href="/create" className="hover:text-white transition-colors">Create Game</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Browse Games</a></li>
                <li><a href="#" className="hover:text-white transition-colors">How It Works</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Community</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Discord</a></li>
                <li><a href="#" className="hover:text-white transition-colors">GitHub</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Support</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm mb-4 md:mb-0">
              © 2024 AI Game Generator. Built with ❤️ and AI.
            </p>
            <div className="flex space-x-6 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="hover:text-white transition-colors">Contact Us</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}