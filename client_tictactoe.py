import time
from client import Client
from typing import Tuple
import json
import socket

from lib.constant import (
    SYN_FLAG,
    ACK_FLAG,
    FIN_ACK_FLAG,
    PAYLOAD_SIZE,
    SYN_ACK_FLAG,
    TIMEOUT_LISTEN,
    WINDOW_SIZE,
)
from lib.segment import Segment
from lib.constant import (
    SYN_FLAG,
    ACK_FLAG,
    FIN_FLAG,
    SYN_ACK_FLAG,
    TIMEOUT,
    TIMEOUT_LISTEN,
)


class ClientTictactoe(Client):
    def __init__(self):
        super().__init__()
        self.board = [
            [" ", " ", " "],
            [" ", " ", " "],
            [" ", " ", " "],
        ]
        self.current_player = 0
        self.counter = 0
        self.winner = None
        self.game_over = False

    def print_board(self):
        print("\n    0   1   2")
        for row in range(3):
            print(row, end=" ")
            for col in range(3):
                print(f"| {self.board[row][col]} ", end="")
            print("|")
            if row != 2:
                print("  -----------")

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

    def apply_move(self, move, player):
        # Apply move to game board and check winner or tie
        if self.game_over:
            return
        self.counter += 1
        row, col = int(move[0]), int(move[1])
        self.board[row][col] = player
        self.print_board()

        if self.check_if_won():
            if self.winner == "O":
                print("You win!")
            elif self.winner == "X":
                print("You lose!")
        else:
            if self.counter == 9:
                print("It's a tie!")

    def display_board(self):
        print("\n    0   1   2")
        for row in range(3):
            print(row, end=" ")
            for col in range(3):
                print(f"| {self.board[row][col]} ", end="")
            print("|")
            if row != 2:
                print("  -----------")

    def three_way_handshake(self):
        return super().three_way_handshake()

    def listen_info_transfer(self):
        # File transfer, client-side
        data, server_address = None, None
        sequence_base = 2

        while True:
            try:
                data, server_address = self.connection.listen_single_segment(3)
                if server_address[1] == self.broadcast_port:
                    self.segment.set_from_bytes(data)
                    game_info = json.loads(data.decode())

                    # Extract information from the received JSON
                    board = game_info["board"]
                    current_player = game_info["current_player"]
                    winner = game_info["winner"]

                    if (
                        self.segment.valid_checksum()
                        and self.segment.get_header()["seq_num"] == request_number
                    ):
                        payload = self.segment.get_payload()
                        self.board = payload['board']
                        self.current_player = payload['current_player']
                        self.winner = payload['winner']
                        self.logger.debug(
                            f"[!] [Server {server_address[0]}:{server_address[1]}] Received Segment {request_number}"
                        )
                        self.logger.debug(
                            f"[!] [Server {server_address[0]}:{server_address[1]}] Sending ACK {request_number + 1}"
                        )
                        request_number += 1
                        self.send_ack(server_address, request_number)
                        move = input("Enter your move (row,column): ")
                        self.apply_move(move.split(","), "O")
                        response = Segment()
                        game_info = {
                            "board": self.board,
                            "current_player": self.current_player,
                            "winner": self.winner,
                        }
                        json_data = json.dumps(game_info)
                        header = response.get_header()
                        header["seq_num"] = sequence_base + 1
                        header["ack_num"] = sequence_base
                        response.set_header(header)
                        response.set_payload(json_data.encode())
                        self.connection.send_data(response.get_bytes(), server_address)
                        if (self.winner != None or self.counter == 9):
                            break
                        
                    elif self.segment.get_flag() == FIN_FLAG:
                        # Handle FIN segment
                        self.logger.debug(
                            f"[!] [Server {server_address[0]}:{server_address[1]}] Received FIN"
                        )
                        break
                    elif self.segment.get_header()["seq_num"] < request_number:
                        self.logger.warning(
                            f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Duplicate]"
                        )
                    elif self.segment.get_header()["seq_num"] > request_number:
                        self.logger.warning(
                            f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Out-Of-Order]"
                        )
                    else:
                        if not self.segment.valid_checksum():
                            self.logger.warning(
                                f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Invalid-Checksum]"
                            )
                        else:
                            self.logger.warning(
                                f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Corrupt]"
                            )
                else:
                    # Ignore segments with wrong port
                    self.logger.warning(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] Ignored Segment {self.segment.get_header()['seq_num']} [Wrong-Port]"
                    )

                self.send_ack(server_address, request_number)

            except socket.timeout:
                self.logger.error(
                    f"[!] [Server {server_address[0]}:{server_address[1]}] Timeout error. Resending previous sequence number"
                )
                self.send_ack(server_address, request_number)

        # Send FIN-ACK
        self.logger.debug(
            f"[!] [Server {server_address[0]}:{server_address[1]}] Sending FIN-ACK"
        )
        finack = Segment()
        finack.set_header({"ack_num": request_number, "seq_num": request_number})
        finack.set_flag(["FIN", "ACK"])
        self.connection.send_data(finack.get_bytes(), server_address)

        ack = False
        timeout = time.time() + TIMEOUT_LISTEN
        while not ack:
            try:
                (data, server_address) = self.connection.listen_single_segment()
                ack_segment = Segment()
                ack_segment.set_from_bytes(data)

                if ack_segment.get_flag() == ACK_FLAG:
                    self.logger.debug(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] Received ACK. Tearing down connection."
                    )
                    ack = True

            except socket.timeout:
                if time.time() > timeout:
                    self.logger.warning(
                        f"[!] [Server {server_address[0]}:{server_address[1]}] Waiting for too long. Connection closed"
                    )
                    break
                self.logger.warning(
                    f"[!] [Server {server_address[0]}:{server_address[1]}] Timeout error. Resending FIN-ACK"
                )
                self.connection.send_data(finack.get_bytes(), server_address)

        self.logger.info(
            f"[!] [Server {server_address[0]}:{server_address[1]}] Data received successfully"
        )
        self.logger.info(
            f"[!] [Server {server_address[0]}:{server_address[1]}] Writing file to out/{self.pathfile_output}"
        )

    def make_move(self, position: int):
        # Make a move on the Tic Tac Toe board
        if 0 <= position < 9 and self.board[position] == " ":
            self.board[position] = "X" if self.current_player == 0 else "O"
            return True
        else:
            print("Invalid move. Try again.")
            return False

    def check_winner(self) -> bool:
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

    def switch_player(self):
        # Switch to the next player
        self.current_player = 1 - self.current_player

    def send_ack(self, server_address, ack_number):
        response = {"type": "ack", "ack_number": ack_number}
        json_data = json.dumps(response)
        self.connection.send_data(json_data.encode(), server_address)

    def shutdown(self):
        return super().shutdown()


if __name__ == "__main__":
    main = ClientTictactoe()
    main.connect()
    main.three_way_handshake()
    main.listen_file_transfer()
    main.shutdown()
