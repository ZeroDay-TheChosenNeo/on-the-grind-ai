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

# NEW OPTIMIZED SYSTEM PROMPT
INSTRUCTIONS = """Είσαι η ψηφιακή γραμματέας του "On The Grind", ενός premium barbershop στη Θεσσαλονίκη, στην Αριστοτέλους 31. Τηλέφωνο: 6934354652.

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
- Επιβεβαίωση = ΜΙΑ φυσική πρόταση"""

async def entrypoint(ctx: JobContext):
    logger.info("Job received, connecting to room")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    session = voice.AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2", language="el"),
        llm=anthropic.LLM(model="claude-haiku-4-5"),
        tts=cartesia.TTS(
            voice=os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091"),
            language="el",
            speed=0.95,  # CHANGED: Slower for clarity (was default 1.0)
        ),
    )
    
    agent = voice.Agent(instructions=INSTRUCTIONS)
    await session.start(agent=agent, room=ctx.room)
    
    logger.info("Session started, saying greeting")
    # NEW GREETING MESSAGE
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
