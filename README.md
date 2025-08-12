# Agent Notes de Frais

Service FastAPI pour traiter automatiquement les demandes de notes de frais avec Azure OpenAI.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` vers `.env` et remplir vos credentials Azure OpenAI :

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

Si pas configuré, ça marche quand même avec l'extraction basique.

## Utilisation

```bash
# Tests
python run_tests.py

# API
uvicorn app.main:app --reload
# http://localhost:8000/docs
```

## Comment ça marche

1. L'utilisateur envoie un message : "Taxi 50€ avec reçu"
2. Azure OpenAI extrait les infos structurées (ou fallback heuristique)
3. Application des règles depuis `policy.json`
4. Décision : OK / NEEDS_APPROVAL / REJECTED

## API

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Restaurant 85€ avec reçu"}'
```

Réponse :
```json
{
  "verdict": "OK",
  "reason": "Conforme à la politique", 
  "record": { ... }
}
```
Interface Swagger
L'API est documentée et testable via l'interface Swagger : http://localhost:8000/docs
Voir le dossier captures/ pour des exemples visuels de l'interface et des réponses.


## Tests

12 scénarios de test qui couvrent :
- Les 4 cas de base demandés
- Quelques cas limites (montants aux seuils)
- Formats variés (virgules, etc.)

## Règles

Voir `policy.json` :
- Taxi : 80€ max, reçu obligatoire
- Restaurant : 100€ max, reçu obligatoire  
- Hôtel : 180€ max, reçu obligatoire
- Alcool : interdit
- Seuils d'approbation : 120€ (EUR), 150€ (CAD)

## Fichiers générés

- `expenses.json` : dépenses créées
- `approvals.json` : demandes d'approbation

## Notes techniques

- Timeout Azure OpenAI : 30s
- Fallback heuristique si Azure indisponible
- Logs basiques pour debug
- Pas de BDD, juste des fichiers JSON