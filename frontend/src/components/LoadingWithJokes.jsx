import { useState, useEffect } from "react";
import { Sparkles, Loader } from "lucide-react";

const JOKES = [
  "Why did the game developer go broke? Because he used all his cache.",
  "Why don't programmers like nature? It has too many bugs.",
  "Why did the AI go to therapy? It had too many unresolved promises.",
  "What's a pirate's favorite programming language? R!",
  "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
  "How many programmers does it take to change a light bulb? None — it's a hardware problem.",
  "Why did the coder quit his job? Because he didn't get arrays.",
  "What do you call 8 hobbits? A hobbyte.",
  "A SQL query walks into a bar, walks up to two tables and asks: Can I JOIN you?",
  "Why do Java developers wear glasses? Because they don't C#.",
  "Why did the developer go broke in Vegas? He lost all his bits on binary.",
  "How do you comfort a JavaScript bug? You console it.",
  "Why don't game devs go outside? The graphics are too realistic.",
  "What's a game developer's favorite snack? Microchips.",
  "Why did the pixel break up with the sprite? Too many dimensions.",
  "AI is thinking... probably about whether pineapple belongs on pizza.",
  "Fun fact: This game will have exactly zero bugs. (Gemini said so, not me.)",
  "Loading creativity... please stand by. Genius cannot be rushed.",
  "The AI is currently debating whether to add a dragon. Fingers crossed.",
  "Did you know? The first video game was created in 1958 — it was tennis.",
];

const STAGES = [
  "Reading your game idea...",
  "Brainstorming mechanics...",
  "Designing visual style...",
  "Crafting the perfect controls...",
  "Polishing the game concept...",
  "Almost there...",
];

export default function LoadingWithJokes({ engine = "phaser" }) {
  const [jokeIndex, setJokeIndex] = useState(() => Math.floor(Math.random() * JOKES.length));
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const jokeTimer = setInterval(() => {
      setJokeIndex((i) => (i + 1) % JOKES.length);
    }, 4500);
    const stageTimer = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, STAGES.length - 1));
    }, 3000);
    return () => {
      clearInterval(jokeTimer);
      clearInterval(stageTimer);
    };
  }, []);

  return (
    <div className="py-10 px-4">
      <div className="flex flex-col items-center text-center max-w-2xl mx-auto">
        {/* Animated spinner */}
        <div className="relative mb-6">
          <div className="w-24 h-24 border-4 border-emerald-100 rounded-full"></div>
          <div className="absolute inset-0 w-24 h-24 border-4 border-t-emerald-500 border-r-emerald-500 rounded-full animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Sparkles className="text-emerald-500 animate-pulse" size={28} />
          </div>
        </div>

        {/* Current stage */}
        <div className="flex items-center space-x-2 mb-3">
          <Loader size={16} className="text-emerald-500 animate-spin" />
          <p className="text-lg font-semibold text-gray-800">{STAGES[stageIndex]}</p>
        </div>

        <p className="text-sm text-gray-500 mb-8">
          Estimated time: 5–15 seconds · Engine: {engine === "threejs" ? "3D Three.js" : "2D PhaserJS"}
        </p>

        {/* Joke card */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-2xl p-6 w-full transition-all duration-500">
          <div className="flex items-center justify-center mb-3">
            <div className="bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full p-2">
              <Sparkles size={16} className="text-white" />
            </div>
            <span className="ml-2 text-xs font-semibold text-indigo-600 uppercase tracking-wider">
              While you wait
            </span>
          </div>
          <p
            key={jokeIndex}
            className="text-gray-700 italic animate-fade-in text-base leading-relaxed"
          >
            "{JOKES[jokeIndex]}"
          </p>
        </div>

        {/* Progress dots */}
        <div className="flex items-center space-x-2 mt-6">
          {STAGES.map((_, i) => (
            <div
              key={i}
              className={`h-2 rounded-full transition-all duration-500 ${
                i <= stageIndex
                  ? "bg-gradient-to-r from-emerald-400 to-teal-500 w-8"
                  : "bg-gray-200 w-2"
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
