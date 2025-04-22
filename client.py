import socket
import tkinter as tk
from tkinter import messagebox
import logging

# Server Configuration
HOST = '127.0.0.1'  # Server IP
PORT = 12347        # Server Port

def connect_to_server():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        return client_socket
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
        return None

def send_choice(client_socket, choice):
    try:
        client_socket.send(choice.encode())
        response = client_socket.recv(1024).decode()
        return response
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send choice: {e}")
        return None

def display_games(client_socket):
    try:
        response = ""
        while True:
            chunk = client_socket.recv(1024).decode()
            response += chunk
            if "Select a game by entering the number:" in chunk:
                break

        # Extract only the lines that look like game entries (e.g., "1. Tic-Tac-Toe")
        games = []
        for line in response.splitlines():
            if line.strip().split(".")[0].isdigit():
                games.append(line)

        return games
    except Exception as e:
        messagebox.showerror("Error", f"Failed to receive games: {e}")
        return []

def on_game_select():
    try:
        selected_index = game_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Invalid Input", "Please select a game from the list.")
            return

        selected_line = game_listbox.get(selected_index[0])
        choice = selected_line.split(".")[0]  # Extract number before the dot
        response = send_choice(client_socket, choice)
        if response:
            messagebox.showinfo("Game Selection", response)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# GUI Setup
root = tk.Tk()
root.title("Multi-Game Client")

frame = tk.Frame(root)
frame.pack(pady=20, padx=20)

tk.Label(frame, text="Available Games:").pack()

game_var = tk.StringVar()
game_listbox = tk.Listbox(frame, listvariable=game_var, height=10, width=40)
game_listbox.pack()

tk.Button(frame, text="Select Game", command=on_game_select).pack(pady=10)

# Connect to server and populate game list
client_socket = connect_to_server()
if client_socket:
    games = display_games(client_socket)
    for game in games:
        game_listbox.insert(tk.END, game)

root.mainloop()

# Close connection when done
if client_socket:
    client_socket.close()
