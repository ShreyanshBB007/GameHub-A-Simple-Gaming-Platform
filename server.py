import socket
import threading
import logging
import time

# Server Configuration
HOST = '127.0.0.1'  # Localhost
PORT = 12347        # Port to listen on

# List of available games
GAMES = ["Snake & Ladders", "Ludo", "Chess", "Tic-Tac-Toe", "Rock-Paper-Scissors"]

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def tic_tac_toe(client_socket):
    client_socket.send("Starting Tic-Tac-Toe...\n".encode())
    board = [" "] * 9

    def display_board():
        return f"\n{board[0]} | {board[1]} | {board[2]}\n---------\n{board[3]} | {board[4]} | {board[5]}\n---------\n{board[6]} | {board[7]} | {board[8]}\n"

    def check_winner():
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        for condition in win_conditions:
            if board[condition[0]] == board[condition[1]] == board[condition[2]] != " ":
                return board[condition[0]]
        return None

    turn = "X"
    for _ in range(9):
        client_socket.send(display_board().encode())
        client_socket.send(f"{turn}'s turn. Enter position (1-9):\n".encode())
        try:
            move = int(client_socket.recv(1024).decode().strip()) - 1
            if board[move] == " ":
                board[move] = turn
                winner = check_winner()
                if winner:
                    client_socket.send(display_board().encode())
                    client_socket.send(f"{winner} wins!\n".encode())
                    return
                turn = "O" if turn == "X" else "X"
            else:
                client_socket.send("Invalid move. Try again.\n".encode())
        except (ValueError, IndexError):
            client_socket.send("Invalid input. Enter a number between 1 and 9.\n".encode())

    client_socket.send(display_board().encode())
    client_socket.send("It's a draw!\n".encode())

def rock_paper_scissors(client_socket):
    client_socket.send("Starting Rock-Paper-Scissors...\n".encode())
    choices = ["rock", "paper", "scissors"]

    def determine_winner(player, computer):
        if player == computer:
            return "It's a tie!"
        elif (player == "rock" and computer == "scissors") or \
             (player == "scissors" and computer == "paper") or \
             (player == "paper" and computer == "rock"):
            return "You win!"
        else:
            return "Computer wins!"

    while True:
        client_socket.send("Enter rock, paper, or scissors (or 'quit' to exit):\n".encode())
        player_choice = client_socket.recv(1024).decode().strip().lower()
        if player_choice == "quit":
            client_socket.send("Exiting Rock-Paper-Scissors.\n".encode())
            break
        if player_choice not in choices:
            client_socket.send("Invalid choice. Try again.\n".encode())
            continue

        import random
        computer_choice = random.choice(choices)
        result = determine_winner(player_choice, computer_choice)
        client_socket.send(f"Computer chose {computer_choice}. {result}\n".encode())

def handle_client(client_socket):
    try:
        logging.info("Handling new client connection.")
        # Send the list of games to the client
        client_socket.send("Welcome to the Multi-Game Platform!\n".encode())
        client_socket.send("Available games:\n".encode())
        for idx, game in enumerate(GAMES, start=1):
            client_socket.send(f"{idx}. {game}\n".encode())
        client_socket.send("Select a game by entering the number:\n".encode())

        # Ensure the client has time to process the data
        client_socket.settimeout(30)  # Set a timeout of 30 seconds for receiving data

        # Receive the client's choice
        choice = client_socket.recv(1024).decode().strip()
        logging.debug(f"Received raw data from client: {choice}")
        logging.debug(f"Received choice from client: {choice}")
        if choice.isdigit() and 1 <= int(choice) <= len(GAMES):
            selected_game = GAMES[int(choice) - 1]
            logging.info(f"Client selected game: {selected_game}")
            client_socket.send(f"You selected: {selected_game}\n".encode())

            if selected_game == "Tic-Tac-Toe":
                logging.debug("Starting Tic-Tac-Toe game logic.")
                tic_tac_toe(client_socket)
            elif selected_game == "Rock-Paper-Scissors":
                logging.debug("Starting Rock-Paper-Scissors game logic.")
                rock_paper_scissors(client_socket)
            else:
                logging.warning("Game logic not implemented for the selected game.")
                client_socket.send("Game logic will be implemented here.\n".encode())
        else:
            logging.warning(f"Invalid game choice received: {choice}")
            client_socket.send("Invalid choice. Disconnecting.\n".encode())
            logging.warning("Client made an invalid choice.")
    except socket.timeout:
        logging.error("Client did not respond in time. Closing connection.")
        client_socket.send("Timeout: No response received. Disconnecting.\n".encode())
    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        client_socket.close()
        logging.info("Client connection closed.")

# Main server function
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server started on {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")
        logging.info(f"Connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_server()