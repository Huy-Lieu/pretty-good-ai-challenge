from twilio.rest import Client
import config

import sys

scenario_id = sys.argv[1] if len(sys.argv) > 1 else "booking_basic"

client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

call = client.calls.create(
    to=config.PGAI_TEST_NUMBER,
    from_=config.TWILIO_PHONE_NUMBER,
    url=f"{config.PUBLIC_BASE_URL}/twiml/connect?scenario={scenario_id}",
    record=True,
)

print("Call SID:", call.sid, "| scenario:", scenario_id)
print("Status right after placing:", call.status)