# 🎮 AI Game Generator

An intelligent game creation platform that uses AI to transform natural language descriptions into fully playable HTML5 games. The system leverages Google's Gemini API for prompt enhancement and Anthropic's Claude API for game code generation using PhaserJS.

---
## 📋 Project Management

Track progress on technical debt and feature development:
- [**Project Board**](https://github.com/Reasonkc/New_AI-game-generator/projects/1) - Live backlog and status

## 🚀 Features

- 🎨 **AI-Powered Prompt Enhancement**: Uses Gemini AI to refine and enhance user game descriptions
- 🕹️ **Automatic Game Generation**: Creates complete HTML5 games using Claude AI and PhaserJS framework
- ♻️ **Iterative Game Improvement**: Update and modify games based on user feedback
- 💾 **Local Storage**: Save and organize generated games locally with unique identifiers  
- 📸 **Game Screenshots**: Automatically capture game previews for easy browsing
- 🎯 **RESTful API**: Clean, well-documented API endpoints for seamless frontend integration

---

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework for API server
- **Google Gemini API** - Natural language prompt enhancement
- **Anthropic Claude API** - Game code generation
- **PhaserJS** - HTML5 game development framework
- **Python-dotenv** - Environment variable management

### Frontend  
- **React** - Modern UI framework
- **Vite** - Fast development build tool
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library

---

## 📦 Installation & Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file and add your API keys:
# GEMINI_API_KEY=your_gemini_api_key_here
# CLAUDE_API_KEY=your_claude_api_key_here
```

5. Run the backend server:
```bash
python backend.py
```

The API will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

---

## 🔐 API Keys Setup

### Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GEMINI_API_KEY`

### Claude API Key  
1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key
3. Add it to your `.env` file as `CLAUDE_API_KEY`

---

## 📡 API Endpoints

### `POST /enhance-prompt`
Enhances user prompt using Gemini AI for better game generation.

**Request:**
```json
{
  "prompt": "A platformer game where a cat avoids water drops"
}
```

**Response:**
```json
{
  "enhanced_prompt": "Create a 2D side-scrolling platformer game featuring..."
}
```

### `POST /generate-game`
Generates a complete HTML5 game using Claude AI.

**Request:**
```json
{
  "prompt": "Enhanced game description...",
  "title": "Rainy Cat Adventure"
}
```

**Response:**
```json
{
  "html": "<!DOCTYPE html>...",
  "game_id": "game_20241022_123456"
}
```

### `POST /update-game`
Updates an existing game based on user feedback.

**Request:**
```json
{
  "game_id": "game_20241022_123456",
  "feedback": "Add more enemies and power-ups",
  "current_html": "<!DOCTYPE html>..."
}
```

**Response:**
```json
{
  "html": "<!DOCTYPE html>... (updated)"
}
```

### `GET /games`
Lists all generated games with metadata.

### `GET /games/<game_id>`
Retrieves a specific game by ID.

---

## 🎮 How It Works

1. **Describe Your Game**: Enter a natural language description of your desired game
2. **AI Enhancement**: Gemini AI refines and enhances your prompt for optimal game generation  
3. **Game Generation**: Claude AI creates a complete HTML5 game using PhaserJS framework
4. **Play & Iterate**: Test your game and provide feedback for improvements
5. **Save & Share**: Download your games as HTML files for sharing

---

## 📂 Project Structure

```
├── backend/
│   ├── backend.py              # Main Flask application
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example           # Environment variables template
│   ├── games/                 # Generated games storage
│   └── screenshots/           # Game screenshots
├── frontend/
│   ├── src/
│   │   ├── Create.jsx         # Game creation interface
│   │   ├── App.jsx           # Main application
│   │   └── ...               # Other React components
│   ├── package.json          # Node.js dependencies
│   └── vite.config.js        # Vite configuration
└── README.md
```

---

## 🎯 Example Games

The AI can generate various types of games:
- **Platformers** - Jump and run adventures
- **Puzzle Games** - Brain teasers and logic challenges  
- **Arcade Games** - Classic retro-style gameplay
- **Action Games** - Fast-paced gameplay mechanics
- **Adventure Games** - Story-driven experiences

---

## 🧪 Example Usage

```bash
# Enhance a prompt
curl -X POST http://localhost:5000/enhance-prompt \
     -H "Content-Type: application/json" \
     -d '{"prompt": "a puzzle game where robots push boxes"}'

# Generate a game
curl -X POST http://localhost:5000/generate-game \
     -H "Content-Type: application/json" \
     -d '{"prompt": "enhanced prompt here", "title": "Robot Puzzle"}'
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Google Gemini AI for prompt enhancement capabilities
- Anthropic Claude for intelligent game code generation  
- PhaserJS community for the excellent game development framework
- React and Vite teams for modern frontend development tools
