import logging  # Ajouté pour voir les logs durant les tests
from app.agent import agent_reply
from dotenv import load_dotenv  # Ajouté pour charger les variables d'environnement


# Chargement des variables d'environnement depuis .env
load_dotenv()

# Configuration basique des logs pour voir les appels Azure OpenAI
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)

SCENARIOS = [
    { 'title': 'Taxi EUR 60, reçu OK', 'message': 'Taxi 60€ à Paris hier, reçu OK', 'expected_one_of': ['OK'] },
    { 'title': 'Restaurant CAD 120, participants manquants', 'message': 'Restaurant 120 CAD à Montréal, je n\'ai pas indiqué les participants', 'expected_one_of': ['NEEDS_APPROVAL','OK'] },
    { 'title': 'Achat d\'alcool 40€', 'message': 'Achat de vin 40€', 'expected_one_of': ['REJECTED'] },
    { 'title': 'Hôtel 180€, reçu OK', 'message': 'Hôtel 180€ reçu OK', 'expected_one_of': ['NEEDS_APPROVAL','OK'] },
# Quelques cas supplémentaires simples
    { 'title': 'Taxi sans reçu', 'message': 'Taxi 40€ sans justificatif', 'expected_one_of': ['NEEDS_APPROVAL'] },
    { 'title': 'Montant très élevé', 'message': 'Restaurant 200€ avec reçu', 'expected_one_of': ['NEEDS_APPROVAL'] },
    { 'title': 'Taxi exactement au plafond', 'message': 'Taxi 80€ avec reçu', 'expected_one_of': ['OK', 'NEEDS_APPROVAL'] },  # Peut échouer avec extraction heuristique
    { 'title': 'Restaurant exactement au seuil EUR', 'message': 'Restaurant 120€ avec justificatif', 'expected_one_of': ['NEEDS_APPROVAL', 'OK'] },
    { 'title': 'Hôtel sans reçu', 'message': 'Nuit d\'hôtel 150€ pas de reçu', 'expected_one_of': ['NEEDS_APPROVAL'] },
    { 'title': 'Dépense misc faible', 'message': 'Achat fournitures 30€', 'expected_one_of': ['OK'] },
    { 'title': 'Message ambigu', 'message': 'Dépense de 75€ hier', 'expected_one_of': ['OK', 'NEEDS_APPROVAL'] },
    { 'title': 'Montant avec virgule', 'message': 'Taxi 45,50€ avec reçu', 'expected_one_of': ['OK', 'NEEDS_APPROVAL'] },  # Peut échouer avec extraction heuristique


# Tests avec données OCR (simulent des reçus scannés)
    { 
        'title': 'OCR Taxi Paris', 
        'message': 'Voici mon reçu de taxi', 
        'expected_one_of': ['OK'],
        'attachments': {
            'ocr': {
                'vendor': 'Taxi Parisien',
                'date': '2025-06-12', 
                'amount_total': 60.0,
                'currency': 'EUR',
                'has_receipt': True
            }
        }
    },
    { 
        'title': 'OCR Restaurant Montreal', 
        'message': 'Restaurant avec clients', 
        'expected_one_of': ['NEEDS_APPROVAL'],  # 120 CAD > 100 (plafond Restaurant)
        'attachments': {
            'ocr': {
                'vendor': 'Bistro du Vieux-Port',
                'date': '2025-05-28',
                'amount_total': 120.0, 
                'currency': 'CAD',
                'has_receipt': True
            }
        }
    },
]

def main():
    passed = 0
    for s in SCENARIOS:
        out = agent_reply(s['message'], {})
        ok = out['verdict'] in s['expected_one_of']
        print(f"- {s['title']}: got={out['verdict']} expected_one_of={ '/'.join(s['expected_one_of']) } {'✅' if ok else '❌'}")
        if ok: passed += 1
    print(f"\nSummary: {passed}/{len(SCENARIOS)} passed")

if __name__ == '__main__':
    main()
