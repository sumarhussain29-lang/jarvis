import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")

if not api_key:
    print("ERROR: ELEVENLABS_API_KEY nahi mili.")
    exit()

client = ElevenLabs(api_key=api_key)

audio = client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
    text="Hello Umar. I am JARVIS. Main aapse naturally baat kar sakta hoon."
)

print("JARVIS voice generating...")
play(audio)

print("Voice test complete.")