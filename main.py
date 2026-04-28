"""
On The Grind AI - Production Voice Agent
LiveKit + Deepgram (STT) + Claude Haiku (LLM) + Cartesia (TTS)
"""

import os
import logging
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, cartesia, anthropic
from livekit import rtc

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Greek system prompt
SYSTEM_PROMPT = """Είσαι η Νίκη, η ψηφιακή γραμματέας του "On The Grind", ενός premium barbershop στη Θεσσαλονίκη, στην Αριστοτέλους 31. Τηλέφωνο: 6934354652.

Η σημερινή ημερομηνία είναι: 28 Απριλίου 2026, Δευτέρα.

ΧΑΡΑΚΤΗΡΑΣ:
Μιλάς σύντομα και φυσικά σαν άνθρωπος. Μία ερώτηση τη φορά. Ποτέ επαναλήψεις.

ΩΡΑΡΙΟ:
Δευτέρα έως Σάββατο, από τις δέκα το πρωί έως τις εννέα το βράδυ. Κυριακή κλειστά.

ΥΠΗΡΕΣΙΕΣ:
- Κούρεμα Fade: δεκαπέντε ευρώ
- Κούρεμα Fade με ψαλίδι: δεκαοκτώ ευρώ
- Κούρεμα Fade με γενειάδα: είκοσι δύο ευρώ
- Μόνο γενειάδα: δέκα ευρώ
- Styling: δώδεκα ευρώ
- Παιδικό: δώδεκα ευρώ

ΚΡΑΤΗΣΗ ΡΑΝΤΕΒΟΥ:
Πληροφορίες που χρειάζεσαι: υπηρεσία, ημερομηνία, ώρα, όνομα.
Μόλις τα έχεις όλα, επιβεβαίωσε και τελείωσε.

ΚΑΝΟΝΕΣ:
- Μιλάς ΠΑΝΤΑ στα Ελληνικά
- Ώρες και τιμές με λόγια
- Αν ρωτηθείς αν είσαι AI: "Είμαι ο ψηφιακός βοηθός του On The Grind"
"""


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint - called when someone calls the phone number
    """
    
    logger.info(f"🎙️ New call connected to room: {ctx.room.name}")
    
    # Connect to LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Configure STT (Speech-to-Text) - Deepgram Nova-2 Greek
    stt = deepgram.STT(
        model="nova-2",
        language="el",  # Greek
    )
    
    # Configure LLM - Claude Haiku
    llm_instance = anthropic.LLM(
        model="claude-3-haiku-20240307",
    )
    
    # Configure TTS (Text-to-Speech) - Cartesia Greek voice
    tts = cartesia.TTS(
        voice=os.getenv("CARTESIA_VOICE_ID"),  # Greek voice from env
        language="el",
    )
    
    # Create voice assistant
    assistant = VoiceAssistant(
        vad=rtc.VAD.from_silence_detector(),
        stt=stt,
        llm=llm_instance,
        tts=tts,
        chat_ctx=llm.ChatContext(
            messages=[
                llm.ChatMessage(
                    role="system",
                    content=SYSTEM_PROMPT,
                )
            ]
        ),
    )
    
    # Start assistant
    assistant.start(ctx.room)
    
    # Wait for caller
    participant = await ctx.wait_for_participant()
    logger.info(f"📞 Caller connected: {participant.identity}")
    
    # Greet caller in Greek
    await assistant.say("Γεια σου! Καλώς ήρθες στο On The Grind. Πώς μπορώ να σε βοηθήσω;")
    
    logger.info("✅ Voice assistant active and listening")


if __name__ == "__main__":
    # Run LiveKit agent worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        ),
    )