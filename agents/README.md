# Foundry Agents

This folder holds Microsoft Foundry hosted agents managed with the Azure Developer CLI (`azd`) and the `azure.ai.agents` extension. Two environments are configured against two Foundry projects:

| Environment | azd env | Foundry project |
|-------------|---------|-----------------|
| dev  | `dev`  | `forvia-proj-dev`  |
| test | `test` | `forvia-proj-test` |

## Prerequisites

```pwsh
azd extension install azure.ai.agents
azd auth login
```

## Create / scaffold an agent

```pwsh
azd ai agent sample list --featured-only --language python --output json
azd ai agent init -m "<manifestUrl>" --deploy-mode code --runtime python_3_13 --entry-point main.py
```

This writes `azure.yaml`, `src/<agent>/agent.yaml`, and `.agentignore`.

## Edit an agent

Edit `src/<agent>/agent.yaml` (name, model, instructions, tools) and the entry point (e.g. `main.py`). Run locally:

```pwsh
azd ai agent run
azd ai agent invoke --local "hello"
```

## Switch environments and deploy

```pwsh
azd env select dev      # or: azd env select test
azd provision           # first time per project
azd deploy
```

Fill in the real project endpoints in [.foundry/agent-metadata.yaml](.foundry/agent-metadata.yaml).
