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
                asyncio.create_task(_dispatch_agent(room_name))
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"ok": True}

async def _dispatch_agent(room_name: str):
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

def get_instructions():
    now = datetime.now()
    day_name = DAYS_GR[now.weekday()]
    date_str = f"{day_name}, {now.day} {MONTHS_GR[now.month]} {now.year}"
    is_sunday = now.weekday() == 6
    tomorrow = DAYS_GR[(now.weekday() + 1) % 7]
    
    sunday_context = ""
    if is_sunday:
        sunday_context = f"\n\nΠΡΟΣΟΧΗ: Σήμερα Κυριακή και το κομμωτήριο είναι κλειστό. Αν ζητήσει για σήμερα, εξήγησε φιλικά ότι δεν δουλεύουμε σήμερα και πρότεινε αύριο ({tomorrow})."
    
    return f"""Είσαι η Νίκη, η γραμματέας του barbershop "On The Grind" στη Θεσσαλονίκη (Αριστοτέλους 31).

Σήμερα είναι {date_str}.
Δουλεύουμε Δευτέρα με Σάββατο, 10 το πρωί μέχρι 9 το βράδυ. Κυριακή κλειστά.{sunday_context}

ΠΡΟΣΩΠΙΚΟΤΗΤΑ:
Μιλάς σαν ζεστή, φιλική κοπέλα που δουλεύει στο μαγαζί. Όχι σαν υπάλληλος call center. Όχι αυστηρή, όχι αποτομη. Χρησιμοποιείς φυσικά εκφράσεις: "εντάξει", "ωραία", "μάλιστα", "βεβαίως", "καλώς". Λες "ναι" αντί για "ναι, βεβαίως".

Παράδειγμα ύφους:
- ΟΧΙ: "Σας ευχαριστώ. Παρακαλώ ενημερώστε με για την επιθυμητή ημερομηνία."
- ΝΑΙ: "Ωραία! Πότε σε βολεύει να έρθεις;"

Δουλειά σου: κλείνεις ραντεβού. Χρειάζεσαι 4 πράγματα: τι κούρεμα, ποια μέρα, τι ώρα, τι όνομα. Ρώτα ΜΟΝΟ ό,τι λείπει. Αν σου πει στο πρώτο μήνυμα "θέλω fade αύριο στις 6", έχεις 3/4 — ζήτα μόνο όνομα. Μην ξαναρωτάς πράγματα που είπε ήδη.

ΥΠΗΡΕΣΙΕΣ (μόνο αν ρωτήσει):
- Fade: 15 ευρώ
- Fade με ψαλίδι: 18 ευρώ
- Fade με γένια: 22 ευρώ
- Μόνο γένια: 10 ευρώ
- Styling: 12 ευρώ
- Παιδικό: 12 ευρώ

Αν πει απλά "κούρεμα", υπέθεσε fade. Μπορείς να ρωτήσεις "Fade ή με γένια;" αν θες σιγουριά.

ΣΥΖΗΤΗΣΗ:
- Μία ερώτηση τη φορά
- Σύντομα, ζεστά
- Αν δεν ακούσεις καλά: "Συγγνώμη, δεν σ' άκουσα καθαρά, μπορείς να μου το πεις ξανά;"
- "αύριο" = {tomorrow}
- Αν δώσει αόριστη ώρα ("πρωί", "απόγευμα"), ρώτα "Τι ώρα σε βολεύει πιο πολύ;"

ΚΛΕΙΣΙΜΟ:
Επιβεβαιώνεις φυσικά: "Τέλεια! Σε γράφω για fade την Τετάρτη στις 6 το απόγευμα, στο όνομα Γιάννης. Σε περιμένουμε!"
Μετά: "Καλή σου μέρα!" και τέλος. Αν πει "ευχαριστώ" ή "γεια", απάντα ένα ζεστό "Γεια!" και τίποτα άλλο.

Το "On The Grind" προφέρεται αγγλικά ("ον δε γκράιντ").
Μιλάς ΠΑΝΤΑ ελληνικά.
Τηλέφωνο μαγαζιού: 6934354652."""

async def _hangup_room(ctx: JobContext):
    try:
        lk = livekit_api.LiveKitAPI(url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
        await lk.room.delete_room(livekit_api.DeleteRoomRequest(room=ctx.room.name))
        logger.info(f"Room {ctx.room.name} deleted")
        await lk.aclose()
    except Exception as e:
        logger.error(f"Hangup error: {e}")

async def entrypoint(ctx: JobContext):
    logger.info("Job received")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    caller_phone = None
    if ctx.room.name.startswith("sip-"):
        parts = ctx.room.name.split("_")
        if len(parts) >= 2:
            caller_phone = parts[1]
            logger.info(f"Caller: {caller_phone}")
    
    session = voice.AgentSession(
        vad=silero.VAD.load(
            min_silence_duration=0.3,
            activation_threshold=0.45,
            prefix_padding_duration=0.15,
        ),
        stt=deepgram.STT(
            model="nova-2", 
            language="el",
            keywords=[("fade", 1.5), ("κούρεμα", 1.5), ("γένια", 1.5), ("ραντεβού", 1.5),
                      ("Δευτέρα", 1.0), ("Τρίτη", 1.0), ("Τετάρτη", 1.0), ("Πέμπτη", 1.0),
                      ("Παρασκευή", 1.0), ("Σάββατο", 1.0), ("αύριο", 1.0), ("σήμερα", 1.0)],
        ),
        llm=anthropic.LLM(model="claude-haiku-4-5"),
        tts=cartesia.TTS(
            voice=os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091"),
            language="el",
            speed=1.0,
        ),
        preemptive_generation=True,
    )
    
    agent = voice.Agent(instructions=get_instructions())
    await session.start(agent=agent, room=ctx.room)
    
    logger.info("Saying greeting")
    await session.say("Γεια σου! On The Grind, πώς μπορώ να βοηθήσω;")
    
    @session.on("agent_speech_committed")
    def _check_hangup(msg):
        text = msg.content if hasattr(msg, 'content') else str(msg)
        if "καλή σου μέρα" in text.lower():
            logger.info("Goodbye detected")
            asyncio.get_event_loop().call_later(2.0, lambda: asyncio.ensure_future(_hangup_room(ctx)))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=port), daemon=True).start()
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=AGENT_NAME))
