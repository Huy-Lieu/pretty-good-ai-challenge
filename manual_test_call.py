from twilio.rest import Client
import config

client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

call = client.calls.create(
    to=config.PGAI_TEST_NUMBER,
    from_=config.TWILIO_PHONE_NUMBER,
    url=f"{config.PUBLIC_BASE_URL}/twiml/connect",
    record=True,
)

print("Call SID:", call.sid)
print("Status right after placing:", call.status)