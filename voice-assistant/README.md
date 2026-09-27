# Claude Voice Assistant

Talk to Claude in your browser. [ElevenLabs Speech Engine](https://elevenlabs.io/docs/overview/capabilities/speech-engine) handles the microphone, speech-to-text, turn-taking and text-to-speech. This server receives each transcript over a WebSocket, streams Claude's reply back, and ElevenLabs speaks it.

```
browser ──audio──▶ ElevenLabs ──transcript──▶ this server (/ws) ──▶ Claude
   ▲                    │                            │
   └──────speech────────┴◀──────streamed text────────┘
```

## Setup

1. Install dependencies and create your env file:

   ```bash
   npm install
   cp .env.example .env   # add ELEVENLABS_API_KEY and ANTHROPIC_API_KEY
   ```

2. Expose the server publicly (ElevenLabs has to reach it), then put the URL in `.env`:

   ```bash
   ngrok http 3001
   # PUBLIC_WS_URL=wss://<your-subdomain>.ngrok.app/ws
   ```

3. Create the Speech Engine once, and copy the printed ID into `.env` as `ELEVENLABS_SPEECH_ENGINE_ID`:

   ```bash
   npm run create-engine
   ```

4. Start the server and open http://localhost:3001:

   ```bash
   npm start
   ```

If the ngrok URL changes, run `npm run create-engine` again, or update the engine's `wsUrl`.

## Files

| File | Purpose |
| --- | --- |
| `src/server.ts` | Express app: serves the page, issues conversation tokens at `/api/token`, attaches Speech Engine at `/ws` |
| `src/claude.ts` | Turns the transcript into Claude messages and streams the reply |
| `src/create-engine.ts` | One-time script that creates the Speech Engine resource |
| `src/client.ts` | Browser code, bundled to `public/app.js` by `npm start` |

## Notes

- **Model:** `claude-opus-5` at low effort, which keeps replies quick. You can override it with `CLAUDE_MODEL`. Server-side refusal fallbacks (`fallbacks: "default"`) are on.
- **Interruptions:** when the user talks over the assistant, the SDK aborts the signal and the Claude stream is cancelled.
- **Security:** speech transcripts are untrusted. They only ever become `user` messages, capped in length. The assistant has no tools, and the system prompt can't be changed from speech. Your API keys stay on the server, and the browser only gets a short-lived conversation token. Speech Engine verifies the JWT on every incoming connection, so leave `disableAuth` off.
