from server import Server
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


class ServerTictactoe(Server):
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

    def listen_for_clients(self):
        self.logger.debug("[!] Listening to broadcast address for clients.")
        while len(self.client_list) < 2:
            try:
                client = self.connection.listen_single_segment(TIMEOUT_LISTEN)
                client_address = client[1]
                ip, port = client_address
                self.client_list.append(client_address)
                self.logger.debug(f"[!] Received request from {ip}:{port}")
            except socket.timeout:
                if len(self.client_list) == 0:
                    self.logger.error("[!] Timeout error for listening client. Exiting")
                else:
                    self.logger.warning("[!] Timeout error for listening client")
                break

    # -- Game Handler --
    def start_game(self):
        self.logger.debug("[!] Starting game...")

        for client in self.client_list:
            self.three_way_handshake(client)
            self.info_transfer(client)

    def info_transfer(self, client_address: Tuple[str, int]):
        num_of_segment = 6
        sequence_base = 2
        reset_conn = False
        request_number = 2

        while sequence_base < num_of_segment and not reset_conn:
            # for i in range(sequence_max):
            #     # Start sending segment x
            #     self.logger.debug(
            #         f"[!] [Client {client_address[0]}:{client_address[1]}] Sending Segment {sequence_base + i}"
            #     )
            #     if i + sequence_base < num_of_segment:
            #         self.connection.send_data(
            #             self.list_segment[i + sequence_base - 2].get_bytes(),
            #             client_address,
            #         )

            for i in range(4):
                try:
                    data, response_address = self.get_segment(client_address)
                    segment = Segment()
                    segment.set_from_bytes(data)

                    # Various segment conditions
                    if (
                        client_address[1] == response_address[1]
                        and segment.get_flag() == ACK_FLAG
                        and segment.get_header()["ack_num"] == sequence_base + 1
                    ):
                        self.logger.debug(
                            f"[!] [Client {client_address[0]}:{client_address[1]}] Received ACK {sequence_base + 1}"
                        )
                        sequence_base += 1
                    elif segment.get_flag() == SYN_ACK_FLAG:
                        self.logger.debug(
                            f"[!] [Client {client_address[0]}:{client_address[1]}] Received SYN ACK Flag, client ask to reset connection"
                        )
                        reset_conn = True
                        break
                    elif (
                        self.segment.valid_checksum()
                        and self.segment.get_header()["seq_num"] == request_number
                    ):
                        payload = self.segment.get_payload()
                        self.board = payload['board']
                        self.current_player = payload['current_player']
                        self.winner = payload['winner']
                        self.logger.debug(
                            f"[!] [Server {client_address[0]}:{client_address[1]}] Received Segment {request_number}"
                        )
                        self.logger.debug(
                            f"[!] [Server {client_address[0]}:{client_address[1]}] Sending ACK {request_number + 1}"
                        )
                        request_number += 1
                        self.send_ack(client_address, request_number)
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
                        self.connection.send_data(response.get_bytes(), client_address)
                        if (self.winner != None or self.counter == 9):
                            break
                    elif segment.get_flag() != ACK_FLAG:
                        self.logger.warning(
                            f"[!] [Client {client_address[0]}:{client_address[1]}] Received Wrong Flag"
                        )
                    else:
                        self.logger.warning(
                            f"[!] [Client {client_address[0]}:{client_address[1]}] Received Wrong ACK"
                        )
                        request_number = segment.get_header()["ack_num"]
                        if request_number > sequence_base:
                            sequence_base = request_number

                except socket.timeout:
                    self.logger.error(
                        f"[!] [Client {client_address[0]}:{client_address[1]}] ACK response timeout. Resending previous sequence number"
                    )

            if reset_conn:
                self.three_way_handshake(client_address)
                self.file_transfer(client_address)
            else:
                self.logger.info(
                    f"[!] [Client {client_address[0]}:{client_address[1]}] File transfer complete. Sending FIN"
                )
                sendFIN = Segment()
                sendFIN.set_flag(["FIN"])
                self.connection.send_data(sendFIN.get_bytes(), client_address)
                is_ack = False
                game_info = {
                    "board": self.board,
                    "current_player": self.current_player,
                    "winner": self.winner,
                }
                json_data = json.dumps(game_info)
                self.connection.send_data(json_data.encode(), client_address)

            # Wait for ack
            while not is_ack:
                try:
                    data, response_address = self.get_segment(client_address)
                    segment = Segment()
                    segment.set_from_bytes(data)
                    if (
                        client_address[1] == response_address[1]
                        and segment.get_flag() == FIN_ACK_FLAG
                    ):
                        self.logger.debug(
                            f"[!] [Client {client_address[0]}:{client_address[1]}] Received FIN-ACK"
                        )
                        sequence_base += 1
                        is_ack = True
                        if self.parallel:
                            self.parallel_client_list.pop(client_address)

                except socket.timeout:
                    self.logger.error(
                        f"[!] [Client {client_address[0]}:{client_address[1]}] ACK response timeout. Resending FIN"
                    )
                    self.connection.send_data(sendFIN.get_bytes(), client_address)

            # send ACK and tear down connection
            self.logger.info(
                f"[!] [Client {client_address[0]}:{client_address[1]}] Sending ACK. Tearing down connection."
            )
            segmentACK = Segment()
            segmentACK.set_flag(["ACK"])
            self.connection.send_data(segmentACK.get_bytes(), client_address)

    def three_way_handshake(self, client_address: Tuple[str, int]) -> bool:
        return super().three_way_handshake(client_address)

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


if __name__ == "__main__":
    main = ServerTictactoe()
    main.listen_for_clients()
    if not main.parallel:
        main.start_game()
