# =========================================================
# Step 1: Speech to Text  (from voice_of_the_patient.py)
# =========================================================

import base64
from io import BytesIO
import os

from PIL import Image
from groq import Groq


def transcribe_patient_voice(audio_file_path):
    groq_api_key = os.environ.get("GROQ_API_KEY")

    client = Groq(api_key=groq_api_key)

    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model=os.environ.get("WHISPER_MODEL", "whisper-large-v3")
        )

    return transcription.text


# =========================================================
# Step 2: Brain of the Doctor  (from brain_of_the_doctor_groq.py)
# =========================================================
def encode_image_for_groq(filepath):
    image = Image.open(filepath)
    image.thumbnail((1024, 1024))

    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")