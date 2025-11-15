import openai
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Convert text file to speech and save as .webm file.")
    parser.add_argument("text_file", help="Path to the input text file")
    args = parser.parse_args()

    text_file_path = args.text_file
    base_name = os.path.splitext(text_file_path)[0]
    output_audio_path = base_name + ".mp3"

    # Read text from file
    with open(text_file_path, "r", encoding="utf-8") as f:
        text_to_speak = f.read()

    # TODO change voice
    audio_response = openai.audio.speech.create(
        model="tts-1",
        voice="alloy",  # or "aria", "copper", etc.
        input=text_to_speak,
    )

    with open(output_audio_path, "wb") as f:
        f.write(audio_response.read())
    print(f"TTS audio saved to {output_audio_path}")

if __name__ == "__main__":
    main()