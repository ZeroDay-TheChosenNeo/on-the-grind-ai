import os
import logging
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm, voice
from livekit.plugins import deepgram, cartesia, anthropic, silero
from fastapi import FastAPI
import uvicorn
from threading import Thread

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy"}

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    session = voice.AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2", language="el"),
        llm=anthropic.LLM(model="claude-3-haiku-20240307"),
        tts=cartesia.TTS(voice=os.getenv("CARTESIA_VOICE_ID"), language="el"),
    )

    agent = voice.Agent(
        instructions="Είσαι η Νίκη. Μιλάς μόνο Ελληνικά. Βοηθάς πελάτες του κουρείου On The Grind.",
    )

    await session.start(agent=agent, room=ctx.room)
    await session.say("Γεια σου! Καλώς ήρθες στο On The Grind.")

if __name__ == "__main__":
    Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080"))), daemon=True).start()
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=os.getenv("AGENT_NAME", "on-the-grind-ai")))
