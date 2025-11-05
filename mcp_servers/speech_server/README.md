# Speech Server

This server provides MCP tools for speech-to-text (ASR) and text-to-speech (TTS) functionality.

## Tools

### `speech.recognize_from_mic()`

Captures audio from the microphone and returns the recognized text.

**Example Usage:**

```bash
python -m mcp_servers.speech_server recognize
```

**Example Output:**

```json
{
  "text": "hello world"
}
```

### `speech.synthesize_to_file(text: str, filepath: str)`

Converts text to speech and saves it as an audio file.

**Arguments:**

*   `text` (str): The text to synthesize.
*   `filepath` (str): The path to save the audio file.

**Example Usage:**

```bash
python -m mcp_servers.speech_server synthesize "hello world" hello.mp3
```

**Example Output:**

```json
{
  "success": true,
  "filepath": "hello.mp3"
}
```
