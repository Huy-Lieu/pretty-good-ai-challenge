from fastapi import FastAPI, Response, WebSocket, Request
from twilio.twiml.voice_response import VoiceResponse, Connect
import json
import config
from bridge.realtime import run_realtime_session

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/twiml/connect")
def twiml_connect(request: Request):
    scenario = request.query_params.get("scenario", "booking_basic")
    response = VoiceResponse()
    connect = Connect()
    wss_url = config.PUBLIC_BASE_URL.replace("https://", "wss://")
    stream = connect.stream(url=f"{wss_url}/media-stream")
    stream.parameter(name="scenario", value=scenario)
    response.append(connect)
    return Response(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()
    stream_sid = None
    async for message in websocket.iter_text():
        data = json.loads(message)
        if data["event"] == "start":
            stream_sid = data["start"]["streamSid"]
            params = data["start"].get("customParameters", {})
            print("CUSTOM PARAMS RECEIVED:", params, flush=True)
            scenario_id = params.get("scenario", "booking_basic")
            print("SCENARIO RESOLVED:", scenario_id, flush=True)
            break
    if stream_sid:
        await run_realtime_session(websocket, stream_sid, scenario_id)