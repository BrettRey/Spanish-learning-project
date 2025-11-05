"""
Speech Server CLI

Provides a command-line interface for testing the SpeechServer tools.
"""

import argparse
import json
from server import SpeechServer

def main():
    parser = argparse.ArgumentParser(description="Speech Server CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # recognize command
    recognize_parser = subparsers.add_parser("recognize", help="Recognize speech from the microphone")

    # synthesize command
    synthesize_parser = subparsers.add_parser("synthesize", help="Synthesize text to an audio file")
    synthesize_parser.add_argument("text", help="The text to synthesize")
    synthesize_parser.add_argument("filepath", help="The path to save the audio file")

    args = parser.parse_args()

    server = SpeechServer()

    if args.command == "recognize":
        try:
            result = server.recognize_from_mic()
            print(json.dumps(json.loads(result), indent=2))
        except Exception as e:
            print(f"Error: {e}")

    elif args.command == "synthesize":
        try:
            result = server.synthesize_to_file(args.text, args.filepath)
            print(json.dumps(json.loads(result), indent=2))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
