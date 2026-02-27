# Swarm OS Phase 3: MCP Tool Usage Examples

This document provides examples of how the Swarm OS agents and external clients interact with the 10 synthesized MCP tools.

## 🌦️ Weather (Doc_weather)

**Port:** 9109  
**Endpoints:** `GET /data/2.5/weather`, `GET /data/2.5/forecast`

### Example: Current Weather

```bash
curl "http://localhost:9109/data/2.5/weather?q=Toronto&appid=YOUR_API_KEY"
```

---

## 💳 Payments (Doc_stripe)

**Port:** 9107  
**Endpoints:** `POST /v1/payment_intents`, `GET /v1/payment_intents`, `POST /v1/customers`

### Example: Create Payment Intent

```bash
curl -X POST http://localhost:9107/v1/payment_intents \
  -H "Content-Type: application/json" \
  -d '{"amount": 2000, "currency": "usd"}'
```

---

## 📁 DevOps (Doc_github)

**Port:** 9102  
**Endpoints:** `GET /repos/{owner}/{repo}`, `POST /repos/{owner}/{repo}/issues`

### Example: Create GitHub Issue

```bash
curl -X POST http://localhost:9102/repos/Shawn/Nexus/issues \
  -H "Content-Type: application/json" \
  -d '{"title": "Bug in TRM bridge", "body": "The recursive loop timed out."}'
```

---

## 📢 Social/Workplace (Doc_slack & Doc_discord)

**Ports:** 9105 (Slack), 9100 (Discord)

### Example: Slack Message

```bash
curl -X POST http://localhost:9105/api/chat.postMessage \
  -d '{"channel": "C123456", "text": "Deployment successful!"}'
```

---

## 🧠 AI/ML (Doc_huggingface)

**Port:** 9103  
**Endpoints:** `POST /models/{model_id}`

### Example: Text Generation

```bash
curl -X POST http://localhost:9103/models/gpt2 \
  -d '{"inputs": "The future of AI is swarms."}'
```

---

## 💾 Infrastructure (Doc_redis & Doc_elasticsearch)

**Ports:** 9104 (Redis), 9101 (Elasticsearch)

### Example: Redis Set Key

```bash
curl -X POST http://localhost:9104/set/session_001 \
  -d '{"user_id": "shawn", "role": "admin"}'
```

---

## 🎵 Media (Doc_spotify)

**Port:** 9106  
**Endpoints:** `GET /v1/search`, `POST /v1/me/player/play`

---

## 📞 Communication (Doc_twilio)

**Port:** 9108  
**Endpoints:** `POST /2010-04-01/Accounts/{AccountSid}/Messages.json`

---

## 🧠 Agent Usage (Natural Language)

Agents use these tools by incorporating their knowledge into reasoning.
**Prompt to Seeker:** "Use the weather-api to check if it's raining in Seattle."
**Prompt to Devo:** "Implement a Stripe payment flow using our learned stripe-api."

*All tools are auto-synthesized FastAPI servers with built-in `/health` and `/mcp/manifest` endpoints.*
