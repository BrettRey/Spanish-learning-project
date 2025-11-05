"""
Speech Processing MCP Server Implementation

Provides MCP tools for speech-to-text (ASR) and text-to-speech (TTS).
"""

import logging
import speech_recognition as sr
import pyttsx3
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SpeechServerError(Exception):
    """Base exception for Speech Server errors."""
    pass

class SpeechServer:
    """
    Speech Processing MCP Server

    Exposes two main tools:
    1. speech.recognize_from_mic: Capture audio from the microphone and return the recognized text.
    2. speech.synthesize_to_file: Convert text to speech and save it as an audio file.
    """

    def __init__(self):
        """
        Initialize the Speech Server.
        """
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        logger.info("SpeechServer initialized.")

    def recognize_from_mic(self) -> str:
        """
        MCP Tool: speech.recognize_from_mic

        Captures audio from the microphone and returns the recognized text.

        Returns:
            JSON string containing the recognized text.
        """
        try:
            with sr.Microphone() as source:
                logger.info("Listening for audio...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source)

            logger.info("Recognizing speech...")
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized text: {text}")

            result = {
                "text": text
            }
            return json.dumps(result, indent=2)

        except sr.UnknownValueError:
            logger.error("Google Speech Recognition could not understand audio")
            raise SpeechServerError("Could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            raise SpeechServerError(f"Speech service request failed: {e}")
        except Exception as e:
            logger.error(f"Error in recognize_from_mic: {e}")
            raise SpeechServerError(f"Failed to recognize speech: {e}")

    def synthesize_to_file(self, text: str, filepath: str) -> str:
        """
        MCP Tool: speech.synthesize_to_file

        Converts text to speech and saves it as an audio file.

        Args:
            text: The text to synthesize.
            filepath: The path to save the audio file.

        Returns:
            JSON string containing the status and filepath.
        """
        try:
            logger.info(f"Synthesizing text to file: {filepath}")
            self.tts_engine.save_to_file(text, filepath)
            self.tts_engine.runAndWait()

            result = {
                "success": True,
                "filepath": filepath
            }
            logger.info(f"Successfully synthesized text to {filepath}")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in synthesize_to_file: {e}")
            raise SpeechServerError(f"Failed to synthesize speech: {e}")

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns MCP tool definitions for registration.
        """
        return [
            {
                "name": "speech.recognize_from_mic",
                "description": "Capture audio from the microphone and return the recognized text.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "speech.synthesize_to_file",
                "description": "Convert text to speech and save it as an audio file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to synthesize."
                        },
                        "filepath": {
                            "type": "string",
                            "description": "The path to save the audio file."
                        }
                    },
                    "required": ["text", "filepath"]
                }
            }
        ]
