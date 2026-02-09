import { useState, useRef } from "react";
import { Send, ArrowLeft, AlertCircle, Loader, Play, Download, Save, RefreshCw, Sparkles, Code, Gamepad2, Edit3, CheckCircle, Eye, EyeOff } from "lucide-react";

export default function Create() {
  const [prompt, setPrompt] = useState("");
  const [enhancedPrompt, setEnhancedPrompt] = useState("");
  const [gameHtml, setGameHtml] = useState("");
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1); // 1: Input, 2: Enhancing, 3: Generating, 4: Generated
  const [error, setError] = useState(null);
  const [feedbackPrompt, setFeedbackPrompt] = useState("");
  const [gameId, setGameId] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [isEditingPrompt, setIsEditingPrompt] = useState(false);
  const [editablePrompt, setEditablePrompt] = useState("");
  const gamePreviewRef = useRef(null);

  // Check if HTML is complete and valid
  const validateGameHtml = (html) => {
    if (!html) return false;
    
    // Check for basic HTML structure
    const hasHtmlTags = html.includes('<html') && html.includes('</html>');
    const hasPhaser = html.includes('phaser') || html.includes('Phaser');
    const notTruncated = !html.endsWith('...') && !html.includes('...');
    
    return hasHtmlTags && hasPhaser && notTruncated;
  };

  // Simple markdown to HTML converter for basic formatting
  const parseMarkdown = (markdown) => {
    if (!markdown) return '';
    return markdown
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/^\* (.*$)/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      .replace(/\n/g, '<br>');
  };

  // Show success message temporarily
  const showSuccess = (message) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  // Save edited prompt
  const saveEditedPrompt = () => {
    const updatedPrompt = {
      ...enhancedPrompt,
      description: editablePrompt
    };
    setEnhancedPrompt(updatedPrompt);
    setIsEditingPrompt(false);
    showSuccess("Changes saved successfully!");
  };

  // Cancel editing
  const cancelEditing = () => {
    setEditablePrompt(enhancedPrompt.description || enhancedPrompt);
    setIsEditingPrompt(false);
  };

  // Step 1: Send prompt to Gemini for enhancement
  const handlePromptSubmit = async () => {
    if (!prompt.trim()) {
      setError("Please enter a game idea first!");
      return;
    }

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
        setEditablePrompt(data.description || data);
        setCurrentStep(2); // Stay on step 2 to allow editing
        showSuccess("Prompt enhanced successfully! You can now edit it before generating the game.");
      } else {
        const errorData = await response.json();
        setError(errorData.error || "Failed to enhance prompt. Please try again.");
        setCurrentStep(1);
      }
    } catch (err) {
      setError("Network error. Please check if the backend is running.");
      console.error("Error:", err);
      setCurrentStep(1);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Generate game using Claude API
  const generateGame = async (promptToUse = enhancedPrompt || prompt) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:5000/generate_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          enhanced_prompt: promptToUse
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Generated game response:", data);
        setGameId(data.game_id);
        setTitle(data.title);
        
        // Fetch HTML separately
        const htmlResponse = await fetch(`http://127.0.0.1:5000${data.play_url}`);
        const html = await htmlResponse.text();
        setGameHtml(html);
        
        setCurrentStep(4);
        showSuccess("Game generated successfully! You can now play, download, or modify it.");
      }
    } catch (err) {
      setError("Network error. Please check if the backend is running.");
      console.error("Error:", err);
      setCurrentStep(2);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Update game based on feedback
  const handleFeedbackSubmit = async () => {
    if (!feedbackPrompt.trim()) {
      setError("Please enter feedback for game modification!");
      return;
    }

    setIsUpdating(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:5000/update_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_id: gameId,
          feedback: feedbackPrompt,
          current_html: gameHtml,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("Updated game:", data);
        
        // Fetch updated HTML
        const htmlResponse = await fetch(`http://127.0.0.1:5000/play_game/${gameId}`);
        const html = await htmlResponse.text();
        setGameHtml(html);
        
        setFeedbackPrompt("");
        showSuccess("Game updated successfully!");
        
        if (gamePreviewRef.current) {
          gamePreviewRef.current.src = gamePreviewRef.current.src;
        }
      }
    } catch (err) {
      setError("Network error. Please check if the backend is running.");
      console.error("Error:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  // Download game as HTML file
  const downloadGame = () => {
    if (!gameHtml) return;
    
    const blob = new Blob([gameHtml], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title || 'ai-game'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  // Reset to start over
  const resetGame = () => {
    setPrompt("");
    setEnhancedPrompt("");
    setGameHtml("");
    setTitle("");
    setFeedbackPrompt("");
    setGameId("");
    setCurrentStep(1);
    setError(null);
  };



  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">{/* Success Message */}
      {successMessage && (
        <div className="fixed top-4 right-4 z-50 flex items-center space-x-2 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <CheckCircle size={20} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <button
              onClick={() => window.location.href = "/"}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200"
            >
              <ArrowLeft size={20} className="mr-2" />
              <span className="font-medium">Back to Games</span>
            </button>
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                {Array.from({ length: 4 }, (_, i) => (
                  <div
                    key={i}
                    className={`w-3 h-3 rounded-full transition-all duration-300 ${
                      i + 1 <= currentStep
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-500'
                        : 'bg-gray-200'
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm font-medium text-gray-600">
                Step {currentStep} of 4
              </span>
            </div>
          </div>
        </div>
      </div>
      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-center">
            <div className="flex items-center space-x-4">
              {/* Step 1 */}
              <div className="flex items-center space-x-3">
                <div className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 ${
                  currentStep >= 1 
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 border-transparent text-white' 
                    : 'border-gray-300 text-gray-400'
                }`}>
                  <Edit3 size={20} />
                </div>
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-900">Describe</div>
                  <div className="text-xs text-gray-500">Your game idea</div>
                </div>
              </div>
              
              {/* Connector */}
              <div className={`w-16 h-0.5 transition-all duration-300 ${currentStep >= 2 ? 'bg-gradient-to-r from-indigo-500 to-purple-500' : 'bg-gray-300'}`} />
              
              {/* Step 2 */}
              <div className="flex items-center space-x-3">
                <div className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 ${
                  currentStep >= 2 
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 border-transparent text-white' 
                    : 'border-gray-300 text-gray-400'
                }`}>
                  <Sparkles size={20} />
                </div>
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-900">Enhance</div>
                  <div className="text-xs text-gray-500">AI refinement</div>
                </div>
              </div>
              
              {/* Connector */}
              <div className={`w-16 h-0.5 transition-all duration-300 ${currentStep >= 3 ? 'bg-gradient-to-r from-indigo-500 to-purple-500' : 'bg-gray-300'}`} />
              
              {/* Step 3 */}
              <div className="flex items-center space-x-3">
                <div className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 ${
                  currentStep >= 3 
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 border-transparent text-white' 
                    : 'border-gray-300 text-gray-400'
                }`}>
                  <Code size={20} />
                </div>
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-900">Generate</div>
                  <div className="text-xs text-gray-500">Create game</div>
                </div>
              </div>
              
              {/* Connector */}
              <div className={`w-16 h-0.5 transition-all duration-300 ${currentStep >= 4 ? 'bg-gradient-to-r from-indigo-500 to-purple-500' : 'bg-gray-300'}`} />
              
              {/* Step 4 */}
              <div className="flex items-center space-x-3">
                <div className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 ${
                  currentStep >= 4 
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 border-transparent text-white' 
                    : 'border-gray-300 text-gray-400'
                }`}>
                  <Gamepad2 size={20} />
                </div>
                <div className="text-center">
                  <div className="text-sm font-medium text-gray-900">Play</div>
                  <div className="text-xs text-gray-500">Enjoy & modify</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-8 mx-auto max-w-2xl">
            <div className="bg-red-50 border border-red-200 text-red-800 px-6 py-4 rounded-xl flex items-center shadow-sm">
              <div className="bg-red-100 rounded-full p-1 mr-3">
                <AlertCircle size={20} className="text-red-600" />
              </div>
              <div>
                <div className="font-medium">Error</div>
                <div className="text-sm opacity-90">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Step 1: Initial Prompt Input */}
        {currentStep === 1 && (
          <div className="mx-auto max-w-4xl">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
              <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-8 text-white">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="bg-white/20 rounded-full p-3">
                    <Edit3 size={28} />
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold">Describe Your Game</h2>
                    <p className="text-indigo-100 mt-1">Tell us about your dream game and watch AI bring it to life</p>
                  </div>
                </div>
              </div>
              
              <div className="p-8">
                <div className="grid md:grid-cols-2 gap-8">
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-3">
                      Game Title (Optional)
                    </label>
                    <input
                      type="text"
                      className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
                      placeholder="Enter a creative title for your game"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-3">
                      Character Count
                    </label>
                    <div className="flex items-center space-x-2 p-4">
                      <div className="text-2xl font-bold text-indigo-600">{prompt.length}</div>
                      <div className="text-gray-500">characters</div>
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                        prompt.length > 100 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {prompt.length > 100 ? 'Great detail!' : 'Add more details'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <label className="block text-sm font-semibold text-gray-900 mb-3">
                    Game Description
                  </label>
                  <textarea
                    className="w-full p-6 border border-gray-300 rounded-xl h-48 resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 text-gray-700"
                    placeholder="Example: Create a space shooter game where the player controls a spaceship and fights alien enemies. The game should have power-ups, multiple levels, and a boss at the end. Use a retro pixel art style with neon colors."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                  />
                  <div className="mt-3 text-sm text-gray-500">
                    💡 <strong>Tip:</strong> Include gameplay mechanics, visual style, difficulty, and any special features you want.
                  </div>
                </div>

                <div className="mt-8 flex justify-center">
                  <button
                    className={`px-12 py-4 rounded-xl font-semibold text-lg transition-all duration-200 transform ${
                      loading || !prompt.trim()
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:from-indigo-600 hover:to-purple-700 hover:scale-105 shadow-lg hover:shadow-xl'
                    }`}
                    onClick={handlePromptSubmit}
                    disabled={loading || !prompt.trim()}
                  >
                    {loading ? (
                      <div className="flex items-center">
                        <Loader size={20} className="mr-3 animate-spin" />
                        Enhancing with AI...
                      </div>
                    ) : (
                      <div className="flex items-center">
                        <Sparkles size={20} className="mr-3" />
                        Generate My Game
                      </div>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2 & 3: Enhanced Prompt Display and Generation */}
        {currentStep >= 2 && currentStep <= 3 && (
          <div className="mx-auto max-w-5xl">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
              <div className="bg-gradient-to-r from-emerald-500 to-teal-600 p-8 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="bg-white/20 rounded-full p-3">
                      {currentStep === 2 ? <Sparkles size={28} /> : <Code size={28} />}
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold">
                        {currentStep === 2 ? 'AI Enhancement Complete' : 'Generating Your Game'}
                      </h2>
                      <p className="text-emerald-100 mt-1">
                        {currentStep === 2 ? 'Review and edit your enhanced game concept' : 'Creating an amazing Phaser.js game with full physics'}
                      </p>
                    </div>
                  </div>
                  {currentStep === 3 && loading && (
                    <div className="flex items-center text-white bg-white/10 px-4 py-2 rounded-xl">
                      <Loader size={20} className="mr-2 animate-spin" />
                      <span className="font-medium">Generating game...</span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="p-8">
                {enhancedPrompt && (
                  <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-gray-900 flex items-center">
                        <Sparkles className="mr-2 text-emerald-500" size={20} />
                        Enhanced Game Concept
                      </h3>
                      <div className="flex items-center space-x-2">
                        {currentStep === 2 && (
                          <button
                            onClick={() => setIsEditingPrompt(!isEditingPrompt)}
                            className="flex items-center px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 transition-colors"
                          >
                            {isEditingPrompt ? <EyeOff size={16} className="mr-2" /> : <Edit3 size={16} className="mr-2" />}
                            {isEditingPrompt ? 'Preview' : 'Edit'}
                          </button>
                        )}
                      </div>
                    </div>
                    
                    <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl p-6">
                      {isEditingPrompt ? (
                        <div>
                          <textarea
                            value={editablePrompt}
                            onChange={(e) => setEditablePrompt(e.target.value)}
                            className="w-full h-96 p-4 border border-emerald-300 rounded-lg resize-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                            placeholder="Edit your enhanced game concept..."
                          />
                          <div className="flex justify-end space-x-3 mt-4">
                            <button
                              onClick={cancelEditing}
                              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={saveEditedPrompt}
                              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                            >
                              Save Changes
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div>
                          <div 
                            className="prose prose-emerald max-w-none text-gray-800 leading-relaxed"
                            dangerouslySetInnerHTML={{ __html: parseMarkdown(enhancedPrompt.description || enhancedPrompt) }}
                          />
                          
                          {enhancedPrompt.title && (
                            <div className="mt-6 pt-6 border-t border-emerald-200">
                              <div className="grid md:grid-cols-3 gap-6 text-sm">
                                <div className="bg-white p-4 rounded-lg">
                                  <span className="font-semibold text-emerald-700 block mb-1">Genre</span>
                                  <div className="text-gray-600">{enhancedPrompt.genre}</div>
                                </div>
                                <div className="bg-white p-4 rounded-lg">
                                  <span className="font-semibold text-emerald-700 block mb-1">Visual Style</span>
                                  <div className="text-gray-600">{enhancedPrompt.visual_style}</div>
                                </div>
                                <div className="bg-white p-4 rounded-lg">
                                  <span className="font-semibold text-emerald-700 block mb-1">Controls</span>
                                  <div className="text-gray-600">{enhancedPrompt.controls}</div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Loading indicator for game generation */}
                {currentStep === 3 && loading && (
                  <div className="mb-8 text-center">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-8">
                      <div className="flex flex-col items-center">
                        <div className="relative mb-6">
                          <div className="w-20 h-20 border-4 border-blue-200 rounded-full animate-pulse"></div>
                          <div className="absolute inset-0 w-20 h-20 border-4 border-t-blue-600 rounded-full animate-spin"></div>
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2">Creating Your Game</h3>
                        <p className="text-gray-600 mb-4">AI is generating a fully functional Phaser.js game with proper physics and mechanics</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                            Enhanced with Claude AI
                          </div>
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                            Full Physics Engine
                          </div>
                          <div className="flex items-center">
                            <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                            Interactive Gameplay
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <button
                    className="px-6 py-3 bg-gray-500 text-white rounded-xl hover:bg-gray-600 transition-colors duration-200 flex items-center disabled:opacity-50"
                    onClick={resetGame}
                    disabled={loading}
                  >
                    <ArrowLeft size={18} className="mr-2" />
                    Start Over
                  </button>
                  
                  {enhancedPrompt && !loading && currentStep === 2 && !isEditingPrompt && (
                    <button
                      className="px-8 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl hover:from-emerald-600 hover:to-teal-700 transition-all duration-200 flex items-center shadow-lg"
                      onClick={() => {
                        setCurrentStep(3);
                        generateGame();
                      }}
                    >
                      <Code size={18} className="mr-2" />
                      Generate Game Code
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Generated Game Display */}
        {currentStep === 4 && gameHtml && (
          <div className="mx-auto max-w-6xl">
            {/* Game Header */}
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden mb-8">
              <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-8 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="bg-white/20 rounded-full p-4">
                      <Gamepad2 size={32} />
                    </div>
                    <div>
                      <h2 className="text-4xl font-bold">{title || "Your AI Game"}</h2>
                      <p className="text-purple-100 mt-1">Game generated successfully! Ready to play</p>
                    </div>
                  </div>
                  <div className="flex space-x-3">
                    <button
                      className="px-6 py-3 bg-white/20 hover:bg-white/30 text-white rounded-xl transition-colors duration-200 flex items-center backdrop-blur-sm"
                      onClick={downloadGame}
                    >
                      <Download size={20} className="mr-2" />
                      Download HTML
                    </button>
                    <button
                      className="px-6 py-3 bg-white/20 hover:bg-white/30 text-white rounded-xl transition-colors duration-200 flex items-center backdrop-blur-sm"
                      onClick={resetGame}
                    >
                      <RefreshCw size={20} className="mr-2" />
                      Create New
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Game Preview */}
              <div className="p-8">
                <div className="bg-gray-900 rounded-xl overflow-hidden shadow-2xl">
                  <div className="bg-gray-800 px-4 py-2 flex items-center space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <div className="ml-4 text-gray-400 text-sm">Game Preview</div>
                  </div>
                  <iframe
                    ref={gamePreviewRef}
                    srcDoc={gameHtml}
                    title="Game Preview"
                    className="w-full h-[500px] border-0 bg-white"
                    sandbox="allow-scripts allow-same-origin"
                  />
                </div>
              </div>
            </div>

            {/* Game Modification Panel */}
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
                <div className="flex items-center space-x-3">
                  <div className="bg-white/20 rounded-full p-3">
                    <Edit3 size={24} />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold">Modify Your Game</h3>
                    <p className="text-blue-100">Tell us what changes you'd like to make</p>
                  </div>
                </div>
              </div>
              
              <div className="p-8">
                <div className="grid md:grid-cols-3 gap-6 mb-6">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-900 mb-3">
                      Modification Request
                    </label>
                    <textarea
                      className="w-full p-4 border border-gray-300 rounded-xl h-32 resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                      placeholder="Example: Make the player move faster, add more enemies, change the background color to blue, add sound effects..."
                      value={feedbackPrompt}
                      onChange={(e) => setFeedbackPrompt(e.target.value)}
                    />
                  </div>
                  
                  <div className="flex flex-col justify-end">
                    <div className="bg-blue-50 rounded-xl p-4 mb-4">
                      <div className="text-sm text-blue-800 font-medium mb-2">💡 Ideas for modifications:</div>
                      <ul className="text-xs text-blue-600 space-y-1">
                        <li>• Change colors or graphics</li>
                        <li>• Adjust game speed or difficulty</li>
                        <li>• Add new features or mechanics</li>
                        <li>• Modify controls or UI elements</li>
                      </ul>
                    </div>
                    
                    <button
                      className={`w-full py-4 rounded-xl font-semibold transition-all duration-200 ${
                        isUpdating || !feedbackPrompt.trim()
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700 shadow-lg hover:shadow-xl'
                      }`}
                      onClick={handleFeedbackSubmit}
                      disabled={isUpdating || !feedbackPrompt.trim()}
                    >
                      {isUpdating ? (
                        <div className="flex items-center justify-center">
                          <Loader size={20} className="mr-2 animate-spin" />
                          Updating Game...
                        </div>
                      ) : (
                        <div className="flex items-center justify-center">
                          <RefreshCw size={20} className="mr-2" />
                          Apply Changes
                        </div>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-6">
        <div className="container mx-auto px-4 text-center">
          <h3 className="text-lg font-semibold mb-2">AI Game Generator</h3>
          <p className="text-gray-300">Create amazing games with the power of AI • Powered by Gemini & Claude</p>
        </div>
      </footer>
    </div>
  );
}