"""
Authentification par clé API — PSG Analytics API.

Utilisation : ajouter `Depends(verify_api_key)` sur chaque endpoint protégé.
La clé attendue est lue depuis la variable d'environnement API_KEY.
"""
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# Nom du header HTTP attendu dans chaque requête
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """
    Dépendance FastAPI : vérifie que le header X-API-Key est présent et correct.

    - Clé absente ou vide  → 401
    - Clé incorrecte       → 401
    - Clé correcte         → retourne la clé (pour éventuellement logger)

    Raises:
        RuntimeError: si la variable d'env API_KEY n'est pas définie côté serveur.
        HTTPException 401: si la clé est absente ou invalide.
    """
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        # Erreur de config serveur, pas une erreur client
        raise RuntimeError(
            "Variable d'environnement API_KEY non définie. "
            "Définis-la dans .env (local) ou dans les secrets Cloud Run (prod)."
        )

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API manquante ou invalide. Fournis le header X-API-Key.",
        )

    return api_key
