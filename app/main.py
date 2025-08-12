import logging
from fastapi import FastAPI
from dotenv import load_dotenv  # Ajouté pour charger les variables d'environnement depuis .env
from .models import ChatIn, ChatOut
from .agent import agent_reply

# Chargement des variables d'environnement depuis le fichier .env
load_dotenv()

logging.getLogger("httpx").setLevel(logging.WARNING)


app = FastAPI(title='Expense Agent (Python)', version='0.1.0')

@app.post('/chat', response_model=ChatOut)
def chat(body: ChatIn):
    out = agent_reply(body.message, body.attachments or {})
    return out
