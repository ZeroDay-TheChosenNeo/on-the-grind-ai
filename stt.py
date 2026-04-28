import os
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))

def transcribe_file(path: str) -> str:
    with open(path, "rb") as audio:
        payload: FileSource = {"buffer": audio.read()}

    options = PrerecordedOptions(
        model="nova-2",
        language="el"
    )

    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
    return response.results.channels[0].alternatives[0].transcript
