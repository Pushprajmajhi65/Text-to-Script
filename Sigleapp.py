from flask import Flask, request, send_file, jsonify
from gtts import gTTS
import os
import time
import io
import re

app = Flask(__name__)

# ====== Setup for TTS ======
SAVE_FOLDER = os.path.join(os.getcwd(), "audio_files")
os.makedirs(SAVE_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return "✅ Flask TTS and SRT service is running!"

@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text')
    filename = data.get('filename', 'speech.mp3')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    output_path = os.path.join(SAVE_FOLDER, filename)

    try:
        tts = gTTS(text=text, lang='en')
        tts.save(output_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    time.sleep(0.3)  # Ensure file is ready

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        return jsonify({"error": "Audio file not created properly"}), 500

    return send_file(
        output_path,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=filename
    )

# ====== Setup for SRT Generation ======
WORDS_PER_SECOND = 4.0

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

def generate_srt(script, wps=WORDS_PER_SECOND):
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    srt_output = ""
    current_time = 0.0
    index = 1

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        word_count = len(sentence.split())
        duration = word_count / wps
        start_time = format_timestamp(current_time)
        end_time = format_timestamp(current_time + duration)
        srt_output += f"{index}\n{start_time} --> {end_time}\n{sentence}\n\n"
        current_time += duration
        index += 1

    return srt_output.strip()

@app.route("/generate-srt", methods=["POST"])
def generate_srt_file():
    data = request.get_json()
    if not data or "script" not in data or "filename" not in data:
        return jsonify({"error": "Missing 'script' or 'filename'"}), 400

    script = data["script"]
    filename = data["filename"].strip()
    if not filename.endswith(".srt"):
        filename += ".srt"

    srt_content = generate_srt(script)

    file_stream = io.BytesIO(srt_content.encode("utf-8"))
    file_stream.seek(0)

    return send_file(
        file_stream,
        mimetype="application/x-subrip",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)