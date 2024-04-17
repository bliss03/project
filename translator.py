from flask import Flask, request, jsonify, send_file
from io import BytesIO
import os
import threading
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator
from flask_cors import CORS
import time

app = Flask(__name__)  # Corrected line
CORS(app, origins=['http://127.0.0.1:5500'])
keep_running = False
audio_file = None
audio_ready = False  # Flag to indicate when audio file is ready

def update_translation(input_lang, output_lang):
    global keep_running, audio_file, audio_ready

    if keep_running:
        r = sr.Recognizer()

        with sr.Microphone() as source:
            print("Speak Now!\n")
            audio = r.listen(source)
            
            try:
                speech_text = r.recognize_google(audio, language=input_lang)
                print("You said:", speech_text)
                
                translated_text = GoogleTranslator(source=input_lang, target=output_lang).translate(speech_text)
                print("Translated Text:", translated_text)

                # Generate translated audio
                tts = gTTS(translated_text, lang=output_lang)
                audio_bytes = BytesIO()
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)
                audio_file = audio_bytes

                # Set the flag to indicate that audio file is ready
                audio_ready = True

                # Log a message when the audio file is generated
                print("Audio file generated successfully.")

            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))

            if keep_running:
                threading.Timer(0, update_translation, args=(input_lang, output_lang)).start()
            else:
                print("Translation stopped")

@app.route('/start_translation', methods=['POST'])
def start_translation():
    global keep_running, audio_ready
    if not keep_running:
        data = request.json
        input_lang = data.get('input_lang')
        output_lang = data.get('output_lang')
        if input_lang and output_lang:
            keep_running = True
            threading.Thread(target=update_translation, args=(input_lang, output_lang)).start()
            return jsonify({'message': 'Translation started successfully.'}), 200
        else:
            return jsonify({'error': 'Input and output languages are required.'}), 400
    else:
        return jsonify({'error': 'Translation is already running.'}), 400

@app.route('/get_audio', methods=['GET'])
def get_audio():
    global audio_file, audio_ready
    if audio_ready:
        audio_file.seek(0)
        return send_file(audio_file, mimetype='audio/mpeg', as_attachment=True, attachment_filename='translated_audio.mp3')
    else:
        return jsonify({'error': 'Audio file not available yet. Please try again later.'}), 404

@app.route('/stop_translation', methods=['POST'])
def stop_translation():
    global keep_running, audio_ready
    if keep_running:
        keep_running = False
        audio_ready = False  # Reset the audio ready flag
        return jsonify({'message': 'Translation stopped successfully.'}), 200
    else:
        return jsonify({'error': 'Translation is not running.'}), 400

if __name__ == '__main__':  # Corrected line
    app.run(debug=True)
