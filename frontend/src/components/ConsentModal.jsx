import { useState, useEffect } from "react";
import { Shield, ExternalLink } from "lucide-react";

const CONSENT_KEY = "ai_game_gen_consent";

export function hasConsent() {
  return localStorage.getItem(CONSENT_KEY) === "true";
}

export default function ConsentModal({ onAccept }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!hasConsent()) setVisible(true);
  }, []);

  const handleAccept = () => {
    localStorage.setItem(CONSENT_KEY, "true");
    setVisible(false);
    if (onAccept) onAccept();
  };

  const handleDecline = () => {
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg mx-4 overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-6 text-white">
          <div className="flex items-center space-x-3">
            <Shield size={28} />
            <h2 className="text-xl font-bold">Data Privacy Notice</h2>
          </div>
        </div>

        <div className="p-6">
          <p className="text-gray-700 mb-4">
            Before you create a game, please be aware of how your data is processed:
          </p>

          <div className="bg-gray-50 rounded-xl p-4 mb-4 space-y-3 text-sm text-gray-600">
            <div className="flex items-start space-x-2">
              <span className="text-indigo-500 font-bold mt-0.5">1.</span>
              <p>
                Your game description is sent to{" "}
                <strong>Google Gemini API</strong> for prompt enhancement.
              </p>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-indigo-500 font-bold mt-0.5">2.</span>
              <p>
                The enhanced prompt is sent to{" "}
                <strong>Anthropic Claude API</strong> for game code generation.
              </p>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-indigo-500 font-bold mt-0.5">3.</span>
              <p>
                Generated games are stored on our server with a unique ID.
                No personal information is collected.
              </p>
            </div>
          </div>

          <p className="text-xs text-gray-500 mb-6">
            By clicking "I Agree," you consent to your prompts being processed
            by third-party AI services.{" "}
            <a href="/privacy" className="text-indigo-600 hover:underline inline-flex items-center">
              Read our full Privacy Policy <ExternalLink size={10} className="ml-1" />
            </a>
          </p>

          <div className="flex space-x-3">
            <button
              onClick={handleDecline}
              className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-xl hover:bg-gray-300 transition-colors font-medium"
            >
              Decline
            </button>
            <button
              onClick={handleAccept}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all font-medium"
            >
              I Agree
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
