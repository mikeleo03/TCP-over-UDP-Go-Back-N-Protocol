import socket
import threading
import sys

class TicTacToe:
    def __init__(self):
        # Initialize game board and state
        self.board = [
            [" ", " ", " "],
            [" ", " ", " "],
            [" ", " ", " "],
        ]
        self.turn = "X"
        self.you = "X"
        self.opponent = "O"
        self.winner = None
        self.game_over = False
        self.counter = 0

    def host_game(self, host, port):
        # Host a game by setting up a server socket and accepting connection
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(1)

        print(f"Waiting for a connection on {host}:{port}...")
        client, addr = server.accept()

        self.you = "X"
        self.opponent = "O"

        # Start a new thread to handle the game connection
        threading.Thread(target=self.handle_connection, args=(client,)).start()

    def connect_to_game(self, host, port):
        # Connect to a hosted game by setting up a client socket and connecting to the host
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((host, port))
        except ConnectionRefusedError:
            print("Connection refused. Make sure the host is running and try again.")
            sys.exit(1)

        self.you = "O"
        self.opponent = "X"

        # Start a new thread to handle the game connection
        threading.Thread(target=self.handle_connection, args=(client,)).start()

    def handle_connection(self, client):
        # Handle game logic and communication with opponent
        print("Connection established. Game starting...")
        while not self.game_over:
            if self.turn == self.you:
                move = input("Enter your move (row,column): ")
                if self.is_valid_move_format(move.split(",")) and self.check_valid_move(
                    move.split(",")
                ):
                    # If the move valid, apply it and switch turn
                    self.apply_move(move.split(","), self.you)
                    self.turn = self.opponent
                    client.send(move.encode("utf-8"))
                else:
                    print("Invalid move format or cell already occupied. Try again.")
            else:
                data = client.recv(1024)
                if not data:
                    break
                else:
                    self.apply_move(data.decode("utf-8").split(","), self.opponent)
                    self.turn = self.you
        client.close()

    def is_valid_move_format(self, move):
        # Check Valid format e.g. "0,0"
        return (
            len(move) == 2
            and move[0].isdigit()
            and move[1].isdigit()
            and 0 <= int(move[0]) < 3
            and 0 <= int(move[1]) < 3
        )

    def apply_move(self, move, player):
        # Apply move to game board and check winner or tie
        if self.game_over:
            return
        self.counter += 1
        row, col = int(move[0]), int(move[1])
        self.board[row][col] = player
        self.print_board()

        if self.check_if_won():
            if self.winner == self.you:
                print("You win!")
                exit()
            elif self.winner == self.opponent:
                print("You lose!")
                exit()
        else:
            if self.counter == 9:
                print("It's a tie!")
                exit()

    def check_valid_move(self, move):
        # Check if the move is valid and empty
        row, col = int(move[0]), int(move[1])
        return 0 <= row < 3 and 0 <= col < 3 and self.board[row][col] == " "

    def check_if_won(self):
        # Checks if there is a winner in the current game state
        for row in range(3):
            if self.board[row][0] == self.board[row][1] == self.board[row][2] != " ":
                self.winner = self.board[row][0]
                self.game_over = True
                return True

        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != " ":
                self.winner = self.board[0][col]
                self.game_over = True
                return True

        if self.board[0][0] == self.board[1][1] == self.board[2][2] != " ":
            self.winner = self.board[0][0]
            self.game_over = True
            return True

        if self.board[0][2] == self.board[1][1] == self.board[2][2] != " ":
            self.winner = self.board[0][2]
            self.game_over = True
            return True
        return False

    def print_board(self):
        print("\n    0   1   2")
        for row in range(3):
            print(row, end=" ")
            for col in range(3):
                print(f"| {self.board[row][col]} ", end="")
            print("|")
            if row != 2:
                print("  -----------")

    def run_game(self, role, host, port):
        # Start the game based on the specified role (host or connect)
        if role == "host":
            self.host_game(host, port)
        elif role == "connect":
            self.connect_to_game(host, port)
        else:
            print("Invalid role. Use 'host' or 'connect.'")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        # Prints usage information if the command line arguments are incorrect
        print("Usage: python tictactoe.py <role> <host> <port>")
        sys.exit(1)

    role, host, port = sys.argv[1], sys.argv[2], int(sys.argv[3])

    game = TicTacToe()
    game.run_game(role, host, port)

# Cara main: 
# python tictactoe.py host localhost 9999
# python tictactoe.py connect localhost 9999