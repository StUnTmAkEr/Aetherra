#!/usr/bin/env python3
"""
Neuroplex - AI-Native Programming Language
Main entry point for the Neuroplex interpreter
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.interpreter import NeuroCodeInterpreter

def main():
    """Main entry point for Neuroplex"""
    print("🧠 Neuroplex - AI-Native Programming Language")
    print("=" * 50)
    print("Type commands or 'help' for assistance")
    print("Type 'exit' or press Ctrl+C to quit")
    print("=" * 50)
    
    interpreter = NeuroCodeInterpreter()
    
    while True:
        try:
            try:
                code = input("🔮 >> ")
            except EOFError:
                print("\n🚀 Input stream closed. Thanks for using Neuroplex!")
                break
                
            if code.lower() in ["exit", "quit", "q"]:
                print("🚀 Thanks for using Neuroplex!")
                break
            elif code.lower() in ["help", "?"]:
                print("""
📋 Neuroplex Commands:
  remember('text') as 'tag'    - Store memory with tag
  recall tag: 'tag'            - Recall memories by tag
  memory summary               - Show memory statistics
  define func() ... end        - Define function
  run func()                   - Execute function
  agent goal: 'description'    - Set AI agent goal
  simulate ... end             - Simulation mode
  help                         - Show this help
  exit                         - Quit interpreter
                """)
                continue
            elif code.strip() == "":
                continue
            
            interpreter.execute(code)
        except KeyboardInterrupt:
            print("\n🚀 Thanks for using Neuroplex!")
            break
        except Exception as e:
            print(f"❌ [Error] {e}")

if __name__ == "__main__":
    main()