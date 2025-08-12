import os, re, json
import httpx # Ajouté pour les appels Azure OpenAI
import logging
from typing import Any, Dict, Optional, Tuple
from .tools import get_policy, create_expense, send_approval


import httpx # Ajouté pour les appels Azure OpenAI
import logging


logger = logging.getLogger(__name__)


def _heuristic_extract(message: str, attachments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    logger.info("🔄 Utilisation de l'extraction heuristique (fallback)")
    text = (message or '').lower()
    has_receipt = bool(re.search(r're(ç|c)e?u.*(ok|oui|yes)', text)) or bool(attachments and attachments.get('ocr', {}).get('has_receipt'))
    currency = 'EUR'
    if 'cad' in text: currency = 'CAD'
    if 'eur' in text or '€' in text: currency = 'EUR'
    if attachments and attachments.get('ocr', {}).get('currency'):
        currency = attachments['ocr']['currency']

    amount = 0.0
    if attachments and attachments.get('ocr', {}).get('amount_total') is not None:
        amount = float(attachments['ocr']['amount_total'])
    else:
        m = re.search(r'(\d+[\.,]\d+|\d+)', text)
        if m: amount = float(m.group(1).replace(',', '.'))

    category = 'Misc'
    if 'taxi' in text: category = 'Taxi'
    elif 'restau' in text: category = 'Restaurant'
    elif 'hôtel' in text or 'hotel' in text or 'hôtel' in text: category = 'Hotel'
    elif 'vin' in text or 'alcool' in text: category = 'Alcohol'

    return {
        'category': category,
        'amount_total': amount,
        'currency': currency,
        'has_receipt': has_receipt
    }

def _azure_openai_extract(message: str, attachments: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:

    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    if not (endpoint and api_key and deployment):
        logger.info("⚠️  Azure OpenAI non configuré - utilisation du fallback heuristique")
        return None
    
    # Construction du contexte avec les données OCR si disponibles
    context = ""
    if attachments and 'ocr' in attachments:
        context = f"OCR data: {attachments['ocr']}"
    
    # Définition du schéma de fonction pour l'extraction structurée
    function_def = {
        "name": "extract_expense",
        "description": "Extraire les informations de dépense depuis le message utilisateur",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["Taxi", "Restaurant", "Hotel", "Alcohol", "Misc"]
                },
                "amount_total": {"type": "number"},
                "currency": {
                    "type": "string", 
                    "enum": ["EUR", "CAD"]
                },
                "has_receipt": {"type": "boolean"}
            },
            "required": ["category", "amount_total", "currency", "has_receipt"]
        }
    }
    
    # Préparation des messages pour le LLM(gpt-4o)
    messages = [
        {
            "role": "system", 
            "content": """Tu es un assistant de traitement des notes de frais. Extrait les informations de dépenses à partir des messages utilisateur.
        
            Catégories disponibles:
            - Taxi: Transport en taxi
            - Restaurant: Repas et restauration  
            - Hotel: Hébergement
            - Alcohol: Boissons alcoolisées (vin, bière, spiritueux)
            - Misc: Autres dépenses diverses

            Attention à:
            - Le montant doit être le total TTC (taxes comprises)
            - Indicateurs de reçu: "reçu OK", "avec reçu", "justificatif disponible"
            - Devises: EUR/€, CAD, USD/$
            - Nombre de participants pour restaurants: "x2", "2 personnes"
            - Formats de date dans différentes langues

            Utilise la fonction extract_expense pour retourner les données structurées."""
        },

        {"role": "user", "content": f"Extrait les informations de cette dépense: {message}\n{context}"}
    ]
    
    # Configuration de l'appel API
    payload = {
        "messages": messages,
        "functions": [function_def],
        "function_call": {"name": "extract_expense"},
        "temperature": 0
    }
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2025-01-01-preview"
    
    # Appel Azure OpenAI avec gestion d'erreurs
    try:
        logger.info("🤖 Appel Azure OpenAI en cours")
        with httpx.Client(timeout=30) as client:  # Timeout 30s pour éviter les blocages
            response = client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and result['choices'][0].get('message', {}).get('function_call'):
                    args = result['choices'][0]['message']['function_call']['arguments']
                    extracted_data = json.loads(args)
                    logger.info("✅ Extraction Azure OpenAI réussie")
                    return extracted_data
    except Exception as e:
        logger.warning(f"Azure OpenAI call failed: {e}")  # Log d'erreur sans exposer de données sensibles
    
    return None  # Retourne None pour déclencher le fallback heuristique

def agent_reply(message: str, attachments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    extracted = _azure_openai_extract(message, attachments) or _heuristic_extract(message, attachments)
    policy = get_policy()
    category = extracted['category']
    amount = float(extracted['amount_total'] or 0)
    currency = extracted['currency']
    has_receipt = bool(extracted['has_receipt'])

    cat = policy['categories'].get(category, policy['categories']['Misc'])
    if not cat['allowed']:
        return {'verdict':'REJECTED', 'reason': f'Catégorie interdite: {category}'}

    if cat.get('requires_receipt') and not has_receipt:
        return {'verdict':'NEEDS_APPROVAL', 'reason': f'Justificatif manquant pour {category}'}

    threshold = policy['approval_thresholds'].get(currency, 0)
    if isinstance(cat.get('max_per_item'), (int, float)) and amount > cat['max_per_item']:
        # Option: envoyer approbation immédiate
        send_approval('manager@example.com', {'category':category, 'amount':amount, 'currency':currency})
        return {'verdict':'NEEDS_APPROVAL', 'reason': f'Dépasse le plafond de catégorie ({category})'}

    if amount > threshold:
        send_approval('manager@example.com', {'category':category, 'amount':amount, 'currency':currency})
        return {'verdict':'NEEDS_APPROVAL', 'reason': f'Dépasse le seuil d\'approbation {currency}'}

    record = create_expense({
        'category': category,
        'amount_total': amount,
        'currency': currency,
        'has_receipt': has_receipt,
        'status': 'created'
    })
    return {'verdict':'OK', 'reason':'Conforme à la politique', 'record': record}
