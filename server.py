import socket
import threading
import os
import sys

# Dictionary to store connected clients and their usernames
clients = {}
lock = threading.Lock()

def send_file(client_socket, command, filename, target_folder):
    """Sends a file in chunks to the client for download.

    Args:
        client_socket (socket.socket object): The socket of the client being sent the file
        command (str): The command required to download the file
        filename (str): The name of the file being downloaded
        target_folder (str): The desired destination of the download
    """
    
    file_path = os.path.join(f"downloads", filename)
    # Ensures works for different systems
    if not os.path.exists(file_path):
        client_socket.send(f"{filename} doesn't exist".encode())
        log(f"Failed file download from {client_socket}")
    else:
        # Send a message to alert client file is being sent
        client_socket.send(f"/download {filename} {target_folder}".encode())
        # Read as binary to send over actual file rather than contents
        with open(file_path, 'rb') as file:
            #Sending file as chunks in case file is large
            while True:
                data = file.read(1024)
                if not data:
                    break
                client_socket.sendall(data)
        file.close()
        client_socket.send("".encode())
        client_socket.send("!!Transfer Complete!!".encode())
        log(f"{filename} successfully downloaded by {client_socket}")

def log(message):
    """Writes messages to server.log about activities in messenger.

    Args:
        message (str): The message to be written to the server.log file
    """
    
    with open("server.log", "a") as log_file:
        log_file.write(message + "\n")                
                    
def broadcast(message, sender_username):
    """Broadcast a message to all connected clients but user.
    Args:
        message (str): The message to be broadcast.
        sender_username (str): The username of the sender."""
        
    with lock:
        for client_socket, username in clients.items():
            # Checking not sending message back to sender
            if username != sender_username:
                try:
                    client_socket.send(message.encode())
                    log(f"(Broadcast) {message}")
                except socket.error or OSError.errno==9:
                    # Handle disconnection
                    remove_client(client_socket)

def unicast(message, sender_socket, recipient_username):
    """Unicast a message to a specific client.
    Args:
        message (str): The message to be sent to specific client.
        sender_socket(socket.socket object): The socket the server received the message from.
        recipient_username (str): The user receiving the message."""
        
    with lock:
        if recipient_username not in clients.values():
            # Can't send message to offline or non-existent user
            sender_socket.send(f"{recipient_username} is not online".encode())
        for client_socket, username in clients.items():
            #Sends only to desired user
            if recipient_username == username:
                try:
                    client_socket.send(message.encode())
                    log(f"(Unicast) {message}")
                except socket.error or OSError.errno==9:
                    # Handle disconnectoin
                    remove_client(client_socket)

def remove_client(client_socket):
    """Remove a client from the server.
    Args:
        client_socket (socket.socket object): The socket of the client to be disconnected."""
        
    with lock:
        username = clients[client_socket]
        log(f"User {username} disconnected from server")
        # Remove from dictionary to keep track of connected clients
        del clients[client_socket]
        client_socket.close()
        

def handle_client(client_socket, username):
    """Handle an individual client. 
    Args:
        client_socket (socket.socket object): The socket the user is connecting to the server from.
        username (str): The name of the client connected to the server."""
        
    welcome_message = f"Welcome to the chat, {username}!"
    client_socket.send(welcome_message.encode())

    broadcast(f"{username} has joined the chat.", username)
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                remove_client(client_socket)
                break

            if message.startswith("/leave"):
                # Meets requirement 1e
                broadcast(f"{username} has left the chat.",username)
                remove_client(client_socket)
                break
            
            elif message.startswith("/list"):
                # Meets requirement 2d)
                file_list = "\n".join(os.listdir("downloads"))
                file_message = "Files for download:\n"+file_list
                client_socket.send(file_message.encode())
                
            elif message.startswith("/download"):
                #Meets requirement 1e) and 1f)
                # Split the message into parts
                command, filename, target_folder = message.split()

                
                send_file(client_socket,command, filename, target_folder)
                   
            elif message.startswith("/pm"):
                # Meets requirement 1c) and 1d)
                #Unicast message
                recipient_username = ""
                #Extract target user and message
                for i in range(4, len(message)):
                    if message[i] == " ":
                        messageStart = i+1
                        break
                    else:
                        recipient_username+=message[i]
                unicast(f"{username} to {recipient_username}: {message[messageStart:]}", client_socket, recipient_username)
                
                
            else:
                #Meets requirement 1b)
                # Default messenging mode is broadcast
                broadcast(f"{username}: {message}", username)
        except socket.error or OSError.errno==9:
            
            # Handle disconnection
            remove_client(client_socket)
            break

def start_server(port):
    """Starts the server and threads to allow multiple client connections. 

    Args:
        port (int): The port number the server connects to
    """
    # TCP 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", port))
    server_socket.listen()
    log(f"Server listening on port {port}")
    print(f"Server listening on port {port}...")
    
    while True:
        try:
            #Accept a connection from client
            client_socket, client_address = server_socket.accept()
            username = client_socket.recv(1024).decode()

            with lock:
                #Keep track of connected clients
                clients[client_socket] = username

            print(f"Connection from {client_address} ({username})")
            log(f"User {username} connected from {client_address}")
            # Start a new thread to handle the client
            # Allow multiple clients to connect to server
            client_thread = threading.Thread(target=handle_client, args=(client_socket, username))
            client_thread.start()
        except KeyboardInterrupt:
            server_socket.close()
            sys.exit(1)
    
if __name__ == "__main__":
    # You can pass the port as a command-line argument
    start_server(port=int(sys.argv[1]))
