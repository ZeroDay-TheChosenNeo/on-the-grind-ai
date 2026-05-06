import os
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents import voice
from livekit.plugins import deepgram, cartesia, anthropic, silero
from livekit import api as livekit_api
from livekit.api import WebhookReceiver
from fastapi import FastAPI, Request, Response
import uvicorn
from threading import Thread

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
AGENT_NAME = os.getenv("AGENT_NAME", "on-the-grind-ai")

app = FastAPI()

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/livekit/webhook")
async def livekit_webhook(request: Request):
    body = await request.body()
    auth_header = request.headers.get("Authorization", "")
    
    try:
        receiver = WebhookReceiver(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        event = receiver.receive(body.decode(), auth_header)
        
        if event.HasField("room_started"):
            room_name = event.room_started.room.name
            logger.info(f"Room started: {room_name}")
            
            # Dispatch agent to any SIP-created room
            if room_name.startswith("sip-"):
                logger.info(f"SIP room detected, dispatching agent to {room_name}")
                asyncio.create_task(_dispatch_agent(room_name))
                
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    
    return {"ok": True}

async def _dispatch_agent(room_name: str):
    try:
        lk = livekit_api.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )
        
        dispatch = await lk.agent_dispatch.create_dispatch(
            livekit_api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
            )
        )
        
        logger.info(f"Agent dispatched: {dispatch.id} to room {room_name}")
        await lk.aclose()
        
    except Exception as e:
        logger.error(f"Failed to dispatch agent: {e}")

# OPTIMIZED SYSTEM PROMPT WITH STRUCTURED FLOW
INSTRUCTIONS = """Είσαι η ψηφιακή γραμματέας του "On The Grind", premium barbershop στη Θεσσαλονίκη, Αριστοτέλους 31. Τηλέφωνο: 6934354652.

ΣΗΜΕΡΙΝΗ ΗΜΕΡΟΜΗΝΙΑ: Τρίτη, 29 Απριλίου 2026

ΩΡΑΡΙΟ: Δευτέρα-Σάββατο 10:00-21:00, Κυριακή κλειστά

═══════════════════════════════════════════
ΥΠΟΧΡΕΩΤΙΚΗ ΣΕΙΡΑ ΕΝΕΡΓΕΙΩΝ - ΑΚΟΛΟΥΘΗΣΕ ΑΚΡΙΒΩΣ
═══════════════════════════════════════════

ΒΗΜΑ 1 - ΧΑΙΡΕΤΙΣΜΟΣ:
Πες ΜΟΝΟ: "On The Grind, παρακαλώ;"
(Προσοχή: "On The Grind" = ΑΓΓΛΙΚΗ προφορά, "ον δε γκράιντ")

ΒΗΜΑ 2 - ΑΚΟΥΣΕ:
Ο πελάτης θα πει τι θέλει. ΜΗ διακόψεις.

ΒΗΜΑ 3 - ΡΩΤΑ ΗΜΕΡΑ:
"Ποια μέρα σας βολεύει;"
Περίμενε απάντηση. Αν πει "αύριο" ή "μεθαύριο", μετέτρεψε σε συγκεκριμένη μέρα της εβδομάδας.
Παράδειγμα: "αύριο" → "Τετάρτη"

ΒΗΜΑ 4 - ΕΝΗΜΕΡΩΣΕ ΔΙΑΘΕΣΙΜΕΣ ΩΡΕΣ:
Πες: "Έχουμε διαθέσιμο από τις δέκα το πρωί έως τις εννέα το βράδυ. Τι ώρα σας βολεύει;"
Περίμενε ΣΥΓΚΕΚΡΙΜΕΝΗ ωρα (π.χ. "έξι το απόγευμα", "δέκα το πρωί").
ΜΗ δεχτείς "μεσημέρι" ή "απόγευμα" - ρώτα: "Τι ώρα ακριβώς;"

ΒΗΜΑ 5 - ΡΩΤΑ ΕΙΔΟΣ ΚΟΥΡΕΜΑΤΟΣ:
Πες: "Τι είδους κούρεμα θέλετε;"
ΜΗ πεις τις επιλογές ΕΚΤΟΣ αν ρωτήσει "τι έχετε;" ή "τι είδη υπάρχουν;"

ΑΝ ΡΩΤΗΣΕΙ ΤΙ ΕΧΟΥΜΕ (ΜΟΝΟ ΤΟΤΕ):
"Έχουμε Fade κούρεμα δεκαπέντε ευρώ, Fade με ψαλίδι δεκαοκτώ ευρώ, Fade με γενειάδα είκοσι δύο ευρώ, μόνο γενειάδα δέκα ευρώ, styling δώδεκα ευρώ, και παιδικό δώδεκα ευρώ."

ΔΙΑΡΚΕΙΕΣ (ΣΗΜΑΝΤΙΚΟ - ΓΙΑ CALENDAR):
- Fade κούρεμα: 30 λεπτά
- Fade με ψαλίδι: 35 λεπτά
- Fade με γενειάδα: 40 λεπτά
- Μόνο γενειάδα: 20 λεπτά
- Styling: 25 λεπτά
- Παιδικό: 25 λεπτά

ΒΗΜΑ 6 - ΠΑΡΕ ΟΝΟΜΑ:
"Σε τι όνομα;"
Περίμενε απάντηση.

ΒΗΜΑ 7 - ΕΠΙΒΕΒΑΙΩΣΗ ΚΑΙ ΚΛΕΙΣΙΜΟ:
Πες ΜΙΑ φυσική πρόταση με ΟΛΑ τα στοιχεία:
"Τέλεια! Σου κλείνω ραντεβού για [ΕΙΔΟΣ ΚΟΥΡΕΜΑΤΟΣ] την [ΜΕΡΑ] στις [ΩΡΑ] στο όνομα [ΟΝΟΜΑ]. Θα σε περιμένουμε!"

Παράδειγμα: "Τέλεια! Σου κλείνω ραντεβού για Fade κούρεμα την Τετάρτη στις έξι το απόγευμα στο όνομα Γιάννη. Θα σε περιμένουμε!"

Μετά πες: "Καλή σου μέρα!" και τέλος.

═══════════════════════════════════════════
ΚΑΝΟΝΕΣ ΓΛΩΣΣΑΣ
═══════════════════════════════════════════

- Μιλάς ΠΑΝΤΑ ελληνικά
- "On The Grind" = Αγγλική προφορά
- Μέρες: "Δευτέρα", "Τρίτη", "Τετάρτη" (όχι "δευτέρα", "τρίτα")
- Ώρες: Πάντα συγκεκριμένες (όχι "μεσημέρι" ή "απόγευμα")
- ΜΙΑ ερώτηση τη φορά
- Σύντομες απαντήσεις
- ΜΗ επαναλάβεις την ίδια ερώτηση πάνω από μία φορά
- Επιβεβαίωση = ΜΙΑ πρόταση με ΟΛΑ τα στοιχεία"""

async def entrypoint(ctx: JobContext):
    logger.info("Job received, connecting to room")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Extract caller phone number from SIP room name
    # Format: sip-_+306944169406_WuoNKcxjn5z9
    caller_phone = None
    if ctx.room.name.startswith("sip-"):
        parts = ctx.room.name.split("_")
        if len(parts) >= 2:
            caller_phone = parts[1]  # +306944169406
            logger.info(f"📞 Caller phone extracted: {caller_phone}")
    
    session = voice.AgentSession(
        vad=silero.VAD.load(
            min_silence_duration=0.5,  # FIXED: 500ms silence = end of speech (was default 1.0s)
            activation_threshold=0.5,   # FIXED: More sensitive detection
            prefix_padding_duration=0.2,  # FIXED: Less padding for faster response
        ),
        stt=deepgram.STT(model="nova-2", language="el"),
        llm=anthropic.LLM(model="claude-haiku-4-5"),
        tts=cartesia.TTS(
            voice=os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091"),
            language="el",
            speed=1.1,
        ),
    )
    
    agent = voice.Agent(instructions=INSTRUCTIONS)
    await session.start(agent=agent, room=ctx.room)
    
    logger.info("Session started, saying greeting")
    await session.say("On The Grind, παρακαλώ;")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=port),
        daemon=True
    ).start()
    
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name=AGENT_NAME,
    ))
