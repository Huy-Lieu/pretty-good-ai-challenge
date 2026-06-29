"""Builds and manages the OpenAI Realtime session. Filled in during Phase 3."""
import json
import asyncio
import os
import time
import websockets
import config

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime-2"

PERSONA_INSTRUCTIONS = (
    "You are a person calling a medical practice on the phone. You are the caller, "
    "a patient, not an assistant. Wait for them to greet you before you speak. "
    "You want to book a routine checkup, you're flexible on day and time. "
    "Speak naturally and casually, the way a real person talks on the phone."
)

async def run_realtime_session(twilio_ws, stream_sid):
    headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"}
    transcript = []  # list of (speaker, text) collected live
    call_start = time.time()

    os.makedirs("results", exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.abspath(os.path.join("results", f"call_{ts}_{stream_sid}.txt"))
    transcript_file = open(path, "a")

    def log_line(speaker, text):
        elapsed = int(time.time() - call_start)
        line = f"[{elapsed//60:02d}:{elapsed%60:02d}] {speaker}: {text}"
        transcript_file.write(line + "\n")
        transcript_file.flush()
        # print("LINE:", line, flush=True)

    async with websockets.connect(OPENAI_REALTIME_URL, additional_headers=headers) as openai_ws:
        await openai_ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "type": "realtime",
                "output_modalities": ["audio"],
                "audio": {
                    "input": {
                        "format": {"type": "audio/pcmu"},
                        "transcription": {"model": "whisper-1"},
                        "turn_detection": {"type": "server_vad"},
                    },
                    "output": {
                        "format": {"type": "audio/pcmu"},
                        "voice": "alloy",
                    },
                },
                "instructions": PERSONA_INSTRUCTIONS,
            },
        }))

        async def twilio_to_openai():
            async for message in twilio_ws.iter_text():
                data = json.loads(message)
                if data["event"] == "media":
                    await openai_ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": data["media"]["payload"],
                    }))
                elif data["event"] == "stop":
                    break

        async def openai_to_twilio():
            async for raw in openai_ws:
                event = json.loads(raw)
                etype = event.get("type")
                # print("EVENT:", etype)
                if etype == "session.updated":
                    print("SESSION CONFIRMED:", json.dumps(event, indent=2))
                elif etype == "response.output_audio.delta":
                    await twilio_ws.send_json({
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {"payload": event["delta"]},
                    })
                elif etype == "response.output_audio_transcript.done":
                    log_line("BOT", event.get("transcript", ""))
                elif etype == "conversation.item.input_audio_transcription.completed":
                    log_line("AGENT", event.get("transcript", ""))
                elif etype == "error":
                    print("OPENAI ERROR:", json.dumps(event, indent=2))
        try:
            await asyncio.gather(twilio_to_openai(), openai_to_twilio())
        except Exception as e:
            print(f"SESSION ENDED WITH: {type(e).__name__}: {e}", flush=True)
        return transcript


        