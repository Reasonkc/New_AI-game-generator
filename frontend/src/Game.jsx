import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router';
import { ArrowLeft, Play, Repeat, Loader, Download, Share2, RefreshCw, Maximize, Code, Gamepad2, Star, Clock } from 'lucide-react';

// Generate a simple sample game HTML for demo purposes
const generateSampleGameHTML = (title) => {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js"></script>
</head>
<body style="margin: 0; background: #2c3e50; display: flex; justify-content: center; align-items: center; min-height: 100vh;">
    <script>
        class GameScene extends Phaser.Scene {
            constructor() {
                super({ key: 'GameScene' });
            }

            create() {
                this.add.text(400, 300, '${title}', {
                    fontSize: '32px',
                    fill: '#ffffff',
                    align: 'center'
                }).setOrigin(0.5);
                
                this.add.text(400, 350, 'Demo Game - Click to interact!', {
                    fontSize: '18px',
                    fill: '#ecf0f1',
                    align: 'center'
                }).setOrigin(0.5);

                // Add simple interactive element
                const rect = this.add.rectangle(400, 400, 100, 50, 0x3498db);
                rect.setInteractive();
                rect.on('pointerdown', () => {
                    rect.setFillStyle(0xe74c3c);
                    this.time.delayedCall(200, () => rect.setFillStyle(0x3498db));
                });
            }
        }

        const config = {
            type: Phaser.AUTO,
            width: 800,
            height: 600,
            scene: GameScene,
            backgroundColor: '#2c3e50'
        };

        const game = new Phaser.Game(config);
    </script>
</body>
</html>`;
};

export default function GamePage() {
  const { gameId } = useParams();
  const [game, setGame] = useState(null);
  const [gameHtml, setGameHtml] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [gameStats, setGameStats] = useState({ rating: 4.5, playCount: 0 });
  const gameIframeRef = useRef(null);
  const containerRef = useRef(null);

  // Sample game data with enhanced info
  const sampleGameData = {
    '1': { title: "Space Explorer", category: "Action", rating: 4.8, playTime: "5-10 min", difficulty: "Medium" },
    '2': { title: "Jungle Adventure", category: "Platform", rating: 4.6, playTime: "10-15 min", difficulty: "Easy" },
    '3': { title: "Racing Challenge", category: "Racing", rating: 4.7, playTime: "3-8 min", difficulty: "Hard" },
    '4': { title: "Puzzle Master", category: "Puzzle", rating: 4.9, playTime: "15-30 min", difficulty: "Hard" },
    '5': { title: "Fantasy Quest", category: "RPG", rating: 4.5, playTime: "20-45 min", difficulty: "Medium" },
    '6': { title: "Tower Defense", category: "Strategy", rating: 4.4, playTime: "10-25 min", difficulty: "Medium" }
  };

  useEffect(() => {
    const fetchGame = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Try to get game from backend first
        const response = await fetch(`http://127.0.0.1:5000/get_game/${gameId}`);
        if (response.ok) {
          const data = await response.json();
          setGame(data.metadata);
          setGameHtml(data.html);
        } else {
          // Fallback to sample games
          const sampleInfo = sampleGameData[gameId];
          if (sampleInfo) {
            setGame(sampleInfo);
            setGameHtml(generateSampleGameHTML(sampleInfo.title));
            setGameStats({ rating: sampleInfo.rating, playCount: Math.floor(Math.random() * 1000) + 100 });
          } else {
            throw new Error("Game not found");
          }
        }
        setLoading(false);
        
      } catch (err) {
        setError("Failed to load game. Please try again later.");
        setLoading(false);
      }
    };

    fetchGame();
  }, [gameId]);

  // Toggle fullscreen mode
  const toggleFullscreen = () => {
    if (!isFullscreen && containerRef.current) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
      setIsFullscreen(true);
    } else if (document.exitFullscreen) {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Download game HTML
  const downloadGame = () => {
    if (!gameHtml) return;
    
    const blob = new Blob([gameHtml], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${game?.title || 'game'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  // Share game
  const shareGame = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: game?.title || 'AI Generated Game',
          text: `Check out this amazing AI-generated game: ${game?.title}!`,
          url: window.location.href,
        });
      } catch (err) {
        console.log('Error sharing:', err);
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      alert('Game link copied to clipboard!');
    }
  };

  const handleRemix = () => {
    alert(`Remixing Game #${gameId}... This would take you to the create page with this game as a template.`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="container mx-auto px-4 py-6">
          <button
            onClick={() => window.location.href = "/"}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200"
          >
            <ArrowLeft size={20} className="mr-2" />
            <span className="font-medium">Back to Games</span>
          </button>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
              <Loader size={48} className="text-indigo-600 animate-spin mb-6 mx-auto" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Loading Game</h3>
              <p className="text-gray-600">Please wait while we prepare your gaming experience...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="bg-white rounded-2xl shadow-xl p-12 text-center max-w-md">
              <div className="bg-red-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-6">
                <ArrowLeft className="text-red-600" size={24} />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Game Not Found</h3>
              <p className="text-gray-600 mb-6">{error}</p>
              <button
                onClick={() => window.location.href = "/"}
                className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors"
              >
                Browse Games
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Game Header */}
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden mb-8">
              <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-8 text-white">
                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center">
                  <div className="mb-6 lg:mb-0">
                    <h1 className="text-4xl font-bold mb-3">{game?.title}</h1>
                    <div className="flex items-center space-x-4 text-indigo-100">
                      <span className="flex items-center">
                        <Star className="mr-1" size={16} fill="currentColor" />
                        {gameStats.rating}
                      </span>
                      <span className="flex items-center">
                        <Play className="mr-1" size={16} />
                        {gameStats.playCount} plays
                      </span>
                      <span className="flex items-center">
                        <Clock className="mr-1" size={16} />
                        {game?.playTime}
                      </span>
                      {game?.difficulty && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          game.difficulty === 'Easy' ? 'bg-green-500/20 text-green-100' :
                          game.difficulty === 'Medium' ? 'bg-yellow-500/20 text-yellow-100' :
                          'bg-red-500/20 text-red-100'
                        }`}>
                          {game.difficulty}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-3">
                    <button 
                      className="px-6 py-3 bg-white/20 hover:bg-white/30 text-white rounded-xl transition-colors duration-200 flex items-center backdrop-blur-sm"
                      onClick={shareGame}
                    >
                      <Share2 size={18} className="mr-2" />
                      Share
                    </button>
                    <button 
                      className="px-6 py-3 bg-white/20 hover:bg-white/30 text-white rounded-xl transition-colors duration-200 flex items-center backdrop-blur-sm"
                      onClick={downloadGame}
                    >
                      <Download size={18} className="mr-2" />
                      Download
                    </button>
                    <button 
                      className="px-6 py-3 bg-white/20 hover:bg-white/30 text-white rounded-xl transition-colors duration-200 flex items-center backdrop-blur-sm"
                      onClick={handleRemix}
                    >
                      <RefreshCw size={18} className="mr-2" />
                      Remix
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Game Player */}
              <div ref={containerRef} className="relative">
                <div className="bg-gray-900 relative">
                  {/* Game Controls Bar */}
                  <div className="bg-gray-800 px-6 py-3 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex space-x-2">
                        <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                        <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      </div>
                      <span className="text-gray-300 text-sm">Playing: {game?.title}</span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={toggleFullscreen}
                        className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-gray-700"
                        title="Fullscreen"
                      >
                        <Maximize size={16} />
                      </button>
                    </div>
                  </div>
                  
                  {/* Game Iframe */}
                  {gameHtml && (
                    <iframe
                      ref={gameIframeRef}
                      srcDoc={gameHtml}
                      title={game?.title}
                      className="w-full h-[600px] border-0 bg-white"
                      sandbox="allow-scripts allow-same-origin allow-modals"
                      allow="autoplay; fullscreen"
                    />
                  )}
                  
                  {/* Game Instructions */}
                  <div className="bg-gray-800 px-6 py-3 text-center">
                    <p className="text-gray-300 text-sm">
                      🎮 Click inside the game area to activate controls • Use arrow keys or WASD to move
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Game Info Grid */}
            <div className="grid lg:grid-cols-3 gap-8 mb-8">
              {/* Game Details */}
              <div className="lg:col-span-2 bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  <Code className="mr-3 text-indigo-600" size={24} />
                  Game Details
                </h2>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold text-gray-700 mb-1">Category</h3>
                      <span className="inline-block bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm font-medium">
                        {game?.category || 'Action'}
                      </span>
                    </div>
                    
                    <div>
                      <h3 className="font-semibold text-gray-700 mb-1">Created By</h3>
                      <p className="text-gray-600">AI Generator</p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold text-gray-700 mb-1">Game ID</h3>
                      <p className="text-gray-600 font-mono">#{gameId}</p>
                    </div>
                    
                    <div>
                      <h3 className="font-semibold text-gray-700 mb-1">Technology</h3>
                      <p className="text-gray-600">Phaser.js • HTML5</p>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Quick Actions */}
              <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                  <Gamepad2 className="mr-2 text-purple-600" size={20} />
                  Quick Actions
                </h2>
                
                <div className="space-y-4">
                  <button
                    onClick={() => window.location.href = "/create"}
                    className="w-full px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 flex items-center justify-center"
                  >
                    <Code size={18} className="mr-2" />
                    Create Similar Game
                  </button>
                  
                  <button
                    onClick={downloadGame}
                    className="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors duration-200 flex items-center justify-center"
                  >
                    <Download size={18} className="mr-2" />
                    Download Source
                  </button>
                  
                  <button
                    onClick={shareGame}
                    className="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors duration-200 flex items-center justify-center"
                  >
                    <Share2 size={18} className="mr-2" />
                    Share Game
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}