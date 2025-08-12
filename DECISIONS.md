# Décisions d'implémentation

## Azure OpenAI

Problème : L'extraction heuristique était trop basique
Solution : Function calling avec un schéma JSON strict
J'ai mis les prompts en français parce que c'est un contexte français. Le schéma force les bonnes catégories et évite les erreurs de parsing.
Fallback automatique vers heuristique si Azure plante - ça marche toujours.
Timeout 30s pour pas que ça traîne.

## Gestion d'erreurs

Principe :

Azure OpenAI fail → heuristique
Fichier policy introuvable → erreur claire
Montant bizarre → extraction de ce qu'on peut

Les logs sont en INFO pour voir ce qui se passe, WARNING si problème.

## Sécurité

Variables d'environnement pour les secrets, jamais dans le code.
Les logs masquent les API keys. Les montants sont loggés parce que c'est nécessaire pour débugger les règles métier.

## Stockage

Choix : Fichiers JSON
C'est simple pour l'exercice. En vrai il faudrait une BDD mais là c'est juste pour tester.
expenses.json pour les dépenses validées, approvals.json pour les demandes.

## Tests

12 tests : les 4 demandés + quelques cas qui me semblaient logiques à tester.
J'ai mis des attentes multiples (OK/NEEDS_APPROVAL) sur les cas limites parce que ça dépend de l'extraction.

## Règles métier

Interprétation :

Catégorie interdite = REJECTED direct
Pas de reçu obligatoire = NEEDS_APPROVAL
Dépassement de plafond = NEEDS_APPROVAL
Dépassement de seuil = NEEDS_APPROVAL

Les approbations sont envoyées automatiquement à manager@example.com (mock).

## Limites connues

L'extraction heuristique est basique (regex)
Pas de gestion de concurrence sur les fichiers
Support limité aux devises EUR/CAD
Pas d'authentification sur l'API

## Améliorations possibles

Base de données proper
Meilleure extraction heuristique
Support plus de devises
Interface web pour les approbations
