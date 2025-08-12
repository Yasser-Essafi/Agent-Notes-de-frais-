import json, os, datetime
from typing import Any, Dict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def get_policy() -> Dict[str, Any]:
    with open(os.path.join(BASE_DIR, 'policy.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def create_expense(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Écrit dans un fichier JSON local (expenses.json)
    path = os.path.join(BASE_DIR, 'expenses.json')
    data = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    payload = dict(payload)
    payload['created_at'] = datetime.datetime.utcnow().isoformat()
    data.append(payload)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return payload

def send_approval(user: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Simule un envoi d'approbation (écrit dans approvals.json)
    path = os.path.join(BASE_DIR, 'approvals.json')
    data = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
    record = {
        'to': user,
        'payload': payload,
        'sent_at': datetime.datetime.utcnow().isoformat()
    }
    data.append(record)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return record
