# Demo — CI/CD d'agents Microsoft Foundry avec GitHub + VS Code

**Objectif de la démo :** montrer le cycle de vie complet d'un agent Foundry piloté par le code —
**créer** un agent dans VS Code, le **versionner** dans Git, le **déployer automatiquement vers un projet de test**
via GitHub Actions, puis le **vérifier** par un smoke-test — le tout sans quitter l'IDE.

> Outils utilisés : **Microsoft Foundry Toolkit for VS Code** (ex-« AI Toolkit », GA depuis avril 2026),
> **Azure Developer CLI (`azd`) + extension agents Foundry**, **GitHub Actions**.

---

## 1. L'histoire que raconte la démo (3 minutes au tableau)

| Étape | Ce que vous montrez | Outil |
|-------|---------------------|-------|
| **Créer** | Scaffolder un agent hébergé depuis la palette VS Code | Foundry Toolkit |
| **Versionner** | `agent.yaml` = manifeste déclaratif suivi dans Git ; chaque `git push` = une version | Git / GitHub |
| **Déployer (test)** | Le push sur `main` déclenche GitHub Actions → `azd deploy` vers le **projet de test** | GitHub Actions + `azd` |
| **Vérifier** | Le pipeline invoque l'agent et échoue si la réponse est vide | `azd ai agent invoke` |

Le message clé pour le client : **l'agent est traité comme de l'« infrastructure-as-config »** — sa définition
(nom, modèle, instructions, outils, protocole) vit dans un fichier YAML versionné, pas dans un clic sur un portail.

---

## 2. Prérequis (une fois)

- **VS Code** + extension **Microsoft Foundry Toolkit** (Marketplace).
- **Azure Developer CLI** `azd` ≥ 1.21.3 — `azd auth login`.
- **Deux projets Microsoft Foundry** dans votre abonnement : `foundry-dev` et `foundry-test`
  (le second est la cible du pipeline). Chacun avec **un modèle déployé** (ex. `gpt-4o-mini`).
- **Python 3.13+** (runtime des agents hébergés) et **Azure CLI**.
- Un **dépôt GitHub** (celui-ci, poussé chez vous).

> 💡 Pour une démo minimale, un seul projet suffit : nommez-le « test » et sautez le projet dev.

---

## 3. Créer l'agent (VS Code Foundry Toolkit)

1. Ouvrez la **palette** (`Ctrl+Shift+P`) → **`Foundry Toolkit: Create a New Hosted Agent`**.
2. Choisissez : langage **Python**, framework **Microsoft Agent Framework**, protocole **Responses API**, un template simple.
3. Choisissez **« Configure with Microsoft Foundry »** pour pré-remplir projet + modèle (`foundry-dev`).
4. Le toolkit génère l'arborescence : `agent.yaml`, code de l'agent, `azure.yaml`, dossier `infra/` (Bicep).
5. Testez en local avec l'**Agent Playground** / **Agent Inspector** (traces, points d'arrêt).

> Ce dépôt fournit des exemples de `agent.yaml` et `azure.yaml` pour que vous voyiez la forme attendue.
> En pratique, **laissez le toolkit/`azd` générer** `infra/` et le Dockerfile — ne les écrivez pas à la main.

Alternative 100 % terminal (équivalent sans l'IDE) :

```bash
azd init -t Azure-Samples/azd-ai-starter-basic --location francecentral
azd ai agent init -m https://github.com/microsoft-foundry/foundry-samples/blob/main/samples/python/hosted-agents/langgraph/calculator-agent/agent.yaml
```

---

## 4. Versionner (Git)

Le fichier **`agent.yaml`** est le cœur versionné. Committez-le comme n'importe quel code :

```bash
git add agent.yaml azure.yaml .github/ tests/
git commit -m "feat(agent): weather concierge v1 — instructions initiales"
git push origin main
```

**Deux niveaux de versioning se combinent :**
- **Côté source** : chaque commit/tag Git est une version reproductible de la définition.
- **Côté Foundry** : le service **Foundry Agent Service crée une nouvelle *version d'agent*** à chaque déploiement,
  visible dans le portail Foundry (page de l'agent → onglet Versions) et via `azd ai agent show`.
  Vous pouvez ainsi **revenir à une version antérieure** côté service, indépendamment du rollback Git.

Bonne pratique démo : taguez vos versions — `git tag agent-v1 && git push --tags`.

---

## 5. Déployer vers le projet de test (GitHub Actions)

Le workflow **`.github/workflows/deploy-test.yml`** (repris du quickstart officiel Foundry) :
se connecte à Azure en **OIDC** (sans secret), sélectionne l'environnement `test`, lance `azd deploy`
vers le **projet Foundry de test**, affiche le statut de l'agent, puis exécute le smoke-test.

### 5.1 Configurer l'accès sans secret (OIDC)

1. Créez une **app registration Entra ID** avec un **federated credential** pour ce dépôt GitHub
   (sujet : `repo:<org>/<repo>:ref:refs/heads/main`).
2. Sur le **projet Foundry de test**, assignez à cette identité les rôles :
   **Foundry User** + **Contributor** (déploiement en mode `code` ; ajoutez les rôles ACR si mode `container`).

### 5.2 Renseigner les variables du dépôt

GitHub → **Settings → Secrets and variables → Actions → Variables**, créez :

| Variable | Où la trouver |
|----------|---------------|
| `AZURE_CLIENT_ID` | App registration OIDC |
| `AZURE_TENANT_ID` | `.azure/<env>/.env` ou portail |
| `AZURE_SUBSCRIPTION_ID` | idem |
| `AZURE_LOCATION` | idem (ex. `francecentral`) |
| `FOUNDRY_PROJECT_ENDPOINT` | Projet **de test** (portail Foundry) |
| `AZURE_AI_PROJECT_ID` | idem |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Nom du déploiement de modèle (ex. `gpt-4o-mini`) |

> Toutes ces valeurs (sauf `AZURE_CLIENT_ID`) sont dans votre fichier local `.azure/<projet>/.env` après un premier `azd provision`/`azd deploy`.

### 5.3 Amorcer une première fois

Le pipeline **met à jour** un agent existant — il faut donc l'avoir créé au moins une fois :

```bash
azd provision      # crée les ressources du projet de test
azd deploy         # premier déploiement de l'agent
```

---

## 6. Vérifier (smoke-test)

Deux niveaux de vérification :

1. **Dans le pipeline** : l'étape *Test agent* appelle `azd ai agent invoke "<prompt>"` et **échoue si la réponse est vide**
   (voir le workflow). C'est le garde-fou minimal « l'agent répond après déploiement ».
2. **En local / dans VS Code** : `tests/test_agent_smoke.py` est un test **pytest** exécutable depuis le
   **Test Explorer** du Foundry Toolkit (le toolkit sait lancer des évaluations continues en syntaxe pytest).

```bash
pip install -r tests/requirements.txt
AGENT_PROJECT_DIR=. pytest tests/ -v
```

---

## 7. Le « moment démo » (à jouer en live)

1. Dans VS Code, ouvrez `agent.yaml` et changez une ligne d'`instructions`
   (ex. ajoutez « Réponds toujours en français et termine par un emoji météo »).
2. `git commit -am "feat(agent): réponses en FR + emoji" && git push`
3. Basculez sur l'onglet **Actions** de GitHub → le workflow **Deploy to Test** démarre.
4. Il déploie vers le projet de test, **crée une nouvelle version d'agent**, et le smoke-test passe au vert. ✅
5. Ouvrez le portail Foundry → l'agent affiche **v2** ; testez-le dans le playground : il répond désormais en français.

Voilà le cycle complet **créer → versionner → déployer(test) → vérifier**, entièrement piloté par Git.

---

## Structure du dépôt

```
foundry-agent-cicd-demo/
├── README.md                       # ce guide (script de démo)
├── agent.yaml                      # manifeste déclaratif de l'agent (VERSIONNÉ)
├── azure.yaml                      # config projet azd (service + modèle)
├── .github/workflows/
│   └── deploy-test.yml             # pipeline CI/CD → projet de test (OIDC + azd)
├── tests/
│   ├── test_agent_smoke.py         # smoke-test pytest (vérif réponse non vide)
│   └── requirements.txt
└── .gitignore
```

## Références officielles

- Quickstart CI/CD agent hébergé (workflow source) : `learn.microsoft.com/azure/foundry/agents/quickstarts/set-up-cicd-hosted-agent`
- Extension `azd` agents Foundry : `learn.microsoft.com/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension`
- Foundry Toolkit for VS Code : `learn.microsoft.com/azure/foundry/how-to/develop/get-started-projects-vs-code`
- Agents déclaratifs (schéma YAML) : `learn.microsoft.com/agent-framework/agents/declarative`
