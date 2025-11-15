## Mic → Text → MP3

### 1) Record (browser)
```bash
/usr/bin/env bash -lc 'cd /home/gleb/code/juction/speech && python3 -m http.server 8000'
```
Open `http://localhost:8000/`, press and hold Record; a `.webm`/`.ogg` downloads.

### 2) Transcribe (.webm→ .txt)
```bash
python3 /home/gleb/code/juction/speech/transcribe.py /path/to/recording-input-...webm
```
Outputs `/path/to/recording-input-...txt`.

### 3) TTS (.txt → .mp3)
```bash
python3 /home/gleb/code/juction/speech/tts.py /path/to/recording-input-...txt
```
Outputs `/path/to/recording-input-....mp3`.