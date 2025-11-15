import openai
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Transcribe an audio file using OpenAI Whisper and save to a .txt "
                                                 "file.")
    parser.add_argument("audio_file_path", help="Path to your audio file (e.g., output.wav)")
    args = parser.parse_args()

    audio_file_path = args.audio_file_path
    txt_file_path = os.path.splitext(audio_file_path)[0] + ".txt"

    with open(audio_file_path, "rb") as audio_file:
        transcription = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    print("Transcribed text:\n", transcription.text)
    with open(txt_file_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(transcription.text)
    print(f"Transcription saved to {txt_file_path}")

if __name__ == "__main__":
    main()
