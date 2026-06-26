import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = os.environ["TWILIO_PHONE_NUMBER"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PUBLIC_BASE_URL = os.environ["PUBLIC_BASE_URL"]

# The only number this project is ever allowed to call.
PGAI_TEST_NUMBER = "+18054398008"