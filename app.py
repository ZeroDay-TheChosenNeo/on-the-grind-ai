import os
import logging
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents import voice
from livekit.plugins import deepgram, cartesia, anthropic, silero
from livekit import api as livekit_api
from livekit.api import WebhookReceiver
from fastapi import FastAPI, Request
import uvicorn
from threading import Thread

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
AGENT_NAME = os.getenv("AGENT_NAME", "on-the-grind-ai")
CARTESIA_VOICE_ID = os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091")

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
                asyncio.create_task(_dispatch_agent(room_name))
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"ok": True}

async def _dispatch_agent(room_name):
    try:
        lk = livekit_api.LiveKitAPI(url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
        dispatch = await lk.agent_dispatch.create_dispatch(
            livekit_api.CreateAgentDispatchRequest(agent_name=AGENT_NAME, room=room_name)
        )
        logger.info(f"Agent dispatched: {dispatch.id}")
        await lk.aclose()
    except Exception as e:
        logger.error(f"Dispatch error: {e}")

DAYS_GR = ["Δευτερα", "Τριτη", "Τεταρτη", "Πεμπτη", "Παρασκευη", "Σαββατο", "Κυριακη"]
MONTHS_GR = ["", "Ιανουαριου", "Φεβρουαριου", "Μαρτιου", "Απριλιου", "Μαιου", "Ιουνιου",
             "Ιουλιου", "Αυγουστου", "Σεπτεμβριου", "Οκτωβριου", "Νοεμβριου", "Δεκεμβριου"]

def get_time_context():
    tz = ZoneInfo("Europe/Athens")
    now = datetime.now(tz)
    day_idx = now.weekday()
    return {
        "date_str": f"{DAYS_GR[day_idx]}, {now.day} {MONTHS_GR[now.month]} {now.year}",
        "day_name": DAYS_GR[day_idx],
        "tomorrow_name": DAYS_GR[(day_idx + 1) % 7],
        "day_after_name": DAYS_GR[(day_idx + 2) % 7],
        "time_str": f"{now.hour}:{now.minute:02d}",
        "is_sunday": day_idx == 6,
        "is_closed_hours": now.hour < 10 or now.hour >= 21,
    }

def get_instructions():
    ctx = get_time_context()
    status_line = ""
    if ctx["is_sunday"]:
        status_line = f"ΠΡΟΣΟΧΗ: Σημερα Κυριακη το μαγαζι ειναι ΚΛΕΙΣΤΟ. Προτεινε αυριο ({ctx['tomorrow_name']})."
    elif ctx["is_closed_hours"]:
        status_line = "ΠΡΟΣΟΧΗ: Το μαγαζι ειναι κλειστο τωρα (ωραριο 10:00-21:00). Εισαι 24ωρη υπηρεσια — κλεινεις ραντεβου για επομενες μερες."
    
    return f"""Εισαι η Νικη, η AI γραμματεας του barbershop "Ον Δε Γκραιντ" στη Θεσσαλονικη (Αριστοτελους 31).

ΧΡΟΝΟΣ (ωρα Ελλαδας):
Σημερα: {ctx['date_str']}
Ωρα: {ctx['time_str']}
Αυριο: {ctx['tomorrow_name']}
Μεθαυριο: {ctx['day_after_name']}

ΩΡΑΡΙΟ: Δευτερα-Σαββατο 10:00-21:00, Κυριακη κλειστα.

{status_line}

ΠΟΙΑ ΕΙΣΑΙ:
Η ψηφιακη φωνη του Ον Δε Γκραιντ. Δουλευεις 24/7. Σηκωνεις καθε κληση. Στοχος: κανεις τον πελατη να νιωθει οτι μιλησε με καποιον που ενδιαφερεται προσωπικα.

Εισαι ζεστη, φιλικη, αυθεντικη, συντομη, επαγγελματικη αλλα οχι ψυχρη.

ΠΩΣ ΜΙΛΑΣ:
ΛΕΣ: "ωραια", "εντάξει", "βεβαιως", "καλως", "ναι, ναι", "μαλιστα", "λοιπον", "τελεια", "ανετα"
ΔΕΝ ΛΕΣ: "Παρακαλω ενημερωστε με", "Επιθυμητη ημερομηνια", "Θα σας εξυπηρετησω"

Παραδειγματα:
- "Ωραια, ποτε σε βολευει να ερθεις;"
- "Ανετα, θα το κανονισω."
- "Καλως, σε ποιο ονομα να το γραψω;"

ΥΠΗΡΕΣΙΕΣ:
Fade: 15 ευρω
Fade με ψαλιδι: 18 ευρω
Fade με γενια: 22 ευρω
Μονο γενια: 10 ευρω
Styling: 12 ευρω
Παιδικο: 12 ευρω

ΜΗΝ τις πεις αν δεν ρωτηθει.

ΡΟΗ - χρειαζεσαι 4: υπηρεσια, μερα, ωρα, ονομα.

ΧΡΟΝΟΣ:
"σημερα" = {ctx['date_str']}
"αυριο" = {ctx['tomorrow_name']}
"μεθαυριο" = {ctx['day_after_name']}

Αν ο πελατης πει πολλα μαζι, ΜΗΝ τα ξαναρωτησεις. Ζητα μονο ο,τι λειπει.

ΑΝ ΧΑΣΕΙΣ: "Συγγνωμη, δεν σ' ακουσα καθαρα, μου το λες ξανα;"

ΕΠΙΒΕΒΑΙΩΣΗ:
"Λοιπον, σε γραφω για [υπηρεσια] [μερα] στις [ωρα], στο ονομα [ονομα]. Σε περιμενουμε!"
Μετα: "Καλη σου μερα!" και σταμάτα.

ΓΛΩΣΣΑ:
- Παντα ελληνικα
- "Ον Δε Γκραιντ" (ελληνικη προφορα)
- Συντομες προτασεις (1-2 max)
- Τηλεφωνο: 6 9 3 4 3 5 4 6 5 2"""

async def _hangup_room(ctx):
    try:
        lk = livekit_api.LiveKitAPI(url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
        await lk.room.delete_room(livekit_api.DeleteRoomRequest(room=ctx.room.name))
        await lk.aclose()
    except Exception as e:
        logger.error(f"Hangup error: {e}")

async def entrypoint(ctx):
    logger.info("Job received")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    if ctx.room.name.startswith("sip-"):
        parts = ctx.room.name.split("_")
        if len(parts) >= 2:
            logger.info(f"Caller: {parts[1]}")
    
    tctx = get_time_context()
    logger.info(f"Context: {tctx['date_str']} {tctx['time_str']}")
    
    session = voice.AgentSession(
        vad=silero.VAD.load(
            min_silence_duration=0.25,
            activation_threshold=0.4,
            prefix_padding_duration=0.15,
        ),
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            keyterms=["fade", "κουρεμα", "γενια", "ραντεβου", "ψαλιδι", "styling",
                      "Δευτερα", "Τριτη", "Τεταρτη", "Πεμπτη", "Παρασκευη", "Σαββατο",
                      "αυριο", "σημερα", "μεθαυριο", "Ον Δε Γκραιντ"],
        ),
        llm=anthropic.LLM(model="claude-haiku-4-5", temperature=0.7),
        tts=cartesia.TTS(
            voice=CARTESIA_VOICE_ID,
            language="el",
        ),
        min_endpointing_delay=0.5,
        max_endpointing_delay=3.0,
        allow_interruptions=True,
    )
    
    agent = voice.Agent(instructions=get_instructions())
    await session.start(agent=agent, room=ctx.room)
    
    logger.info("Saying greeting")
    await session.say("Γεια σου! Ον Δε Γκραιντ, πως μπορω να βοηθησω;")
    
    @session.on("agent_speech_committed")
    def _check_hangup(msg):
        text = msg.content if hasattr(msg, 'content') else str(msg)
        if "καλη σου μερα" in text.lower() or "καλή σου μέρα" in text.lower():
            asyncio.get_event_loop().call_later(2.0, lambda: asyncio.ensure_future(_hangup_room(ctx)))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=port), daemon=True).start()
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=AGENT_NAME))
