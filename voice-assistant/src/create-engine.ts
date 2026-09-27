import "dotenv/config";
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const wsUrl = process.env.PUBLIC_WS_URL;
if (!wsUrl?.startsWith("wss://")) {
  throw new Error("Set PUBLIC_WS_URL to your public WebSocket URL, e.g. wss://abc.ngrok.app/ws");
}

const elevenlabs = new ElevenLabsClient();
const engine = await elevenlabs.speechEngine.create({
  name: "Claude Voice Assistant",
  speechEngine: { wsUrl },
  // Lets the browser supply the greeting via overrides.agent.firstMessage.
  overrides: { firstMessage: true },
});

console.log(`Created Speech Engine. Add this to .env:\n\nELEVENLABS_SPEECH_ENGINE_ID=${engine.engineId}`);
