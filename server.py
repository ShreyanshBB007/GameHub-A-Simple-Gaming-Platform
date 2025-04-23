from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Score
import random
import os

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gameplatform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
socketio = SocketIO(app, async_mode='gevent')
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

# Game states
games = {
    'snake': {},
    'tetris': {}
}

# Tetris piece definitions
TETRIS_PIECES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/leaderboard/<game_type>')
def leaderboard(game_type):
    scores = Score.get_leaderboard(game_type)
    return render_template('leaderboard.html', scores=scores, game_type=game_type)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Snake Game Logic
@socketio.on('join_snake')
def handle_snake_join(data):
    room = data['room']
    join_room(room)
    if room not in games['snake']:
        games['snake'][room] = {
            'snake': [[10, 10]],  # Starting position
            'food': {'x': random.randint(0, 19), 'y': random.randint(0, 19)},
            'score': 0,
            'direction': 'RIGHT',
            'game_over': False
        }
    emit('game_joined', {
        'game': 'snake',
        'gameState': games['snake'][room]
    })

@socketio.on('snake_direction')
def handle_snake_direction(data):
    room = data['room']
    direction = data['direction']
    game = games['snake'].get(room)
    
    if game and not game['game_over']:
        game['direction'] = direction

@socketio.on('snake_move')
def handle_snake_move(data):
    room = data['room']
    game = games['snake'].get(room)
    
    if not game or game['game_over']:
        return

    # Get the head position
    head = game['snake'][0].copy()
    
    # Update head position based on direction
    if game['direction'] == 'UP':
        head[1] -= 1
    elif game['direction'] == 'DOWN':
        head[1] += 1
    elif game['direction'] == 'LEFT':
        head[0] -= 1
    elif game['direction'] == 'RIGHT':
        head[0] += 1

    # Check for collisions with walls
    if head[0] < 0 or head[0] >= 20 or head[1] < 0 or head[1] >= 20:
        game['game_over'] = True
    # Check for self-collision
    elif head in game['snake'][:-1]:
        game['game_over'] = True
    else:
        # Move snake
        game['snake'].insert(0, head)
        
        # Check if food is eaten
        if head[0] == game['food']['x'] and head[1] == game['food']['y']:
            game['score'] += 1
            # Generate new food position
            while True:
                new_food = {
                    'x': random.randint(0, 19),
                    'y': random.randint(0, 19)
                }
                if [new_food['x'], new_food['y']] not in game['snake']:
                    game['food'] = new_food
                    break
        else:
            game['snake'].pop()

    # Send updated game state
    emit('game_update', {
        'snake': game['snake'],
        'food': game['food'],
        'score': game['score'],
        'game_over': game['game_over']
    }, room=room)

@socketio.on('update_score')
def handle_score_update(data):
    if not current_user.is_authenticated:
        return
    
    game_type = data['game_type']
    score = data['score']
    
    new_score = Score(
        user_id=current_user.id,
        game_type=game_type,
        score=score
    )
    db.session.add(new_score)
    db.session.commit()
    
    # Emit updated leaderboard
    scores = Score.get_leaderboard(game_type)
    emit('leaderboard_update', {
        'scores': [{'username': score.user.username, 'score': score.score} 
                  for score in scores]
    }, broadcast=True)

@socketio.on('join_tetris')
def handle_tetris_join(data):
    room = data['room']
    join_room(room)
    if room not in games['tetris']:
        games['tetris'][room] = {
            'board': [[0] * 10 for _ in range(20)],
            'current_piece': random.choice(TETRIS_PIECES),
            'piece_position': [0, 3],  # [row, col]
            'score': 0,
            'game_over': False
        }
    emit('game_joined', {
        'game': 'tetris',
        'gameState': games['tetris'][room]
    })

@socketio.on('tetris_move')
def handle_tetris_move(data):
    room = data['room']
    move_type = data['move']  # 'left', 'right', 'down', 'rotate'
    game = games['tetris'].get(room)
    
    if not game or game['game_over']:
        return

    current_pos = game['piece_position']
    current_piece = game['current_piece']
    
    if move_type == 'left' and can_move(game['board'], current_piece, current_pos[0], current_pos[1] - 1):
        game['piece_position'][1] -= 1
    elif move_type == 'right' and can_move(game['board'], current_piece, current_pos[0], current_pos[1] + 1):
        game['piece_position'][1] += 1
    elif move_type == 'down':
        if can_move(game['board'], current_piece, current_pos[0] + 1, current_pos[1]):
            game['piece_position'][0] += 1
        else:
            # Place the piece and check for completed lines
            place_piece(game)
            lines_cleared = clear_lines(game['board'])
            game['score'] += lines_cleared * 100
            
            # Check for game over
            if not spawn_new_piece(game):
                game['game_over'] = True
                emit('game_update', {
                    'board': game['board'],
                    'score': game['score'],
                    'game_over': True
                }, room=room)
                return
    
    elif move_type == 'rotate':
        rotated_piece = rotate_piece(current_piece)
        if can_move(game['board'], rotated_piece, current_pos[0], current_pos[1]):
            game['current_piece'] = rotated_piece

    emit('game_update', {
        'board': game['board'],
        'current_piece': game['current_piece'],
        'piece_position': game['piece_position'],
        'score': game['score'],
        'game_over': game['game_over']
    }, room=room)

def can_move(board, piece, row, col):
    for i in range(len(piece)):
        for j in range(len(piece[0])):
            if piece[i][j]:
                new_row, new_col = row + i, col + j
                if (new_row >= len(board) or 
                    new_col < 0 or 
                    new_col >= len(board[0]) or 
                    (new_row >= 0 and board[new_row][new_col])):
                    return False
    return True

def place_piece(game):
    board = game['board']
    piece = game['current_piece']
    row, col = game['piece_position']
    
    for i in range(len(piece)):
        for j in range(len(piece[0])):
            if piece[i][j]:
                board[row + i][col + j] = 1

def clear_lines(board):
    lines_cleared = 0
    i = len(board) - 1
    while i >= 0:
        if all(board[i]):
            del board[i]
            board.insert(0, [0] * len(board[0]))
            lines_cleared += 1
        else:
            i -= 1
    return lines_cleared

def rotate_piece(piece):
    return list(zip(*piece[::-1]))

def spawn_new_piece(game):
    game['current_piece'] = random.choice(TETRIS_PIECES)
    game['piece_position'] = [0, 3]
    return can_move(game['board'], game['current_piece'], 0, 3)

if __name__ == '__main__':
    socketio.run(app, debug=True)