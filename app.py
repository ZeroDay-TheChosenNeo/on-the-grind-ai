import os
import logging
import asyncio
import base64
import json
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents import voice
from livekit.plugins import deepgram, google, anthropic, silero
from livekit import api as livekit_api
from livekit.api import WebhookReceiver
from fastapi import FastAPI, Request
import uvicorn
from threading import Thread

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Decode Google credentials from base64 env var and write to temp file
GOOGLE_CREDS_B64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64")
if GOOGLE_CREDS_B64:
    creds_json = base64.b64decode(GOOGLE_CREDS_B64).decode('utf-8')
    creds_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    creds_file.write(creds_json)
    creds_file.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_file.name
    logger.info(f"Google credentials loaded from base64 to {creds_file.name}")

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
AGENT_NAME = os.getenv("AGENT_NAME", "on-the-grind-ai")
GOOGLE_TTS_VOICE = os.getenv("GOOGLE_TTS_VOICE", "el-GR-Wavenet-A")

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

DAYS_GR = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]
MONTHS_GR = ["", "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
             "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου"]

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
        status_line = f"ΠΡΟΣΟΧΗ: Σήμερα Κυριακή το μαγαζί είναι ΚΛΕΙΣΤΟ. Πρότεινε αύριο ({ctx['tomorrow_name']})."
    elif ctx["is_closed_hours"]:
        status_line = "ΠΡΟΣΟΧΗ: Το μαγαζί είναι κλειστό τώρα (ωράριο 10:00-21:00). Είσαι 24ωρη υπηρεσία — κλείνεις ραντεβού για επόμενες μέρες."
    
    return f"""Είσαι η Νίκη, η AI γραμματέας του barbershop "Όν Δε Γκράιντ" στη Θεσσαλονίκη (Αριστοτέλους 31).

ΧΡΟΝΟΣ (ώρα Ελλάδας):
Σήμερα: {ctx['date_str']}
Ώρα: {ctx['time_str']}
Αύριο: {ctx['tomorrow_name']}
Μεθαύριο: {ctx['day_after_name']}

ΩΡΑΡΙΟ: Δευτέρα-Σάββατο 10:00-21:00, Κυριακή κλειστά.

{status_line}

ΠΟΙΑ ΕΙΣΑΙ:
Η ψηφιακή φωνή του Όν Δε Γκράιντ. Δουλεύεις 24/7. Σηκώνεις κάθε κλήση. Στόχος: κάνεις τον πελάτη να νιώθει ότι μίλησε με κάποιον που ενδιαφέρεται προσωπικά.

Είσαι ζεστή, φιλική, αυθεντική, σύντομη, επαγγελματική αλλά όχι ψυχρή.

ΠΩΣ ΜΙΛΑΣ:
ΛΕΣ: "ωραία", "εντάξει", "βεβαίως", "καλώς", "ναι, ναι", "μάλιστα", "λοιπόν", "τέλεια", "άνετα"
ΔΕΝ ΛΕΣ: "Παρακαλώ ενημερώστε με", "Επιθυμητή ημερομηνία", "Θα σας εξυπηρετήσω"

Παραδείγματα:
- "Ωραία, πότε σε βολεύει να έρθεις;"
- "Άνετα, θα το κανονίσω."
- "Καλώς, σε ποιο όνομα να το γράψω;"

ΥΠΗΡΕΣΙΕΣ:
Fade: 15 ευρώ
Fade με ψαλίδι: 18 ευρώ
Fade με γένια: 22 ευρώ
Μόνο γένια: 10 ευρώ
Styling: 12 ευρώ
Παιδικό: 12 ευρώ

ΜΗΝ τις πεις αν δεν ρωτηθεί.

ΡΟΗ - χρειάζεσαι 4: υπηρεσία, μέρα, ώρα, όνομα.

ΧΡΟΝΟΣ:
"σήμερα" = {ctx['date_str']}
"αύριο" = {ctx['tomorrow_name']}
"μεθαύριο" = {ctx['day_after_name']}

Αν ο πελάτης πει πολλά μαζί, ΜΗΝ τα ξαναρωτήσεις. Ζήτα μόνο ό,τι λείπει.

ΑΝ ΧΑΣΕΙΣ: "Συγγνώμη, δεν σ' άκουσα καθαρά, μου το λες ξανά;"

ΕΠΙΒΕΒΑΙΩΣΗ:
"Λοιπόν, σε γράφω για [υπηρεσία] [μέρα] στις [ώρα], στο όνομα [όνομα]. Σε περιμένουμε!"
Μετά: "Καλή σου μέρα!" και σταμάτα.

ΓΛΩΣΣΑ:
- Πάντα ελληνικά
- "Όν Δε Γκράιντ" (ελληνική προφορά)
- Σύντομες προτάσεις (1-2 max)
- Τηλέφωνο: 6 9 3 4 3 5 4 6 5 2"""

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
            min_silence_duration=0.3,
            activation_threshold=0.45,
            prefix_padding_duration=0.15,
        ),
        stt=deepgram.STT(model="nova-2", language="el"),
        llm=anthropic.LLM(model="claude-haiku-4-5", temperature=0.7),
        tts=google.TTS(
            language="el-GR",
            voice_name=GOOGLE_TTS_VOICE,
            gender="female",
        ),
        min_endpointing_delay=0.5,
        max_endpointing_delay=3.0,
        allow_interruptions=True,
    )
    
    agent = voice.Agent(instructions=get_instructions())
    await session.start(agent=agent, room=ctx.room)
    
    logger.info("Saying greeting")
    await session.say("Γεια σου! Όν Δε Γκράιντ, πώς μπορώ να βοηθήσω;")
    
    @session.on("agent_speech_committed")
    def _check_hangup(msg):
        text = msg.content if hasattr(msg, 'content') else str(msg)
        if "καλή σου μέρα" in text.lower() or "καλη σου μερα" in text.lower():
            asyncio.get_event_loop().call_later(2.0, lambda: asyncio.ensure_future(_hangup_room(ctx)))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=port), daemon=True).start()
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=AGENT_NAME))
