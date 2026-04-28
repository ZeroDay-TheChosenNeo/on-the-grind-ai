# On The Grind AI Voice Assistant

Greek-language voice assistant for On The Grind barbershop using LiveKit, Deepgram, Claude, and Cartesia.

## Architecture

- **Orchestration**: LiveKit (open source)
- **Speech-to-Text**: Deepgram Nova-2 (Greek support)
- **LLM**: Claude Haiku (best Greek language support)
- **Text-to-Speech**: Cartesia (Greek voice)
- **Telephony**: Telnyx SIP (optional)

## Cost per Minute

- Deepgram STT: $0.0059/min
- Claude Haiku: ~$0.008/min  
- Cartesia TTS: $0.015/min
- Telnyx SIP: $0.005/min
- **Total**: ~$0.034/min (~€0.031/min)

For 900 minutes/month (15 calls/day × 2 min × 30 days): **~€28/month**

## Setup

### 1. Install Python 3.11+

```bash
python --version  # Should be 3.11 or higher
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Get API Keys

- **LiveKit**: Create account at livekit.io → get API key/secret
- **Deepgram**: Already have account → get API key from console
- **Anthropic**: Get from console.anthropic.com
- **Cartesia**: Already have account → get API key
- **Telnyx** (optional): For phone integration

### 5. Run Locally

```bash
python main.py dev
```

### 6. Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

## Environment Variables for Railway

Add these in Railway dashboard:

```
LIVEKIT_URL=wss://your-url.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
DEEPGRAM_API_KEY=...
ANTHROPIC_API_KEY=...
CARTESIA_API_KEY=...
CARTESIA_VOICE_ID=a0e99841-438c-4a64-b679-ae501e7d6091
```

## Testing

Test locally before deploying:

```bash
# Start the agent
python main.py dev

# In another terminal, use LiveKit CLI to test
lk app create-token --room test-room --identity test-user
```

## Production Deployment

1. Push to GitHub
2. Connect Railway to GitHub repo
3. Add environment variables
4. Deploy

## Troubleshooting

- **Greek not working**: Check DEEPGRAM language is set to "el"
- **No audio**: Verify Cartesia API key and voice ID
- **Connection issues**: Check LiveKit URL format (must start with wss://)

## Cost Optimization

Current setup costs ~€28/month for 900 minutes. Compare to:
- Vapi.ai: ~€135/month (same usage)
- Savings: €107/month per client

## Support

For issues, check the LiveKit docs: docs.livekit.io
