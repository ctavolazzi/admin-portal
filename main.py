#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Simplified launcher aligning with Poetry-based setup

def main():
    print("[booting...]")
    from app import start_server
    print("[GOING ONLINE...]")
    start_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[exitted]")





