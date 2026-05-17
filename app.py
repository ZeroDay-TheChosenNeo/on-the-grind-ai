import os
import logging
import asyncio
from datetime import datetime
import locale
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

DAYS_GR = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]
MONTHS_GR = ["", "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
             "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου"]

def get_instructions():
    now = datetime.now()
    day_name = DAYS_GR[now.weekday()]
    date_str = f"{day_name}, {now.day} {MONTHS_GR[now.month]} {now.year}"
    is_sunday = now.weekday() == 6
    tomorrow = DAYS_GR[(now.weekday() + 1) % 7]
    
    sunday_note = ""
    if is_sunday:
        sunday_note = "ΣΗΜΑΝΤΙΚΟ: Σήμερα είναι Κυριακή, είμαστε ΚΛΕΙΣΤΑ. Αν ρωτήσει για σήμερα, πες: 'Σήμερα Κυριακή δεν δουλεύουμε, αλλά μπορώ να σου κλείσω για αύριο Δευτέρα αν θες!'"
    
    return f"""Είσαι η Νίκη, γραμματέας του κομμωτηρίου "On The Grind" στη Θεσσαλονίκη, Αριστοτέλους 31.

ΣΗΜΕΡΑ: {date_str}
ΩΡΑΡΙΟ: Δευτέρα-Σάββατο 10:00-21:00, Κυριακή κλειστά

ΥΠΗΡΕΣΙΕΣ:
- Fade κούρεμα: 15ε (30 λεπτά)
- Fade με ψαλίδι: 18ε (35 λεπτά)
- Fade με γένια: 22ε (40 λεπτά)
- Μόνο γένια: 10ε (20 λεπτά)
- Styling: 12ε (25 λεπτά)
- Παιδικό: 12ε (25 λεπτά)

ΠΩΣ ΜΙΛΑΣ:
- Μιλάς σαν φυσικός άνθρωπος, όχι σαν ρομπότ
- Σύντομες, ζεστές απαντήσεις
- ΜΙΑ ερώτηση τη φορά
- ΜΗΝ επαναλαμβάνεις ερωτήσεις που ήδη απάντησε ο πελάτης
- Αν ο πελάτης σου πει πολλά μαζί (π.χ. "θέλω fade αύριο στις 6"), μην τα ξαναρωτάς - πήγαινε κατευθείαν σε ό,τι λείπει

ΡΟΗ ΚΡΑΤΗΣΗΣ:
Χρειάζεσαι 4 πράγματα: υπηρεσία, μέρα, ώρα, όνομα.
Ρώτα μόνο ό,τι δεν έχει ήδη πει ο πελάτης. Η σειρά δεν είναι αυστηρή - ακολούθησε τη φυσική ροή της συζήτησης.

{sunday_note}

ΚΑΝΟΝΕΣ:
- "αύριο" = {tomorrow}
- Αν πει "μεσημέρι" ή "απόγευμα" χωρίς ώρα, ρώτα φιλικά: "Τι ώρα περίπου;"
- ΜΗΝ λες τις υπηρεσίες εκτός αν ρωτήσει "τι έχετε;"
- Μίλα ΠΑΝΤΑ ελληνικά
- "On The Grind" προφέρεται αγγλικά

ΕΠΙΒΕΒΑΙΩΣΗ:
Όταν έχεις και τα 4, πες κάτι σαν:
"Ωραία! Σε έχω για [κούρεμα], [μέρα] στις [ώρα], στο όνομα [όνομα]. Σε περιμένουμε!"
Μετά: "Καλή σου μέρα!" και ΤΕΛΟΣ - μη λες τίποτα άλλο.
Αν πει "ευχαριστώ" μετά, απάντα μόνο "Γεια!" και τίποτα άλλο.

ΤΗΛΕΦΩΝΟ ΚΑΤΑΣΤΗΜΑΤΟΣ: 6934354652 (αν χρειαστεί)"""

async def _hangup_room(ctx: JobContext):
    try:
        lk = livekit_api.LiveKitAPI(
            url=LIVEKIT_URL,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )
        await lk.room.delete_room(livekit_api.DeleteRoomRequest(room=ctx.room.name))
        logger.info(f"Room {ctx.room.name} deleted - call ended")
        await lk.aclose()
    except Exception as e:
        logger.error(f"Hangup error: {e}")

async def entrypoint(ctx: JobContext):
    logger.info("Job received, connecting to room")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    caller_phone = None
    if ctx.room.name.startswith("sip-"):
        parts = ctx.room.name.split("_")
        if len(parts) >= 2:
            caller_phone = parts[1]
            logger.info(f"Caller phone extracted: {caller_phone}")
    
    session = voice.AgentSession(
        vad=silero.VAD.load(
            min_silence_duration=0.3,
            activation_threshold=0.45,
            prefix_padding_duration=0.15,
        ),
        stt=deepgram.STT(model="nova-2", language="el"),
        llm=anthropic.LLM(model="claude-haiku-4-5"),
        tts=cartesia.TTS(
            voice=os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091"),
            language="el",
            speed=1.15,
        ),
    )
    
    agent = voice.Agent(instructions=get_instructions())
    await session.start(agent=agent, room=ctx.room)
    
    logger.info("Session started, saying greeting")
    await session.say("On The Grind, παρακαλώ;")
    
    @session.on("agent_speech_committed")
    def _check_hangup(msg):
        text = msg.content if hasattr(msg, 'content') else str(msg)
        if "καλή σου μέρα" in text.lower():
            logger.info("Goodbye detected, hanging up in 2s")
            asyncio.get_event_loop().call_later(2.0, lambda: asyncio.ensure_future(_hangup_room(ctx)))

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
