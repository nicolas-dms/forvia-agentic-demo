"""Smoke-test de l'agent Foundry déployé.

Vérifie que l'agent répond (réponse non vide) après déploiement, en s'appuyant
sur la commande documentée `azd ai agent invoke`. Exécutable en local ou depuis
le Test Explorer du Microsoft Foundry Toolkit (évaluations continues pytest).

Usage local :
    pip install -r tests/requirements.txt
    AGENT_PROJECT_DIR=. pytest tests/ -v
"""
from __future__ import annotations

import os
import subprocess

DEFAULT_PROMPT = "Hello from CI. Réponds par une courte confirmation que tu es opérationnel."


def _invoke_agent(prompt: str) -> subprocess.CompletedProcess[str]:
    """Invoque l'agent déployé via l'Azure Developer CLI (extension Foundry)."""
    return subprocess.run(
        ["azd", "ai", "agent", "invoke", prompt, "--no-prompt"],
        cwd=os.environ.get("AGENT_PROJECT_DIR", "."),
        capture_output=True,
        text=True,
    )


def test_agent_returns_non_empty_response() -> None:
    prompt = os.environ.get("AGENT_TEST_PROMPT", DEFAULT_PROMPT)
    result = _invoke_agent(prompt)

    assert result.returncode == 0, (
        f"`azd ai agent invoke` a échoué (code {result.returncode}).\n"
        f"stderr:\n{result.stderr}"
    )

    response = (result.stdout or "").strip()
    assert response, "L'agent a renvoyé une réponse vide."
    print(f"Réponse de l'agent :\n{response}")
