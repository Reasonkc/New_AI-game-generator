import { useState } from "react";
import { Send, ArrowLeft, AlertCircle, Loader, Play, Download, Edit3, Save } from "lucide-react";

export default function Create() {
  const [prompt, setPrompt] = useState("");
  const [enhancedPrompt, setEnhancedPrompt] = useState(null);
  const [gameHtml, setGameHtml] = useState("");
  const [gameId, setGameId] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1); // 1: Input, 2: Enhanced, 3: Generated
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState("");
  const [showFeedback, setShowFeedback] = useState(false);

  // Step 1: Send prompt to Gemini for enhancement
  const handlePromptSubmit = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);
    setCurrentStep(2);

    try {
      const response = await fetch("http://127.0.0.1:5000/enhance_prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt }),
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("Enhanced prompt:", data);
        setEnhancedPrompt(data);
        setLoading(false);
      } else {
        const errorText = await response.text();
        console.error("Backend error:", errorText);
        setError("Failed to enhance prompt. Please try again.");
        setLoading(false);
      }
    } catch (err) {
      setError("Failed to enhance prompt. Please try again.");
      console.error("Error:", err);
      setLoading(false);
    }
  };

  // Step 2: Generate game using Claude
  const handleGenerateGame = async () => {
    if (!enhancedPrompt) return;

    setLoading(true);
    setError(null);
    setCurrentStep(3);

    try {
      const response = await fetch("http://127.0.0.1:5000/generate_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enhanced_prompt: enhancedPrompt }),
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("Generated game:", data);
        setGameId(data.game_id);
        
        // Fetch HTML separately
        const htmlResponse = await fetch(`http://127.0.0.1:5000${data.play_url}`);
        const html = await htmlResponse.text();
        setGameHtml(html);
        
        setLoading(false);
      }
    } catch (err) {
      setError("Failed to generate game. Please try again.");
      console.error("Error:", err);
      setLoading(false);
    }
  };

  // Update game based on feedback
  const handleFeedbackSubmit = async () => {
    if (!feedback.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:5000/update_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          feedback: feedback,
          current_html: gameHtml,
          game_id: gameId,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("Updated game:", data);
        
        // Fetch updated HTML
        const htmlResponse = await fetch(`http://127.0.0.1:5000/play_game/${gameId}`);
        const html = await htmlResponse.text();
        setGameHtml(html);
        
        setFeedback("");
        setShowFeedback(false);
        setLoading(false);
      }
    } catch (err) {
      setError("Failed to update game. Please try again.");
      console.error("Error:", err);
      setLoading(false);
    }
  };

  const downloadGame = () => {
    if (!gameHtml) return;
    
    const blob = new Blob([gameHtml], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${enhancedPrompt?.title || "game"}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const playGame = () => {
    if (!gameId) return;
    window.open(`http://127.0.0.1:5000/play_game/${gameId}`, '_blank');
  };

  const resetToStart = () => {
    setPrompt("");
    setEnhancedPrompt(null);
    setGameHtml("");
    setGameId("");
    setCurrentStep(1);
    setError(null);
    setFeedback("");
    setShowFeedback(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-4">
              AI Game Generator
            </h1>
            <p className="text-xl text-blue-200">
              Create games with AI - from prompt to playable PhaserJS game
            </p>
          </div>

          {/* Progress indicator */}
          <div className="flex items-center justify-center mb-8">
            <div className="flex items-center space-x-4">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                currentStep >= 1 ? "bg-blue-500 text-white" : "bg-gray-600 text-gray-300"
              }`}>
                1
              </div>
              <div className={`h-1 w-16 ${currentStep >= 2 ? "bg-blue-500" : "bg-gray-600"}`}></div>
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                currentStep >= 2 ? "bg-blue-500 text-white" : "bg-gray-600 text-gray-300"
              }`}>
                2
              </div>
              <div className={`h-1 w-16 ${currentStep >= 3 ? "bg-blue-500" : "bg-gray-600"}`}></div>
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                currentStep >= 3 ? "bg-green-500 text-white" : "bg-gray-600 text-gray-300"
              }`}>
                3
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-6 flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-3" />
              <span className="text-red-200">{error}</span>
            </div>
          )}

          {/* Step 1: Initial Prompt */}
          {currentStep === 1 && (
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
              <h2 className="text-2xl font-semibold text-white mb-4">
                1. Describe Your Game Idea
              </h2>
              <div className="space-y-4">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe the game you want to create... (e.g., 'A space shooter where you dodge asteroids and collect power-ups')"
                  className="w-full h-32 px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 resize-none"
                />
                <button
                  onClick={handlePromptSubmit}
                  disabled={!prompt.trim() || loading}
                  className="flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg text-white font-medium transition-colors"
                >
                  {loading ? (
                    <Loader className="w-5 h-5 mr-2 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5 mr-2" />
                  )}
                  Enhance Prompt
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Enhanced Prompt Review */}
          {currentStep === 2 && enhancedPrompt && !loading && (
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
              <h2 className="text-2xl font-semibold text-white mb-4">
                2. Enhanced Game Concept
              </h2>
              <div className="space-y-4 mb-6">
                <div>
                  <h3 className="text-lg font-medium text-blue-300 mb-2">Title</h3>
                  <p className="text-white">{enhancedPrompt.title}</p>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-blue-300 mb-2">Description</h3>
                  <p className="text-gray-300">{enhancedPrompt.description}</p>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-blue-300 mb-2">Genre</h3>
                  <p className="text-white">{enhancedPrompt.genre}</p>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-blue-300 mb-2">Game Mechanics</h3>
                  <ul className="text-gray-300 list-disc list-inside">
                    {enhancedPrompt.game_mechanics?.map((mechanic, index) => (
                      <li key={index}>{mechanic}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-blue-300 mb-2">Controls</h3>
                  <p className="text-gray-300">{enhancedPrompt.controls}</p>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-blue-300 mb-2">Objectives</h3>
                  <p className="text-gray-300">{enhancedPrompt.objectives}</p>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="flex items-center px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white font-medium transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </button>
                <button
                  onClick={handleGenerateGame}
                  disabled={loading}
                  className="flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg text-white font-medium transition-colors"
                >
                  {loading ? (
                    <Loader className="w-5 h-5 mr-2 animate-spin" />
                  ) : (
                    <Play className="w-5 h-5 mr-2" />
                  )}
                  Generate Game
                </button>
              </div>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-8 border border-gray-700 text-center">
              <Loader className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
              <p className="text-white">
                {currentStep === 2 ? "Enhancing your prompt..." : "Generating your game..."}
              </p>
            </div>
          )}

          {/* Step 3: Generated Game */}
          {currentStep === 3 && gameHtml && !loading && (
            <div className="space-y-6">
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
                <h2 className="text-2xl font-semibold text-white mb-4">
                  3. Your Game is Ready!
                </h2>
                <div className="flex gap-3 mb-6">
                  <button
                    onClick={playGame}
                    className="flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg text-white font-medium transition-colors"
                  >
                    <Play className="w-5 h-5 mr-2" />
                    Play Game
                  </button>
                  <button
                    onClick={downloadGame}
                    className="flex items-center px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Download
                  </button>
                  <button
                    onClick={() => setShowFeedback(!showFeedback)}
                    className="flex items-center px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg text-white font-medium transition-colors"
                  >
                    <Edit3 className="w-5 h-5 mr-2" />
                    Improve
                  </button>
                  <button
                    onClick={resetToStart}
                    className="flex items-center px-4 py-3 bg-gray-600 hover:bg-gray-700 rounded-lg text-white font-medium transition-colors"
                  >
                    Create New Game
                  </button>
                </div>

                {showFeedback && (
                  <div className="border-t border-gray-600 pt-6">
                    <h3 className="text-lg font-medium text-white mb-3">Improve Your Game</h3>
                    <div className="space-y-3">
                      <textarea
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        placeholder="What would you like to change or improve? (e.g., 'Make it faster', 'Add more enemies', 'Change the colors')"
                        className="w-full h-24 px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 resize-none"
                      />
                      <div className="flex gap-3">
                        <button
                          onClick={handleFeedbackSubmit}
                          disabled={!feedback.trim() || loading}
                          className="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-lg text-white font-medium transition-colors"
                        >
                          {loading ? (
                            <Loader className="w-4 h-4 mr-2 animate-spin" />
                          ) : (
                            <Save className="w-4 h-4 mr-2" />
                          )}
                          Update Game
                        </button>
                        <button
                          onClick={() => setShowFeedback(false)}
                          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white font-medium transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Game preview */}
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
                <h3 className="text-lg font-medium text-white mb-4">Game Preview</h3>
                <div className="bg-white rounded-lg overflow-hidden">
                  <iframe
                    srcDoc={gameHtml}
                    className="w-full h-96"
                    title="Game Preview"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}