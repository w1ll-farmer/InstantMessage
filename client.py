import socket
import threading
import os
import sys

def receive_messages(client_socket):
    """Receive messages from the server.
    
    Args:
        client_socket(socket.socket object): The socket the client is connecting to the server from
    """
    
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break
                
            if message.strip().startswith("/download"):
                receive_file(client_socket, message)
            else:
                print(message)
                print("> ", end="", flush=True)  # Display the prompt after receiving a message
        except socket.error or OSError.errno == 9:
            print("Connection to the server lost.")
            break


def send_messages(client_socket, username):
    """Send messages to the server.
    
    Args:
        client_socket (socket.socket object): The socket the client is connecting to the server from
        username (str): The client's chosen username.
    """
    
    try:
        while True:
            message = input("")
            if message.lower() == "/leave":
                print("Logging off...")
                client_socket.send(f"/leave".encode())
                break
            elif message.lower().startswith("/download"):
                request_file(client_socket, message)
            else:
                client_socket.send(message.encode())
                print("> ", end="", flush=True)  # Display the prompt after sending a message
    except KeyboardInterrupt:
        pass  # Handle Ctrl+C gracefully
    except socket.error or OSError.errno == 9:
        print("Connection to the server lost.")

def receive_file(client_socket, message):
    """Allows the client to receive a downloaded file and save it 

    Args:
        client_socket (socket.socket object): The socket the client is connecting to the server from
        message (str): The message specifying filename and desired location
    """
    try:
        filename, dest = message.split(" ")[1], message.split(" ")[2]
        
        os.makedirs(dest, exist_ok=True)
        #Makes directory if doesn't already exist
        file_path = os.path.join(dest, filename)
        file_data = b""
        #Binary file data
        while True:
            #Runs until all contents transferred
            data = client_socket.recv(1024)
            if "!!Transfer Complete!!".encode() in data:
                #Flag used to signal end of transfer
                data = data[:-22]
                #Cut off flag from data so isn't written to file
                file_data+=data
                break
            if not data:
                break
            file_data+=data
            
        with open(file_path, 'wb') as file:
            file.write(file_data)
        file.close()
        print("File Downloaded")
        print("> ", end="", flush=True)  # Display the prompt after receiving a message
            
    except Exception as e:
        print("Error during file download:")
        print(f"{e}")

def request_file(client_socket, message):
    """Allows the user to request a file from server to download

    Args:
        client_socket (socket.socket Object): The socket the client is using to connect to the server
        message (str): The message containing name and required download destination of the file
    """
    try:
        client_socket.send(message.encode())
        print("File download request sent. Waiting for server response...")
    except Exception as e:
        print("Error sending file download request:")
        print(f"{e}")

def start_client(username, host, port):
    """Connects client to server and starts threads for receiving and sending messages.

    Args:
        username (str): The username of the client
        host (str): The hostname of the client
        port (int): The port the client wants to connect to
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    client_socket.send(username.encode())

    # Start threads for sending and receiving messages
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    send_thread = threading.Thread(target=send_messages, args=(client_socket, username))

    receive_thread.start()
    send_thread.start()

    # Wait for both threads to finish
    send_thread.join()
    receive_thread.join()

    # Close the socket when the threads finish
    client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py [username] [hostname] [port]")
        sys.exit(1)

    username = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])

    start_client(username, host, port)
