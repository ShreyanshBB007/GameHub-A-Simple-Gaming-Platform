# GameHub: A Simple Gaming Platform

GameHub is a web-based interactive gaming platform designed for children and casual users. It features a collection of classic games—Snake, Tetris, Pong, and Tic Tac Toe—with both single-player and real-time multiplayer modes. The platform includes secure user authentication, persistent leaderboards, and a modern, responsive interface.

---

## 🚀 Features

- **Multiple Games:**
  - **Snake** (Single Player): Classic snake gameplay with real-time controls and scoring.
  - **Tetris** (Single Player): Block-stacking puzzle game with line-clearing and increasing difficulty.
  - **Pong** (Multiplayer): Two-player real-time Pong with keyboard controls and score tracking.
  - **Tic Tac Toe** (Multiplayer): Two-player Tic Tac Toe with real-time updates and win/draw detection.

- **User Management:**
  - Secure registration and login (passwords hashed, session-based authentication).
  - User profiles with personal score history.

- **Leaderboard System:**
  - Persistent, per-game leaderboards showing top scores and player rankings.
  - Leaderboards update in real time as games finish.

- **Real-Time Multiplayer:**
  - Multiplayer games use WebSockets (Flask-SocketIO) for instant updates and smooth gameplay.

- **Modern UI:**
  - Responsive HTML5/CSS3 interface with dynamic game selection and in-browser gameplay.

---

## 🛠️ Technologies Used

- **Backend:**
  - Flask (Python web framework)
  - Flask-SocketIO (real-time communication)
  - Flask-Login (user authentication)
  - Flask-SQLAlchemy (ORM for database management)
  - Gevent (asynchronous server)
- **Frontend:**
  - HTML5, CSS3, JavaScript (with Canvas for games)
- **Database:**
  - SQLite (stores users, scores, and leaderboards)

---

## 📋 Requirements

- Python 3.7+
- See `requirements.txt` for dependencies

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd GameHub-A-Simple-Gaming-Platform
   ```
2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Linux/macOS
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the application:**
   ```bash
   python server.py
   ```
5. **Access the app:**
   Open your browser to [http://localhost:5000](http://localhost:5000)

*The database (`gameplatform.db`) is created automatically on first run.*

---

## 🕹️ How to Play

1. **Register** a new account or **log in** with existing credentials.
2. **Choose a game** from the main menu:
   - **Single Player:** Snake, Tetris
   - **Multiplayer:** Pong, Tic Tac Toe
3. **Game Controls:**
   - **Snake:** Arrow keys to move. Eat food, avoid walls and yourself.
   - **Tetris:** Arrow keys to move/rotate, space for hard drop.
   - **Pong:**
     - Player 1: W/S keys (left paddle)
     - Player 2: Up/Down arrows (right paddle)
   - **Tic Tac Toe:** Click to place your mark. First to 3 in a row wins.
4. **Leaderboard:**
   - View top scores for each game via the leaderboard links.
   - Scores update in real time after each game.

---

## 🗂️ Project Structure

- `server.py` — Main Flask app, game logic, SocketIO events, and routes.
- `models.py` — SQLAlchemy models for `User` and `Score`, leaderboard queries.
- `requirements.txt` — Python dependencies.
- `static/` — Static assets (images, CSS, JS, background).
- `templates/` — HTML templates for all pages (login, register, index, leaderboard).
- `instance/gameplatform.db` — SQLite database (auto-generated).

---

## 🧩 Database Schema

- **User**: Stores username and hashed password.
- **Score**: Stores user, game type, score, and date. Used for leaderboards.
- **Leaderboard**: Top scores per game, queried dynamically.

---

## 🔒 Security & Authentication

- Passwords are securely hashed (Werkzeug).
- User sessions managed with Flask-Login.
- Only authenticated users can access games and leaderboards.

---

## 🌐 Real-Time & Multiplayer

- Multiplayer games (Pong, Tic Tac Toe) use SocketIO rooms for real-time, two-player matches.
- Game state is synchronized between clients and server for fairness and responsiveness.

---

## 📑 For Reports & Documentation

This README provides a detailed overview of the platform's features, architecture, and usage. It can be used as a prompt for generating technical reports, user guides, or presentations about the project.

---

## 📞 Contact & Contributions

For questions, suggestions, or contributions, please open an issue or submit a pull request.

---
