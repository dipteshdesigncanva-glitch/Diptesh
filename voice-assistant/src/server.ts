import "dotenv/config";
import { createServer } from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import express from "express";
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { streamReply, toClaudeMessages } from "./claude.js";

const PORT = Number(process.env.PORT ?? 3001);
const ENGINE_ID = process.env.ELEVENLABS_SPEECH_ENGINE_ID;
if (!ENGINE_ID) {
  throw new Error("Set ELEVENLABS_SPEECH_ENGINE_ID (run `npm run create-engine` first).");
}

const here = path.dirname(fileURLToPath(import.meta.url));
const elevenlabs = new ElevenLabsClient();
const app = express();

app.use(express.static(path.join(here, "..", "public")));

// Issues a short-lived conversation token so the API key never reaches the browser.
app.get("/api/token", async (_req, res) => {
  try {
    const { token } = await elevenlabs.conversationalAi.conversations.getWebrtcToken({
      agentId: ENGINE_ID,
    });
    res.json({ token });
  } catch (err) {
    console.error("Failed to create conversation token:", err);
    res.status(502).json({ error: "Could not start a conversation" });
  }
});

const httpServer = createServer(app);
const engine = await elevenlabs.speechEngine.get(ENGINE_ID);

const attachment = engine.attach(httpServer, "/ws", {
  debug: process.env.DEBUG === "true",
  onInit(conversationId) {
    console.log(`[${conversationId}] conversation started`);
  },
  async onTranscript(transcript, signal, session) {
    const messages = toClaudeMessages(transcript);
    if (messages.length === 0) return;
    await session.sendResponse(streamReply(messages, signal));
  },
  onClose(session) {
    console.log(`[${session.conversationId}] conversation ended`);
  },
  onDisconnect(session) {
    console.warn(`[${session.conversationId}] connection dropped`);
  },
  onError(error, session) {
    console.error(`[${session.conversationId}]`, error);
  },
});

httpServer.listen(PORT, () => {
  console.log(`Voice assistant on http://localhost:${PORT} (Speech Engine at /ws)`);
});

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.once(signal, async () => {
    await attachment.close();
    httpServer.close(() => process.exit(0));
  });
}
