# Understand-Anything MCP License Backend

FastAPI backend for validating and generating license keys for the Understand-Anything MCP Server.

## Features
- `/validate` endpoint for key verification.
- Stripe webhook integration for automatic key generation upon purchase.
- Admin CLI for manual key generation.
- SQLite default database, with script to migrate to PostgreSQL.
- Dockerized and ready for Render Free Tier.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Environment Variables (`.env`):
   ```env
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   # DATABASE_URL=sqlite:///./licenses.db # Optional, defaults to sqlite
   ```

3. Run locally:
   ```bash
   uvicorn main:app --reload
   ```

## Admin CLI
Generate a key manually:
```bash
python generate_key.py --tier Pro --email test@example.com
```

## Stripe Webhook Setup
1. In your Stripe dashboard, create a webhook endpoint pointing to `https://your-domain.com/stripe/webhook`.
2. Listen for the `checkout.session.completed` event.
3. Grab the Signing Secret and set it as `STRIPE_WEBHOOK_SECRET`.
4. Ensure your Checkout Sessions pass `metadata: { tier: 'Pro' }` to properly assign the tier.

## Migration to Postgres
When you outgrow SQLite, provision a PostgreSQL database (e.g., on Render):
1. Set `POSTGRES_URL`.
2. Run `python migrate_to_postgres.py` to copy data.
3. Update `DATABASE_URL` for your app to point to Postgres.
