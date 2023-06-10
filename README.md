# Filler

Filler continuously fills relations between blocks and transactions into a nosql database. 
This is used only for blockchains that do not expose that relationship in their API.

## How to run locally
Define the following variables in `.env` file:
```dotenv
NODE_BLOCKCHAIN="eos"
NODE_URL="<node_url>"
NODE_TOKEN="<node_token>"
```

### Terminal
```bash
./scripts/entrypoint
```

### Docker compose
```bash
docker-compose up -d
```
