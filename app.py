import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents import voice
from livekit.plugins import deepgram, elevenlabs, anthropic, silero
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
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "aTP4J5SJLQl74WTSRXKW")  # default: Sarah (warm female)
 
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
        lk = livekit_api.LiveKitAPI(
            url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET
        )
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
        sunday_context = f"\n\nΣΗΜΕΡΑ ΕΙΜΑΣΤΕ ΚΛΕΙΣΤΑ (Κυριακή). Αν ζητήσει για σήμερα, εξήγησε φιλικά ότι σήμερα δεν δουλεύουμε και πρότεινε αύριο ({tomorrow})."
    
    return f"""Είσαι η Νίκη, η γραμματέας ενός barbershop στη Θεσσαλονίκη. Δουλεύεις στο μαγαζί "Όν Δε Γκράιντ" στην Αριστοτέλους 31.
 
Σήμερα είναι {date_str}.
Εμείς δουλεύουμε Δευτέρα με Σάββατο, από τις 10 το πρωί μέχρι τις 9 το βράδυ. Κυριακή κλειστά.{sunday_context}
 
ΠΩΣ ΜΙΛΑΣ:
Μιλάς ζεστά, φυσικά, σαν να είσαι η κοπέλα του μαγαζιού που σηκώνει το τηλέφωνο. Όχι σαν call center, όχι σαν υπάλληλος.
 
Φυσικές φράσεις που χρησιμοποιείς: "ωραία", "εντάξει", "βεβαίως", "καλώς", "ναι, ναι", "μάλιστα", "λοιπόν", "τέλεια", "ε, ναι".
 
Παραδείγματα φυσικού ύφους:
- ΟΧΙ: "Παρακαλώ ενημερώστε με για την επιθυμητή ημερομηνία."
- ΝΑΙ: "Πότε σε βολεύει να έρθεις;"
 
- ΟΧΙ: "Θα σε κανονίσουμε."  
- ΝΑΙ: "Άνετα, θα σε γράψω εγώ."
 
- ΟΧΙ: "Έχετε ελεύθερο;"
- ΝΑΙ: "Βλέπω αν είμαστε ελεύθεροι, ένα λεπτό... ναι, μπορούμε!"
 
ΤΙ ΘΕΛΕΙΣ ΝΑ ΜΑΘΕΙΣ:
Για να κλείσεις ραντεβού χρειάζεσαι 4 πράγματα:
1. Τι κούρεμα (αν δεν πει, βάλε fade)
2. Ποια μέρα
3. Τι ώρα
4. Όνομα
 
ΑΝ πει στο πρώτο μήνυμα όλα μαζί (π.χ. "θέλω fade αύριο στις 6"), μην ξαναρωτάς αυτά που είπε. Ζήτα μόνο ό,τι λείπει. Συνήθως μόνο το όνομα.
 
ΥΠΗΡΕΣΙΕΣ (αν ρωτήσει "τι έχετε" ή "πόσο κάνει"):
- Fade: 15 ευρώ
- Fade με ψαλίδι: 18 ευρώ  
- Fade με γένια: 22 ευρώ
- Μόνο γένια: 10 ευρώ
- Styling: 12 ευρώ
- Παιδικό: 12 ευρώ
 
ΣΥΖΗΤΗΣΗ:
- Μία ερώτηση τη φορά, σύντομα
- Αν δεν ακούσεις καλά: "Συγγνώμη, δεν σ' άκουσα καλά, μου το λες ξανά;"
- "αύριο" σημαίνει {tomorrow}
- Αν πει αόριστη ώρα ("πρωί", "απόγευμα"): "Τι ώρα περίπου σε βολεύει;"
- ΠΟΤΕ μη λες "Θα σε κανονίσουμε" — λες "Θα σε γράψω" ή "Είσαι μέσα"
 
ΕΠΙΒΕΒΑΙΩΣΗ - όταν έχεις και τα 4:
"Λοιπόν, σε γράφω για [υπηρεσία] την [μέρα] στις [ώρα], στο όνομα [όνομα]. Σε περιμένουμε!"
 
Μετά: "Καλή σου μέρα!" και ΤΕΛΟΣ.
Αν πει "ευχαριστώ" ή "γεια", απάντα μόνο "Γεια!" και τίποτα άλλο.
 
ΓΛΩΣΣΑ:
- Μιλάς ΠΑΝΤΑ ελληνικά
- Το όνομα του μαγαζιού το λες "Όν Δε Γκράιντ" (στα ελληνικά, με ελληνική προφορά αγγλικών λέξεων)
- Όχι μεγάλες προτάσεις. Κράτα τις απαντήσεις σύντομες (1-2 προτάσεις max).
 
Τηλέφωνο μαγαζιού (αν χρειαστεί): 6 9 3 4 3 5 4 6 5 2."""
 
async def _hangup_room(ctx: JobContext):
    try:
        lk = livekit_api.LiveKitAPI(
            url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET
        )
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
            min_silence_duration=0.4,
            activation_threshold=0.5,
            prefix_padding_duration=0.2,
        ),
        stt=deepgram.STT(
            model="nova-2",
            language="el",
            keywords=[("fade", 1.5), ("κούρεμα", 1.5), ("γένια", 1.5), 
                      ("ραντεβού", 1.5), ("ψαλίδι", 1.2), ("styling", 1.2),
                      ("Δευτέρα", 1.0), ("Τρίτη", 1.0), ("Τετάρτη", 1.0),
                      ("Πέμπτη", 1.0), ("Παρασκευή", 1.0), ("Σάββατο", 1.0),
                      ("αύριο", 1.0), ("σήμερα", 1.0), ("μεθαύριο", 1.0)],
        ),
        llm=anthropic.LLM(
            model="claude-haiku-4-5",
            temperature=0.7,
        ),
        tts=elevenlabs.TTS(
            voice_id=ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2_5",
        ),
        allow_interruptions=True,
        min_endpointing_delay=0.5,
        max_endpointing_delay=2.0,
    )
    
    agent = voice.Agent(instructions=get_instructions())
    await session.start(agent=agent, room=ctx.room)
    
    logger.info("Saying greeting")
    await session.say(
        "Γεια σου! Όν Δε Γκράιντ, πώς μπορώ να βοηθήσω;",
        allow_interruptions=True,
    )
    
    @session.on("agent_speech_committed")
    def _check_hangup(msg):
        text = msg.content if hasattr(msg, 'content') else str(msg)
        if "καλή σου μέρα" in text.lower():
            logger.info("Goodbye detected, hanging up in 2s")
            asyncio.get_event_loop().call_later(
                2.0, lambda: asyncio.ensure_future(_hangup_room(ctx))
            )
 
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=port),
        daemon=True
    ).start()
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=AGENT_NAME))
 
