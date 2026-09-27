import { Conversation } from "@elevenlabs/client";

const button = document.querySelector<HTMLButtonElement>("#toggle")!;
const statusEl = document.querySelector<HTMLParagraphElement>("#status")!;
const log = document.querySelector<HTMLOListElement>("#log")!;

let conversation: Conversation | null = null;

function setStatus(text: string) {
  statusEl.textContent = text;
}

function addLine(role: "user" | "agent", text: string) {
  const item = document.createElement("li");
  item.className = role;
  item.textContent = text;
  log.append(item);
  item.scrollIntoView({ block: "end" });
}

async function start() {
  button.disabled = true;
  setStatus("Requesting microphone…");
  try {
    await navigator.mediaDevices.getUserMedia({ audio: true });
    setStatus("Connecting…");
    const res = await fetch("/api/token");
    if (!res.ok) throw new Error("Could not get a conversation token");
    const { token } = await res.json();

    conversation = await Conversation.startSession({
      conversationToken: token,
      overrides: { agent: { firstMessage: "Hi! I'm Claude. What would you like to talk about?" } },
      onConnect: () => {
        button.textContent = "Stop";
        button.disabled = false;
        setStatus("Listening");
      },
      onDisconnect: () => {
        conversation = null;
        button.textContent = "Start talking";
        button.disabled = false;
        setStatus("Ready");
      },
      onModeChange: ({ mode }) => setStatus(mode === "speaking" ? "Speaking" : "Listening"),
      onMessage: ({ role, message }) => addLine(role, message),
      onError: (message) => setStatus(`Error: ${message}`),
    });
  } catch (err) {
    button.disabled = false;
    setStatus(err instanceof Error ? err.message : "Could not start");
  }
}

button.addEventListener("click", async () => {
  if (conversation) {
    button.disabled = true;
    await conversation.endSession();
  } else {
    await start();
  }
});
