<<<<<<< Updated upstream
# pretty-good-ai-challenge
=======
# Patient Simulator Voice Bot

A voice bot that calls Pretty Good AI's scheduling agent, plays the role of a
realistic patient across a range of scenarios, holds a full spoken conversation,
records and transcribes both sides, and produces the evidence for a bug report.

It places real outbound phone calls, speaks naturally in real time, and was used
to run 16 distinct test scenarios against the target agent. The findings are in
[`bug_report.md`](bug_report.md).

## How it works

The bot bridges two services. **Twilio** handles the actual phone call (dialing
out, carrying audio). **OpenAI's Realtime API** is the brain that listens and
speaks as the patient. A thin **FastAPI bridge** sits between them, relaying
audio in both directions, and an **orchestrator** script places the calls and
collects the results.

```
Orchestrator → Twilio → (phone call) → Athena agent
                  ↕  media stream
              FastAPI bridge ↔ OpenAI Realtime API
                  ↓
              results/ (transcript per call) + manifest.json
```

The bridge is deliberately thin: it moves audio and writes transcripts, but makes
no decisions about the conversation. All of the patient's behavior comes from a
per-scenario prompt loaded from `scenarios.yaml`. Audio passes through in Twilio's
native G.711 codec on both legs, so no resampling is needed. A fuller design
write-up, including the rationale for the speech-to-speech approach over a
cascaded STT/LLM/TTS pipeline, is in [`architecture.md`](architecture.md).

## Scenarios

Sixteen scenarios in `scenarios.yaml`, each crossing a *task* with a *caller
type* so no two calls are alike: booking, rescheduling, canceling, refills,
insurance questions, and edge cases (closed-day requests, contradictory info,
out-of-scope medical questions, an interrupting caller, a frustrated caller, and
more). Each has a distinct persona and a voice appropriate to the caller.

## Setup

Requirements: Python 3.12, a Twilio account with a voice-capable number, an
OpenAI API key with Realtime access, and a public HTTPS/WebSocket tunnel (this
project used ngrok).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your credentials
```

`.env` values:

```
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=     # your Twilio number, E.164 (e.g. +15625241556)
OPENAI_API_KEY=
PUBLIC_BASE_URL=         # your public tunnel URL, no trailing slash
```

The target test line is a single hardcoded constant in `config.py`, so the bot
can only ever dial that one number.

## Running it

Three processes. In separate terminals:

```bash
# 1. the bridge
uvicorn bridge.server:app --port 8000

# 2. the public tunnel (example with ngrok)
ngrok http --url=YOUR-DOMAIN.ngrok-free.dev 8000

# 3. place calls
python3 orchestrator.py                      # run all 16 scenarios
python3 orchestrator.py closed_saturday      # run specific scenario(s)
```

Each call writes a live transcript to `results/` and appends a record (scenario,
call SID, timestamp, status) to `results/manifest.json`. Recordings are captured
by Twilio and retrievable by call SID.

## Repository layout

```
config.py            shared config + the single allowed test number
bridge/
  server.py          FastAPI: TwiML route + media-stream websocket
  realtime.py        OpenAI Realtime session, audio relay, transcript capture
orchestrator.py      places calls, polls status, writes the manifest
scenarios.yaml       the 16 patient personas and their voices
results/             transcripts, recordings, manifest.json
architecture.md      design write-up
bug_report.md        findings from the 16 test calls
```

## Notes

- The caller side of each transcript ("BOT") is exact. The agent side is
  transcribed by a separate speech-to-text model and may contain minor noise; the
  audio recordings are authoritative for agent-side quotes.
- Calls are placed sequentially, one at a time, with a configurable pause between
  them. There is no database; results live as flat files plus a manifest, which
  is all this project needs.
>>>>>>> Stashed changes
