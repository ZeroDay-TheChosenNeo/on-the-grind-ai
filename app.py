"""
On The Grind AI - Production Voice Agent
LiveKit + Deepgram (STT) + Claude Haiku (LLM) + Cartesia (TTS)
"""

import os
import logging
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    voice,
)
from livekit.plugins import deepgram, cartesia, anthropic
from fastapi import FastAPI
import uvicorn
from threading import Thread

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app for Railway health checks
app = FastAPI()

@app.get("/")
@app.get("/health")
async def health():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "on-the-grind-ai"}

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
    """Main entrypoint for voice agent"""
    
    logger.info(f"🎙️ Starting voice agent for room: {ctx.room.name}")
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Create voice agent
    agent = voice.Agent(
        vad=agents.vad.silero.VAD.load(),
        stt=deepgram.STT(model="nova-2", language="el"),
        llm=anthropic.LLM(model="claude-3-haiku-20240307"),
        tts=cartesia.TTS(
            voice=os.getenv("CARTESIA_VOICE_ID"),
            language="el"
        ),
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=SYSTEM_PROMPT
        )
    )
    
    # Start agent
    agent.start(ctx.room)
    
    # Wait for participant
    participant = await ctx.wait_for_participant()
    logger.info(f"📞 Participant joined: {participant.identity}")
    
    # Start conversation
    await agent.say("Γεια σου! Καλώς ήρθες στο On The Grind. Πώς μπορώ να σε βοηθήσω;")
    
    logger.info("✅ Voice agent active")


if __name__ == "__main__":
    # Start health server in background
    def run_health_server():
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")), log_level="info")
    
    health_thread = Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("✅ Health server started on port 8080")
    
    # Run LiveKit agent
    logger.info("🎙️ Starting LiveKit agent worker...")
    cli.run_app(WorkerOptions(
        agent_name=os.getenv("AGENT_NAME", "on-the-grind-ai"),entrypoint_fnc=entrypoint))
        entrypoint_fnc=entrypoint
    ))
