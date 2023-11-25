import argparse

class FileTransferArgumentParser:
    def __init__(self, is_server: bool = False):
        self.is_server = is_server

        # Dictionary to store server-specific arguments
        self.server_arguments = {"broadcast_port": 0, 
                                 "pathfile_input": ""}

        # Dictionary to store client-specific arguments
        self.client_arguments = {"client_port": 0,
                                 "broadcast_port": 0,
                                 "pathfile_output": ""}

        self._parse_arguments()

    def _parse_arguments(self):
        # If the process is server, parse according to server needed arguments. Otherwise, parse according to client needed arguments.
        if self.is_server:
            self._parse_server_arguments()
        else:
            self._parse_client_arguments()

    def _parse_server_arguments(self):
        # Argument parser for server application
        parser = argparse.ArgumentParser(
            description="Server for handling file transfer connection to client"
        )

        # Adding server specific arguments
        parser.add_argument(
            "broadcast_port",
            metavar="[broadcast port]",
            type=int,
            help="Broadcast port used for all clients",
        )
        parser.add_argument(
            "pathfile_input",
            metavar="[pathfile input]",
            type=str,
            help="Path to the file to send",
        )

        # Parse server arguments
        args = parser.parse_args()
        self.server_arguments = {
            "broadcast_port": args.broadcast_port,
            "pathfile_input": args.pathfile_input,
        }

    def _parse_client_arguments(self):
        # Argument parser for component application
        parser = argparse.ArgumentParser(
            description="Client for handling file transfer connection from server"
        )

        # Adding client specific arguments
        parser.add_argument(
            "client_port",
            metavar="[client port]",
            type=int,
            help="Port where client service is located",
        )
        parser.add_argument(
            "broadcast_port",
            metavar="[broadcast port]",
            type=int,
            help="Broadcast port used for destination address",
        )
        parser.add_argument(
            "pathfile_output",
            metavar="[pathfile output]",
            type=str,
            help="Output file path",
        )

        # Parse client arguments
        args = parser.parse_args()
        self.client_arguments = {
            "client_port": args.client_port,
            "broadcast_port": args.broadcast_port,
            "pathfile_output": args.pathfile_output,
        }

    def get_value(self):
        if self.is_server:
            return self.server_arguments
        else:
            return self.client_arguments

    def __str__(self):
        result = ""
        if self.is_server:
            result = f"Server Parser:\n Broadcast port: {self.server_arguments['broadcast_port']}\n Input pathfile: {self.server_arguments['pathfile_input']}"
        else:
            result = f"Client Parser:\n Client Port: {self.client_arguments['client_port']}\n Broadcast port: {self.client_arguments['broadcast_port']}\n Output pathfile: {self.client_arguments['pathfile_output']}"
        return result