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
    return db.session.get(User, int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

# Game states
games = {
    'snake': {},
    'tetris': {},
    'pong': {},
    'tictactoe': {}
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
            'snake': [[20, 15]],  # Center of 40x30 grid
            'food': {'x': random.randint(0, 39), 'y': random.randint(0, 29)},
            'score': 0,
            'direction': 'RIGHT',
            'last_direction': 'RIGHT',  # Track the last processed direction
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
        # Prevent 180-degree turns
        opposite_directions = {
            'UP': 'DOWN',
            'DOWN': 'UP',
            'LEFT': 'RIGHT',
            'RIGHT': 'LEFT'
        }
        
        # Only change direction if it's not opposite to the current direction
        if direction != opposite_directions[game['direction']]:
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
    
    # Store last processed direction
    game['last_direction'] = game['direction']

    # Updated wall collision for 40x30 grid
    if head[0] < 0 or head[0] >= 40 or head[1] < 0 or head[1] >= 30:
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
                    'x': random.randint(0, 39),
                    'y': random.randint(0, 29)
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

@socketio.on('restart_snake')
def handle_restart_snake(data):
    room = data['room']
    # Reset the snake game state
    games['snake'][room] = {
        'snake': [[20, 15]],  # Center of 40x30 grid
        'food': {'x': random.randint(0, 39), 'y': random.randint(0, 29)},
        'score': 0,
        'direction': 'RIGHT',
        'last_direction': 'RIGHT',
        'game_over': False
    }
    # Send the reset game state
    emit('game_joined', {
        'game': 'snake',
        'gameState': games['snake'][room]
    })

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
def handle_join_tetris(data):
    room = data['room']
    join_room(room)
    # Only initialize if not already present
    if room not in games['tetris']:
        games['tetris'][room] = {
            'board': [[0 for _ in range(10)] for _ in range(20)],  # 10x20 grid
            'current_piece': generate_tetris_piece(),
            'piece_position': [0, 3],  # row, col
            'next_piece': generate_tetris_piece(),
            'score': 0,
            'level': 1,
            'game_over': False
        }
    # Notify client game started
    emit('game_joined', {
        'game': 'tetris',
        'gameState': games['tetris'][room]
    })

@socketio.on('tetris_move')
def handle_tetris_move(data):
    room = data['room']
    move = data['move']
    game = games['tetris'].get(room)
    
    if not game or game['game_over']:
        return
    
    board = game['board']
    current_piece = game['current_piece']
    position = list(game['piece_position'])  # Create a copy to modify

    def valid_position(piece, pos):
        for row in range(len(piece)):
            for col in range(len(piece[0])):
                if piece[row][col]:
                    new_row = pos[0] + row
                    new_col = pos[1] + col
                    if (new_row < 0 or new_row >= len(board) or
                        new_col < 0 or new_col >= len(board[0]) or
                        board[new_row][new_col]):
                        return False
        return True

    placed = False
    if move == 'left':
        new_pos = [position[0], position[1] - 1]
        if valid_position(current_piece, new_pos):
            position = new_pos
    elif move == 'right':
        new_pos = [position[0], position[1] + 1]
        if valid_position(current_piece, new_pos):
            position = new_pos
    elif move == 'rotate':
        rotated = [list(row) for row in zip(*current_piece[::-1])]
        if valid_position(rotated, position):
            current_piece = rotated
            game['current_piece'] = rotated
    elif move == 'down':
        new_pos = [position[0] + 1, position[1]]
        if valid_position(current_piece, new_pos):
            position = new_pos
        else:
            place_piece(game)
            completed_lines = check_completed_lines(game)
            if completed_lines > 0:
                scores = [100, 300, 500, 800]
                game['score'] += scores[completed_lines - 1] * game['level']
                game['level'] = 1 + game['score'] // 1000
            game['current_piece'] = game['next_piece']
            game['next_piece'] = generate_tetris_piece()
            game['piece_position'] = [0, 3]
            # Check for game over
            if not valid_position(game['current_piece'], game['piece_position']):
                game['game_over'] = True
            placed = True
    # Update position if not placed and not game over
    if not game['game_over'] and not placed:
        game['piece_position'] = position
    # Always emit game update after move
    emit('game_update', {
        'board': board,
        'current_piece': game['current_piece'],
        'piece_position': game['piece_position'],
        'score': game['score'],
        'game_over': game['game_over']
    }, to=room)

@socketio.on('restart_tetris')
def handle_restart_tetris(data):
    room = data['room']
    games['tetris'][room] = {
        'board': [[0 for _ in range(10)] for _ in range(20)],
        'current_piece': generate_tetris_piece(),
        'piece_position': [0, 3],
        'next_piece': generate_tetris_piece(),
        'score': 0,
        'level': 1,
        'game_over': False
    }
    emit('game_joined', {
        'game': 'tetris',
        'gameState': games['tetris'][room]
    })

def generate_tetris_piece():
    # Define all tetris pieces
    pieces = [
        # I piece
        [[1, 1, 1, 1]],
        # O piece
        [[1, 1], [1, 1]],
        # T piece
        [[0, 1, 0], [1, 1, 1]],
        # S piece
        [[0, 1, 1], [1, 1, 0]],
        # Z piece
        [[1, 1, 0], [0, 1, 1]],
        # J piece
        [[1, 0, 0], [1, 1, 1]],
        # L piece
        [[0, 0, 1], [1, 1, 1]]
    ]
    return random.choice(pieces)

def place_piece(game):
    board = game['board']
    piece = game['current_piece']
    position = game['piece_position']
    
    for row in range(len(piece)):
        for col in range(len(piece[0])):
            if piece[row][col]:
                if 0 <= position[0] + row < len(board) and 0 <= position[1] + col < len(board[0]):
                    board[position[0] + row][position[1] + col] = 1

def check_completed_lines(game):
    board = game['board']
    completed_lines = 0
    rows_to_remove = []
    
    # Check each row
    for i, row in enumerate(board):
        if all(cell for cell in row):
            rows_to_remove.append(i)
            completed_lines += 1
    
    # Remove completed lines
    for row_idx in sorted(rows_to_remove, reverse=True):
        board.pop(row_idx)
        board.insert(0, [0 for _ in range(10)])
    
    return completed_lines

def is_collision(game):
    board = game['board']
    piece = game['current_piece']
    position = game['piece_position']
    
    for row in range(len(piece)):
        for col in range(len(piece[0])):
            if piece[row][col]:
                if (position[0] + row >= len(board) or
                    position[1] + col < 0 or
                    position[1] + col >= len(board[0]) or
                    board[position[0] + row][position[1] + col]):
                    return True
    return False

# Pong Game Logic
@socketio.on('join_pong')
def handle_pong_join(data):
    room = data['room']
    join_room(room)
    
    # Initialize game state if it doesn't exist
    if room not in games['pong']:
        games['pong'][room] = {
            'players': [],
            'ball': {
                'x': 400,  # Center of the canvas
                'y': 300,
                'dx': 5,   # Initial ball direction and speed
                'dy': 5,
                'radius': 10
            },
            'paddles': {
                'left': {'y': 250, 'height': 100},   # Left paddle
                'right': {'y': 250, 'height': 100}   # Right paddle
            },
            'scores': {'left': 0, 'right': 0},
            'ready': 0,    # Number of players ready
            'in_progress': False
        }
        
    # Add player to the game
    player_id = request.sid
    player_num = len(games['pong'][room]['players'])
    
    # Only allow 2 players max
    if player_num < 2:
        games['pong'][room]['players'].append(player_id)
        player_side = 'left' if player_num == 0 else 'right'
        
        emit('pong_joined', {
            'side': player_side,
            'gameState': games['pong'][room]
        })
        
        # If two players have joined, start the game
        if len(games['pong'][room]['players']) == 2:
            emit('pong_ready', room=room)
    else:
        # Allow spectators
        emit('pong_spectate', {'gameState': games['pong'][room]})

@socketio.on('pong_player_ready')
def handle_pong_ready(data):
    room = data['room']
    game = games['pong'].get(room)
    
    if game:
        game['ready'] += 1
        if game['ready'] == 2:
            game['in_progress'] = True
            emit('pong_game_start', room=room)

@socketio.on('pong_paddle_move')
def handle_pong_paddle_move(data):
    room = data['room']
    side = data['side']  # 'left' or 'right'
    position = data['position']
    game = games['pong'].get(room)
    
    if game and game['in_progress']:
        game['paddles'][side]['y'] = position
        
        # Broadcast paddle position to other player
        emit('pong_paddle_update', {
            'side': side,
            'position': position
        }, room=room)

@socketio.on('pong_update')
def handle_pong_update(data):
    room = data['room']
    game = games['pong'].get(room)
    
    if not game or not game['in_progress']:
        return
    
    # Update ball position
    ball = game['ball']
    ball['x'] += ball['dx']
    ball['y'] += ball['dy']
    
    # Handle collisions with top and bottom walls
    if ball['y'] - ball['radius'] <= 0 or ball['y'] + ball['radius'] >= 600:
        ball['dy'] = -ball['dy']
    
    # Handle collisions with paddles
    left_paddle = game['paddles']['left']
    right_paddle = game['paddles']['right']
    
    # Left paddle collision
    if (ball['x'] - ball['radius'] <= 20 and  # Paddle width is 20px
        ball['y'] >= left_paddle['y'] and 
        ball['y'] <= left_paddle['y'] + left_paddle['height']):
        ball['dx'] = -ball['dx']
        # Adjust angle based on where the ball hits the paddle
        ball['dy'] += (ball['y'] - (left_paddle['y'] + left_paddle['height'] / 2)) * 0.1
    
    # Right paddle collision
    if (ball['x'] + ball['radius'] >= 780 and  # Canvas width (800) - paddle width
        ball['y'] >= right_paddle['y'] and 
        ball['y'] <= right_paddle['y'] + right_paddle['height']):
        ball['dx'] = -ball['dx']
        # Adjust angle based on where the ball hits the paddle
        ball['dy'] += (ball['y'] - (right_paddle['y'] + right_paddle['height'] / 2)) * 0.1
    
    # Check for scoring
    if ball['x'] - ball['radius'] <= 0:
        # Right player scores
        game['scores']['right'] += 1
        reset_ball(ball)
    elif ball['x'] + ball['radius'] >= 800:
        # Left player scores
        game['scores']['left'] += 1
        reset_ball(ball)
    
    # Send updated game state
    emit('pong_game_update', {
        'ball': ball,
        'scores': game['scores']
    }, room=room)

def reset_ball(ball):
    # Reset ball to center with random direction
    ball['x'] = 400
    ball['y'] = 300
    ball['dx'] = 5 if random.random() > 0.5 else -5
    ball['dy'] = 5 if random.random() > 0.5 else -5

# --- Tic Tac Toe Game Logic ---
@socketio.on('join_tictactoe')
def handle_tictactoe_join(data):
    room = data['room']
    join_room(room)
    if room not in games['tictactoe']:
        games['tictactoe'][room] = {
            'board': [[None for _ in range(3)] for _ in range(3)],
            'players': [],
            'turn': 0,  # 0 for X, 1 for O
            'winner': None,
            'draw': False
        }
    player_id = request.sid
    if player_id not in games['tictactoe'][room]['players'] and len(games['tictactoe'][room]['players']) < 2:
        games['tictactoe'][room]['players'].append(player_id)
    # Send game state and playerIndex to all players in the room
    for idx, pid in enumerate(games['tictactoe'][room]['players']):
        emit('tictactoe_joined', {
            'game': 'tictactoe',
            'gameState': games['tictactoe'][room],
            'playerIndex': idx
        }, room=pid)
    if len(games['tictactoe'][room]['players']) == 2:
        emit('tictactoe_start', room=room)

@socketio.on('tictactoe_move')
def handle_tictactoe_move(data):
    room = data['room']
    row = data['row']
    col = data['col']
    player_id = request.sid
    game = games['tictactoe'].get(room)
    if not game or game['winner'] or game['draw']:
        return
    player_index = game['players'].index(player_id) if player_id in game['players'] else -1
    if player_index != game['turn']:
        return  # Not this player's turn
    if game['board'][row][col] is not None:
        return  # Cell already taken
    symbol = 'X' if game['turn'] == 0 else 'O'
    game['board'][row][col] = symbol
    # Check win/draw
    winner = check_tictactoe_winner(game['board'])
    if winner:
        game['winner'] = winner
    elif all(cell is not None for row_ in game['board'] for cell in row_):
        game['draw'] = True
    else:
        game['turn'] = 1 - game['turn']
    emit('tictactoe_update', {
        'board': game['board'],
        'turn': game['turn'],
        'winner': game['winner'],
        'draw': game['draw']
    }, room=room)
    # Leaderboard update if game ended
    if game['winner'] or game['draw']:
        for idx, pid in enumerate(game['players']):
            if game['winner']:
                score = 1 if (game['winner'] == ('X' if idx == 0 else 'O')) else 0
            else:
                score = 0.5  # Draw
            if current_user.is_authenticated:
                new_score = Score(user_id=current_user.id, game_type='tictactoe', score=score)
                db.session.add(new_score)
        db.session.commit()
        scores = Score.get_leaderboard('tictactoe')
        emit('leaderboard_update', {
            'scores': [{'username': score.user.username, 'score': score.score} for score in scores]
        }, broadcast=True)

def check_tictactoe_winner(board):
    # Rows, columns, diagonals
    for i in range(3):
        if board[i][0] and board[i][0] == board[i][1] == board[i][2]:
            return board[i][0]
        if board[0][i] and board[0][i] == board[1][i] == board[2][i]:
            return board[0][i]
    if board[0][0] and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    return None

@socketio.on('restart_tictactoe')
def handle_restart_tictactoe(data):
    room = data['room']
    if room in games['tictactoe']:
        players = games['tictactoe'][room]['players']
        games['tictactoe'][room] = {
            'board': [[None for _ in range(3)] for _ in range(3)],
            'players': players,
            'turn': 0,
            'winner': None,
            'draw': False
        }
        # Send updated game state and playerIndex to all players
        for idx, pid in enumerate(players):
            emit('tictactoe_joined', {
                'game': 'tictactoe',
                'gameState': games['tictactoe'][room],
                'playerIndex': idx
            }, room=pid)

if __name__ == '__main__':
    socketio.run(app, debug=True)

