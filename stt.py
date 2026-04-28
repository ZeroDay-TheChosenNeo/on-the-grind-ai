import os
from deepgram import DeepgramClient

deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))

def transcribe_file(path: str) -> str:
    with open(path, "rb") as audio:
        buffer_data = audio.read()

    payload = {"buffer": buffer_data}

    options = {
        "model": "nova-2",
        "language": "el"
    }

    response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
    return response["results"]["channels"][0]["alternatives"][0]["transcript"]
