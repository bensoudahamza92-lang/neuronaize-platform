# NeuronAIze

NeuronAIze is a Python Streamlit demo application for intelligent banking recommendations and cross-selling campaign orchestration.

The project demonstrates how a bank can segment customers, recommend relevant products, enrich recommendations with a product catalogue, simulate AI-assisted workflows, manage human validation, and measure subscription intent.

## Features

- Excel customer upload with automatic product-column detection using the `Produit -` prefix.
- Local customer clustering with KMedoids and Manhattan distance.
- Automatic cluster-count selection using KMedoids inertia and elbow detection.
- Customer profile view and product ownership display.
- Banking product recommendations based on similar customers in the predicted cluster.
- Product catalogue upload and validation.
- Catalogue-based product detail enrichment.
- Local RAG-style product chatbot based only on the uploaded catalogue.
- Workflow Agent IA for cross-selling campaign preparation.
- Promotion management with local Excel storage ignored by Git.
- Human-in-the-loop validation and AI Agent Console.
- JSON workflow engine with nodes `C1` to `C10`.
- Workflow guardrails and compliance checks.
- Simulated notifications only: no real email, SMS, push, signature, accounting, or subscription action is sent.
- Assisted subscription simulation with contract and terms generation.
- Subscription and campaign reporting dashboards.

## Project Structure

```text
.
├── app.py
├── recommender.py
├── product_catalog.py
├── product_rag.py
├── chatbot.py
├── workflow_agent.py
├── workflow_engine.py
├── workflow_executor.py
├── workflow_guardrails.py
├── workflow_schemas.py
├── workflow_reporting.py
├── compliance_checker.py
├── promotion_manager.py
├── campaign_manager.py
├── notification_simulator.py
├── subscription_agent.py
├── subscription_reporting.py
├── contract_generator.py
├── shared_models.py
├── ui_components.py
├── assets/
│   └── neuronaize-logo-baseline.png
├── requirements.txt
├── .env.example
└── .gitignore
```

## Screenshots

Add screenshots after publishing or running the app locally.

```text
docs/screenshots/01-recommendation-engine.png
docs/screenshots/02-product-catalogue.png
docs/screenshots/03-workflow-agent.png
docs/screenshots/04-ai-agent-console.png
docs/screenshots/05-subscription-reporting.png
```

## Installation

Clone the repository:

```bash
git clone https://github.com/bensoudahamza92-lang/neuronaize.git
cd neuronaize
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file if needed:

```bash
cp .env.example .env
```

## Run Locally

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Expected Customer Excel Format

Each row represents one customer.

- The first column is used as the customer code.
- Product columns must start with `Produit -`.
- Product columns must be encoded as `0` or `1`.
- Other columns are used as customer features for clustering.

Example:

```text
Code Client | Âge | Situation | Revenu annuel | Produit - Compte courant | Produit - Carte Premium
C001        | 42  | Salarié   | 62000         | 1                         | 0
```

## Expected Product Catalogue Format

The product catalogue Excel file must contain:

```text
Code produit
Nom produit
Colonne source bddf2
Catégorie
Description
Conditions d’éligibilité
Avantages
Limites / points de vigilance
Arguments commerciaux
Mots-clés chatbot
```

`Colonne source bddf2` must match the product column name in the customer file.

## Security and Data Notes

- The app is a local demo.
- No real campaign is sent.
- No real subscription is finalized.
- No external API is required for the current demo mode.
- Local Excel files, generated reports, uploads, `.env`, and temporary data are excluded from Git by `.gitignore`.
- Do not commit real customer data, API keys, bank secrets, or production catalogues.

## GitHub Publication

Recommended repository name:

```text
neuronaize
```

Target GitHub user:

```text
bensoudahamza92-lang
```

Before pushing, review ignored files with:

```bash
git status --ignored
```

Then initialize and push:

```bash
git init
git add .
git commit -m "Initial NeuronAIze Streamlit demo"
git branch -M main
git remote add origin https://github.com/bensoudahamza92-lang/neuronaize.git
git push -u origin main
```
