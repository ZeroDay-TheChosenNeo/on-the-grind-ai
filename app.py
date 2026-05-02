"""
On The Grind AI - Production Voice Agent (OPTIMIZED)
LiveKit + Deepgram Nova-2 (STT) + Claude Haiku (LLM) + Cartesia (TTS)
Cost-optimized for Greek market while maintaining quality
"""

import os
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents import voice
from livekit.plugins import deepgram, cartesia, anthropic, silero
from livekit import rtc
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

# Greek system prompt - optimized for natural conversation
SYSTEM_PROMPT = """Είσαι η ψηφιακή γραμματέας του "On The Grind", ενός premium barbershop στη Θεσσαλονίκη, στην Αριστοτέλους 31. Τηλέφωνο: 6934354652.

Η σημερινή ημερομηνία είναι: 28 Απριλίου 2026, Δευτέρα.

ΧΑΡΑΚΤΗΡΑΣ:
Μιλάς σύντομα και φυσικά σαν άνθρωπος. Μία ερώτηση τη φορά. Ποτέ επαναλήψεις.

ΧΑΙΡΕΤΙΣΜΟΣ:
Όταν απαντάς την κλήση, πες: "Ον δε Γκράιντ, παρακαλώ;"
(Προσοχή: Πες το "On The Grind" με ΑΓΓΛΙΚΗ προφορά, όχι ελληνική!)

ΩΡΑΡΙΟ:
Δευτέρα έως Σάββατο, από τις δέκα το πρωί έως τις εννέα το βράδυ. Κυριακή κλειστά.

ΥΠΗΡΕΣΙΕΣ - ΣΗΜΑΝΤΙΚΟ:
ΜΗ λες ΠΟΤΕ τις υπηρεσίες ΕΚΤΟΣ αν:
- Ο πελάτης ρωτήσει ρητά "τι υπηρεσίες έχετε;" ή "τι κάνετε;"
- Ο πελάτης πει "δεν ξέρω τι θέλω" ή "τι μου προτείνετε;"

Αν λέει "θέλω κούρεμα" ή "θέλω ραντεβού" → ΜΗΝ πεις τις υπηρεσίες!
Απλά ρώτα: "Ποια μέρα σας βολεύει;"

Όταν ΠΡΕΠΕΙ να πεις τις υπηρεσίες (μόνο όταν ρωτηθείς):
"Έχουμε κούρεμα Fade δεκαπέντε ευρώ, Fade με ψαλίδι δεκαοκτώ ευρώ, Fade με γενειάδα είκοσι δύο ευρώ, μόνο γενειάδα δέκα ευρώ, styling δώδεκα ευρώ, και παιδικό δώδεκα ευρώ."

ΚΡΑΤΗΣΗ ΡΑΝΤΕΒΟΥ:
Πληροφορίες που χρειάζεσαι: ημερομηνία, ώρα, όνομα.
Μόλις τα έχεις όλα, επιβεβαίωσε με ΦΥΣΙΚΗ ΠΡΟΤΑΣΗ.

Παράδειγμα: "Τέλεια! Σου κλείνω ραντεβού για κούρεμα αύριο στις πέντε το απόγευμα στο όνομα σου. Θα σε περιμένουμε!"

ΚΑΝΟΝΕΣ:
- Μιλάς ΠΑΝΤΑ στα Ελληνικά
- "On The Grind" = Αγγλική προφορά (όπως "ον δε γκράιντ")
- ΜΗ λες υπηρεσίες αν δεν ρωτηθείς
- Επιβεβαίωση = ΜΙΑ φυσική πρόταση
"""


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint - called when someone calls the phone number
    """
    
    logger.info(f"🎙️ New call connected to room: {ctx.room.name}")
    
    # Connect to LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Configure STT (Speech-to-Text) - Deepgram Nova-2 Greek (better accuracy)
    stt = deepgram.STT(
        model="nova-2",  # Better accuracy: 8.4% WER vs Base 12% WER
        language="el",  # Greek
    )
    
    # Configure LLM - Claude Haiku (BEST for Greek)
    llm_instance = anthropic.LLM(
        model="claude-3-haiku-20240307",
        temperature=0.2,  # Fast & consistent responses
    )
    
    # Configure TTS (Text-to-Speech) - Cartesia Greek voice with optimizations
    tts = cartesia.TTS(
        voice=os.getenv("CARTESIA_VOICE_ID"),  # Greek voice from env
        language="el",  # Greek
        speed=0.95,  # Slightly slower for clarity (was 1.1 - too fast for lists)
        emotion=["positivity:low"],  # Friendly but professional
    )
    
    
    
    
        
        
        
   
    
    # Create voice assistant
    assistant = voice.VoiceSession(
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
    
   
    
    
    # Wait for caller
    participant = await ctx.wait_for_participant()
    logger.info(f"📞 Caller connected: {participant.identity}")

    # Start assistant
    session = await assistant.astart(ctx.room)

    
    # Greet caller with new greeting
    await assistant.say("On The Grind, παρακαλώ;")
    
    logger.info("✅ Voice assistant active and listening")


if __name__ == "__main__":
    # Start FastAPI health server in background thread
    def run_health_server():
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
    
    health_thread = Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("✅ Health server started on port 8080")
    
    # Run LiveKit agent worker (main process)
    logger.info("🎙️ Starting LiveKit voice agent worker...")
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="on-the-grind-ai",
        )
    )
