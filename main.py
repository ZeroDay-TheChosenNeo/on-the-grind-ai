"""
On The Grind AI Voice Assistant
Simple REST API approach - no LiveKit Agents framework
Works with Python 3.9+
"""

import os
import logging
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt
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


class SimpleVoiceAssistant:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.conversation_history = []

    def chat(self, user_input):
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        response = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=self.conversation_history
        )

        assistant_message = response.content[0].text

        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message


def main():
    print("On The Grind AI Assistant - Test Mode")
    print("=" * 50)
    print("Type 'quit' to exit\n")

    assistant = SimpleVoiceAssistant()

    greeting = assistant.chat("Γεια σου")
    print(f"Νίκη: {greeting}\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Αντίο!")
            break

        response = assistant.chat(user_input)
        print(f"Νίκη: {response}\n")


if __name__ == "__main__":
    main()
