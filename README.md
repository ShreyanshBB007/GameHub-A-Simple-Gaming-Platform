# GameHub : A Simple Gaming Platform
A web-based interactive gaming platform designed for children, featuring games with a leaderboard system to track progress and encourage engagement.

## 🎮 Features

- **Multiple Games**:
  - Snake Game - Classic snake gameplay with responsive controls
  - Tetris - Block-stacking puzzle game

- **User Management**:
  - Secure user registration and login system
  - Personal profiles to track individual progress

- **Leaderboard System**:
  - Competitive leaderboards for each game

## 🛠️ Technologies Used

- **Backend**:
  - Flask - Python web framework
  - Flask-SocketIO - For real-time communication
  - SQLAlchemy - ORM for database management
  - Flask-Login - User authentication

- **Frontend**:
  - HTML5, CSS3, JavaScript
  - Responsive design for various devices

- **Database**:
  - SQLite - Lightweight database for storing user data and scores

## 📋 Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## ⚙️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/Learning-Platform-for-Children.git
   cd Learning-Platform-for-Children
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   # The database will be automatically created when you run the application
   ```

5. Run the application:
   ```bash
   python server.py
   ```

6. Access the application in your web browser at [http://localhost:5000](http://localhost:5000)

## 🎯 How to Play

1. Register an account or log in if you already have one
2. Select a game from the main menu
3. Follow the on-screen instructions for each game:
   - **Snake**: Use arrow keys to control the snake. Eat food to grow and earn points.
   - **Tetris**: Use arrow keys to move and rotate pieces. Complete lines to earn points.
4. View your scores on the leaderboard and compete with others!

## 📁 Project Structure

- `server.py` - Main Flask application and game server
- `models.py` - Database models for user management and score tracking
- `client.py` - Client-side utilities
- `static/` - Static assets (CSS, JavaScript, images)
- `templates/` - HTML templates for the web interface
