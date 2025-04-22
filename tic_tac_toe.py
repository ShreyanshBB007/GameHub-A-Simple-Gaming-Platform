board = [
    [' ', ' ', ' '],
    [' ', ' ', ' '],
    [' ', ' ', ' ']
]

def display():
    print("\n")
    for i in range(3):
        for j in range(3):
            print(f" {board[i][j]} ", end="")
            if j < 2:
                print("|", end="")
        print()
        if i < 2:
            print("---|---|---")
    print("\n")

def play(player):
    move = int(input(f"Player {player}, enter your move (1-9): "))

    if move < 1 or move > 9:
        print("Invalid move!")
        return False

    row = (move - 1) // 3
    col = (move - 1) % 3

    if board[row][col] != ' ':
        print("Already occupied! Try again.")
        return False

    board[row][col] = player
    return True

def result():
    for i in range(3):
        if (board[i][0] != ' ' and board[i][0] == board[i][1] == board[i][2]) or \
           (board[0][i] != ' ' and board[0][i] == board[1][i] == board[2][i]):
            return 1

    if (board[0][0] != ' ' and board[0][0] == board[1][1] == board[2][2]) or \
       (board[0][2] != ' ' and board[0][2] == board[1][1] == board[2][0]):
        return 1

    for i in range(3):
        for j in range(3):
            if board[i][j] == ' ':
                return 0
    return 2

def main():
    player = 'X'
    while True:
        display()
        if not play(player):
            continue

        r = result()
        if r == 1:
            display()
            print(f"Player {player} Wins!!")
            break
        if r == 2:
            display()
            print("It's a Draw!!")
            break

        player = 'O' if player == 'X' else 'X'

if __name__ == "__main__":
    main()
