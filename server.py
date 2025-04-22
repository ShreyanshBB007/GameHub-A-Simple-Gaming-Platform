from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, async_mode='gevent')

# Game states
games = {
    'tic_tac_toe': {},  # {room_id: {board: [], current_player: 'X', players: [], game_over: False}}
    'snake': {}  # {room_id: {snake: [], food: {}, score: 0, game_over: False}}
}

@app.route('/')
def index():
    return render_template('index.html')

# Tic Tac Toe Logic
def check_winner(board):
    # Check rows, columns and diagonals
    win_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]  # Diagonals
    ]
    for combo in win_combinations:
        if board[combo[0]] and board[combo[0]] == board[combo[1]] == board[combo[2]]:
            return board[combo[0]]
    if '' not in board:  # Check for draw
        return 'draw'
    return None

@socketio.on('join_tictactoe')
def handle_tictactoe_join(data):
    room = data['room']
    join_room(room)
    if room not in games['tic_tac_toe']:
        games['tic_tac_toe'][room] = {
            'board': [''] * 9,
            'current_player': 'X',
            'players': [],
            'game_over': False
        }
    games['tic_tac_toe'][room]['players'].append(request.sid)
    emit('game_joined', {'game': 'tic_tac_toe', 'player': len(games['tic_tac_toe'][room]['players'])})

@socketio.on('make_move_tictactoe')
def handle_tictactoe_move(data):
    room = data['room']
    position = data['position']
    game = games['tic_tac_toe'].get(room)
    
    if not game or game['game_over'] or position < 0 or position > 8:
        return
    
    if game['board'][position] == '' and request.sid in game['players']:
        game['board'][position] = game['current_player']
        winner = check_winner(game['board'])
        
        response = {
            'board': game['board'],
            'current_player': game['current_player'],
            'winner': winner if winner != 'draw' else "It's a draw!"
        }
        
        if winner:
            game['game_over'] = True
        else:
            game['current_player'] = 'O' if game['current_player'] == 'X' else 'X'
        
        emit('move_made', response, room=room)

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

if __name__ == '__main__':
    socketio.run(app, debug=True)