import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

app = FastAPI()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Είσαι η Νίκη, η ψηφιακή γραμματέας του On The Grind.
Μιλάς πάντα Ελληνικά, σύντομα και φυσικά.
Μία ερώτηση τη φορά.
"""

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat")
def chat(req: ChatRequest):
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": req.message}]
    )
    return {"reply": response.content[0].text}

@app.post("/inbound-call")
async def inbound_call(request: Request):
    body = await request.json()
    print("TELNYX WEBHOOK:", body)

    return JSONResponse({
        "actions": [
            {
                "answer": {}
            },
            {
                "speak": {
                    "language": "el-GR",
                    "voice": "female",
                    "text": "Γεια σου. Καλώς ήρθες στο On The Grind. Πώς μπορώ να βοηθήσω;"
                }
            }
        ]
    })
