# Remote Control Lab

## Overview
Remote Control Lab is a client-server cybersecurity research framework designed to study remote system interaction, TCP-based communication, and command execution in controlled environments.

The system demonstrates how a master controller can interact with a remote worker agent over a persistent TCP connection to execute commands, transfer files, capture system data, and simulate remote administration behavior.

---

## Architecture

The system is composed of three core components:

### 🔹 Master Controller
Acts as the central control interface for issuing commands and managing remote sessions.

**Capabilities:**
- TCP session management
- Interactive command shell
- Bidirectional file transfer system
- Keypress injection commands
- Structured protocol communication
- Session termination control

---

### 🔹 Worker Agent
Runs on the target machine and executes received commands from the master.

**Capabilities:**
- Command execution via system shell
- Directory navigation (`cd`)
- File upload/download handling
- Screenshot capture (multi-screen support)
- Keylogging functionality
- Keyboard simulation (input injection)
- Auto-reconnection mechanism
- Persistent TCP communication loop

---

### 🔹 HTTP File Server
Auxiliary component used for file distribution and testing.

**Capabilities:**
- Lightweight HTTP file hosting
- Local directory exposure for controlled transfers
- Development/testing support for payload delivery

---

## Communication Protocol

All communication is based on a custom TCP protocol:

- `<END>` → message delimiter
- `|` → command argument separator
- Binary-safe file transfer system
- Chunk-based streaming (4096 bytes)

---

## Supported Commands

### System Commands
- `cd <path>` – change working directory
- `terminate` – close remote session
- general shell execution

### File Operations
- `transfer | mw | src | dst` – Master → Worker
- `transfer | wm | src | dst` – Worker → Master

### System Interaction
- `screenshot | path` – capture screen
- `keypress | data` – simulate keyboard input
- `start_keylog` – start keylogger
- `stop_keylog` – stop keylogger and return log

---

## Technical Features

- Multi-threaded TCP communication
- Persistent worker reconnection logic
- Chunk-based file transfer system
- Structured command parsing engine
- Cross-layer system interaction (OS + network)
- Event-driven response handling

---

## Technologies Used
- Python 3
- Socket Programming (TCP)
- Threading
- Subprocess execution
- PIL (image capture)
- pynput (keyboard interaction)
- HTTP server module

---

## Design Goals
This project was built to explore:

- Remote system communication patterns
- TCP protocol design and reliability
- File transfer mechanisms over sockets
- Command execution pipelines
- Client-server architecture modeling

---

## Ethical Notice
This project is intended strictly for educational and controlled laboratory environments. It must not be used on unauthorized systems or networks.

---

## Disclaimer
This software is provided for cybersecurity research and learning purposes only.
