import { ArrowLeft } from "lucide-react";

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="container mx-auto px-4 py-6">
          <button
            onClick={() => window.location.href = "/"}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={20} className="mr-2" />
            <span className="font-medium">Back to Home</span>
          </button>
        </div>
      </div>

      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Privacy Policy</h1>

        <div className="prose prose-indigo max-w-none text-gray-700 space-y-6">
          <section>
            <h2 className="text-2xl font-semibold text-gray-900">1. Data We Collect</h2>
            <p>
              When you use the AI Game Generator, we process the following data:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Game descriptions and titles you provide</li>
              <li>Feedback you submit for game modifications</li>
              <li>Generated game files (HTML) stored with a unique identifier</li>
            </ul>
            <p>We do not collect personal information, email addresses, or account data.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900">2. Third-Party AI Services</h2>
            <p>Your game descriptions are processed by two external AI services:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong>Google Gemini API</strong> — used to enhance and refine your game
                idea into a structured concept. Subject to{" "}
                <a href="https://policies.google.com/privacy" className="text-indigo-600 hover:underline" target="_blank" rel="noopener noreferrer">
                  Google's Privacy Policy
                </a>.
              </li>
              <li>
                <strong>Anthropic Claude API</strong> — used to generate the game code from
                the enhanced prompt. Subject to{" "}
                <a href="https://www.anthropic.com/privacy" className="text-indigo-600 hover:underline" target="_blank" rel="noopener noreferrer">
                  Anthropic's Privacy Policy
                </a>.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900">3. Data Storage</h2>
            <p>
              Generated games are stored on our server with a UUID identifier. Game
              metadata (title, genre, creation date) is stored alongside the game file.
              No data is shared with third parties beyond the AI services listed above.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900">4. Your Consent</h2>
            <p>
              By using the AI Game Generator, you consent to your game descriptions being
              sent to Google Gemini and Anthropic Claude for processing. You may withdraw
              consent at any time by clearing your browser's localStorage.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-gray-900">5. Contact</h2>
            <p>
              For questions about this privacy policy, please open an issue on our{" "}
              <a href="https://github.com/Reasonkc/New_AI-game-generator" className="text-indigo-600 hover:underline" target="_blank" rel="noopener noreferrer">
                GitHub repository
              </a>.
            </p>
          </section>
        </div>
      </div>

      <footer className="bg-gray-800 text-white py-6 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-300">AI Game Generator — Powered by Gemini & Claude</p>
        </div>
      </footer>
    </div>
  );
}
