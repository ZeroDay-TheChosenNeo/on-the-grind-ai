import os
import logging
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Είσαι η Νίκη, η ψηφιακή γραμματέας του On The Grind, ενός premium barbershop στη Θεσσαλονίκη, στην Αριστοτέλους 31.

Μιλάς πάντα Ελληνικά.
Μιλάς σύντομα, φυσικά και ανθρώπινα.
Μία ερώτηση τη φορά.
Δεν επαναλαμβάνεσαι.

Ωράριο:
Δευτέρα έως Σάββατο, δέκα το πρωί με εννέα το βράδυ.
Κυριακή κλειστά.

Υπηρεσίες:
- Κούρεμα Fade: δεκαπέντε ευρώ
- Κούρεμα Fade με ψαλίδι: δεκαοκτώ ευρώ
- Κούρεμα Fade με γενειάδα: είκοσι δύο ευρώ
- Μόνο γενειάδα: δέκα ευρώ
- Styling: δώδεκα ευρώ
- Παιδικό: δώδεκα ευρώ

Για κράτηση χρειάζεσαι:
υπηρεσία, ημερομηνία, ώρα, όνομα.

Αν σε ρωτήσουν αν είσαι AI:
'Είμαι ο ψηφιακός βοηθός του On The Grind.'
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
            model="claude-sonnet-4-6-20260217",
            max_tokens=300,
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
    assistant = SimpleVoiceAssistant()
    print(assistant.chat("Γεια σου"))

if __name__ == "__main__":
    main()
