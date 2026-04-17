from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

def get_creds(credentials_path="credentials.json", token_path="token.json"):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds

def main():
    creds = get_creds()
    service = build("calendar", "v3", credentials=creds)

    # lista próximos 5 eventos (só para confirmar que funcionou)
    events = service.events().list(calendarId="primary", maxResults=5, singleEvents=True, orderBy="startTime").execute()
    items = events.get("items", [])
    print("OK. Eventos encontrados:", len(items))
    for e in items:
        print("-", e.get("summary", "(sem título)"))

if __name__ == "__main__":
    main()
    