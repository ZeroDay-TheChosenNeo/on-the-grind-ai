"""
On The Grind AI Voice Assistant
LiveKit + Deepgram + Claude + Cartesia integration
"""

import asyncio
import os
import logging
from livekit import rtc, agents
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.plugins import deepgram, openai, cartesia, silero

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt for the barbershop assistant
SYSTEM_PROMPT = """Είσαι η Νίκη, η ψηφιακή γραμματέας του "On The Grind", ενός premium barbershop στη Θεσσαλονίκη, στην Αριστοτέλους 31. Τηλέφωνο: 6934354652.

Η σημερινή ημερομηνία είναι: 28 Απριλίου 2026, Δευτέρα.

ΧΑΡΑΚΤΗΡΑΣ:
Μιλάς σύντομα και φυσικά σαν άνθρωπος. Μία ερώτηση τη φορά. Ποτέ επαναλήψεις.

ΩΡΑΡΙΟ:
Δευτέρα έως Σάββατο, από τις δέκα το πρωί έως τις εννέα το βράδυ. Κυριακή κλειστά.

ΥΠΗΡΕΣΙΕΣ:
- Κούρεμα Fade: δεκαπέντε ευρώ
- Κούρεμα Fade με ψαλίδι: δεκαοκτώ ευρώ
- Κούρεμα Fade με γενειάδα: είκοσι δύο ευρώ
- Μόνο γενειάδα: δέκα ευρώ
- Styling: δώδεκα ευρώ
- Παιδικό: δώδεκα ευρώ

ΚΡΑΤΗΣΗ ΡΑΝΤΕΒΟΥ:
Πληροφορίες που χρειάζεσαι: υπηρεσία, ημερομηνία, ώρα, όνομα.
Μόλις τα έχεις όλα, επιβεβαίωσε και τελείωσε.

ΚΑΝΟΝΕΣ:
- Μιλάς ΠΑΝΤΑ στα Ελληνικά
- Ώρες και τιμές με λόγια
- Αν ρωτηθείς αν είσαι AI: "Είμαι ο ψηφιακός βοηθός του On The Grind"
"""


class VoiceAssistant:
    """Main voice assistant class"""
    
    def __init__(self):
        self.chat_ctx = ChatContext()
        self.chat_ctx.messages.append(
            ChatMessage(role="system", content=SYSTEM_PROMPT)
        )
    
    async def entrypoint(self, ctx: JobContext):
        """Main entrypoint for LiveKit job"""
        logger.info("Starting voice assistant job")
        
        # Connect to the room
        await ctx.connect()
        
        # Wait for participant
        participant = await ctx.wait_for_participant()
        logger.info(f"Participant connected: {participant.identity}")
        
        # Initialize pipeline components
        stt = deepgram.STT(
            model="nova-2",
            language="el",  # Greek
        )
        
        llm = openai.LLM(
            model="claude-3-haiku-20240307",
            base_url="https://api.anthropic.com/v1",
        )
        
        tts = cartesia.TTS(
            voice_id=os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091"),
            language="el",  # Greek
        )
        
        # Start the assistant
        assistant = agents.VoiceAssistant(
            vad=silero.VAD.load(),
            stt=stt,
            llm=llm,
            tts=tts,
            chat_ctx=self.chat_ctx,
        )
        
        assistant.start(ctx.room)
        
        # Greet the user
        await assistant.say("On The Grind, γεια σας! Είμαι η Νίκη. Πώς μπορώ να σας βοηθήσω;")
        
        logger.info("Assistant started and greeted user")


def main():
    """Entry point"""
    assistant = VoiceAssistant()
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=assistant.entrypoint,
        ),
    )


if __name__ == "__main__":
    main()
