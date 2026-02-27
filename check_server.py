#!/usr/bin/env python3
import socket
import sys

def check_port(host='localhost', port=8001, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

if __name__ == "__main__":
    print(f"Checking if server is running on localhost:8001...")
    if check_port():
        print("✅ Port 8001 is open (server likely running)")
    else:
        print("❌ Port 8001 is closed (server not running)")