import httpx
import json

payload = {
    "event": "messages.received",
    "sessionId": "ebf133d869684fc674046c6c35a0a47007d00993befb1a6ef6bb1bf73058ec08",
    "data": {
        "messages": {
            "key": {
                "id": "3EB004D253B5B248BB088C",
                "fromMe": False,
                "remoteJid": "189975127683211@lid",
                "senderPn": "584128961647@s.whatsapp.net",
                "cleanedSenderPn": "584128961647",
                "senderLid": "189975127683211@lid",
                "addressingMode": "lid"
            },
            "messageTimestamp": 1784402765,
            "pushName": ".",
            "broadcast": False,
            "message": {
                "conversation": "Hola",
                "messageContextInfo": {}
            },
            "messageBody": "Hola",
            "remoteJid": "189975127683211@lid",
            "id": "3EB004D253B5B248BB088C"
        }
    },
    "timestamp": 1784402766013
}

url = "http://127.0.0.1:8000/webhook"
try:
    response = httpx.post(url, json=payload, timeout=10.0)
    print(f"STATUS: {response.status_code}")
    print(f"RESPONSE: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")
