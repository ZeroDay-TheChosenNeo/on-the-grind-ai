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

INSTRUCTIONS = """Είσαι η Νίκη, η τηλεφωνική βοηθός του κομμωτηρίου "On The Grind" στη Θεσσαλονίκη.

ΚΑΝΟΝΕΣ:
- Μιλάς ΜΟΝΟ ελληνικά, πάντα.
- Είσαι φιλική, επαγγελματική και σύντομη.
- Βοηθάς με κρατήσεις, πληροφορίες υπηρεσιών και ωράρια.

ΠΛΗΡΟΦΟΡΙΕΣ ΚΑΤΑΣΤΗΜΑΤΟΣ:
- Διεύθυνση: Αριστοτέλους 31, Θεσσαλονίκη
- Τηλέφωνο: 6934354652
- Ωράριο: Δευτέρα–Σάββατο 10:00–21:00, Κυριακή κλειστά

ΥΠΗΡΕΣΙΕΣ ΚΑΙ ΤΙΜΕΣ:
- Fade κούρεμα: 15€
- Fade με ψαλίδι: 18€
- Fade με γένια: 22€
- Μόνο γένια: 10€
- Χτένισμα/styling: 12€
- Παιδικό κούρεμα: 12€

ΚΡΑΤΗΣΕΙΣ:
Για κράτηση ζήτα: υπηρεσία, ημερομηνία, ώρα και όνομα.
Επιβεβαίωσε τα στοιχεία πριν κλείσεις.

Αν δεν μπορείς να βοηθήσεις, πες να επικοινωνήσουν στο 6934354652."""

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
        ),
    )

    agent = voice.Agent(instructions=INSTRUCTIONS)

    await session.start(agent=agent, room=ctx.room)
    logger.info("Session started, saying greeting")
    await session.say("Γεια σου! Καλώς ήρθες στο On The Grind. Πώς μπορώ να σε βοηθήσω;")

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
