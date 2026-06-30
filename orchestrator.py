"""Places calls, polls status, collects results. Filled in during Phase 7."""
import sys
import json
import os
import time
from twilio.rest import Client
import config

client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

PAUSE_BETWEEN_CALLS = 300      # seconds to wait after one call ends before the next begins
POLL_INTERVAL = 5               # seconds between Twilio status checks while a call runs
MAX_WAIT_PER_CALL = 360         # orchestrator stops waiting on a single call after this many seconds

ALL_SCENARIOS = [
    "book_brisk", "reschedule_elderly", "cancel_flustered", "refill_elderly",
    "hours_location_calm", "closed_saturday", "vague_request", "interrupt_redirect",
    "conflicting_info", "out_of_scope", "insurance_specifics", "book_for_family",
    "new_patient_paperwork", "cancel_fee_worried", "impatient_angry", "double_booking_check",
]

TERMINAL_STATES = ("completed", "failed", "busy", "no-answer", "canceled")


def place_call(scenario_id):
    call = client.calls.create(
        to=config.PGAI_TEST_NUMBER,
        from_=config.TWILIO_PHONE_NUMBER,
        url=f"{config.PUBLIC_BASE_URL}/twiml/connect?scenario={scenario_id}",
        record=True,
    )
    return call.sid


def wait_for_completion(call_sid):
    waited = 0
    while waited < MAX_WAIT_PER_CALL:
        status = client.calls(call_sid).fetch().status
        if status in TERMINAL_STATES:
            return status
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL
    return "timeout-waiting"


def log_manifest(record):
    os.makedirs("results", exist_ok=True)
    path = os.path.join("results", "manifest.json")
    manifest = json.load(open(path)) if os.path.exists(path) else []
    manifest.append(record)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    return len(manifest)


def run_batch(scenario_ids):
    for i, scenario_id in enumerate(scenario_ids, 1):
        print(f"\n[{i}/{len(scenario_ids)}] Placing call: {scenario_id}", flush=True)
        call_sid = place_call(scenario_id)
        print(f"  Call SID: {call_sid} -- waiting for it to finish...", flush=True)
        status = wait_for_completion(call_sid)
        total = log_manifest({
            "scenario": scenario_id,
            "call_sid": call_sid,
            "placed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "final_status": status,
        })
        print(f"  Finished: {status}. Manifest now holds {total} call(s).", flush=True)
        if i < len(scenario_ids):
            print(f"  Pausing {PAUSE_BETWEEN_CALLS}s before next call...", flush=True)
            time.sleep(PAUSE_BETWEEN_CALLS)
    print("\nBatch complete.", flush=True)


if __name__ == "__main__":
    scenarios = sys.argv[1:] if len(sys.argv) > 1 else ALL_SCENARIOS
    print(f"Running batch of {len(scenarios)} scenario(s).", flush=True)
    run_batch(scenarios)