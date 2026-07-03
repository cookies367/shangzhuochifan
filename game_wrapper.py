#!/usr/bin/env python3
"""Operit plugin wrapper"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_engine import MarketGame

def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("?")
        return
    instruction = " ".join(sys.argv[1:]).strip()
    g = MarketGame()
    result = g.cmd(instruction)
    g.save()
    print(result)

if __name__ == "__main__":
    main()
