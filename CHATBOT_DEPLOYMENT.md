# Chatbot Deployment Guide: Cloudflare Workers AI

This guide explains how to deploy the chatbot using **Cloudflare Workers** so your API key never touches GitHub.

---

## Architecture

```
Browser (your site) → Cloudflare Worker → Cloudflare Workers AI / OpenAI / Anthropic
                          ↑
                    API Key stored securely
                    in Worker secrets (not in code)
```

---

## Option 1: Cloudflare Workers AI (Recommended - Free tier available)

**No external API key needed!** Uses Cloudflare's built-in models.

### Step 1: Enable Workers AI
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **Workers & Pages** → **Workers AI**
3. Enable Workers AI for your account (free tier: 100k requests/day)

### Step 2: Create the Worker
1. Go to **Workers & Pages** → **Create application** → **Create Worker**
2. Name it (e.g., `mcda-chatbot`)
3. Copy the contents of `cloudflare-worker.js` into the editor
4. **Important**: In the Worker settings, add an **AI Binding**:
   - Settings → Bindings → Add → AI
   - Variable name: `AI` (this matches `env.AI` in the code)

### Step 3: Deploy
1. Click **Deploy**
2. Your worker URL will be: `https://mcda-chatbot.your-account.workers.dev`

### Step 4: Update Your Site
In `app.js`, update the endpoint:
```javascript
const CHATBOT_API_ENDPOINT = 'https://mcda-chatbot.your-account.workers.dev';
```

---

## Option 2: OpenAI / Anthropic via Worker (If you prefer specific models)

### Step 1: Create the Worker (same as above)

### Step 2: Add API Key as Secret (NEVER put in code!)
1. In Worker settings → **Settings** → **Variables and Secrets**
2. Add **Secret**:
   - For OpenAI: Name `OPENAI_API_KEY`, Value: `sk-...`
   - For Anthropic: Name `ANTHROPIC_API_KEY`, Value: `sk-ant-...`
3. The worker code automatically detects which secret exists

### Step 3: Deploy & Update Endpoint (same as above)

---

## Option 3: Using Wrangler CLI (For local development)

```bash
# Install Wrangler
npm install -g wrangler

# Login
wrangler login

# Create project
mkdir mcda-chatbot-worker
cd mcda-chatbot-worker
cp ../cloudflare-worker.js src/index.js

# Create wrangler.toml
cat > wrangler.toml << 'EOF'
name = "mcda-chatbot"
main = "src/index.js"
compatibility_date = "2024-01-01"

# Enable Workers AI binding
[ai]
binding = "AI"
EOF

# Add secret (choose one)
wrangler secret put OPENAI_API_KEY
# OR
wrangler secret put ANTHROPIC_API_KEY

# Deploy
wrangler deploy
```

---

## Restricting CORS to Your Domain (Recommended)

In `cloudflare-worker.js`, change:
```javascript
'Access-Control-Allow-Origin': '*',
```
To:
```javascript
'Access-Control-Allow-Origin': 'https://madisonchinesedance.github.io',
```

---

## Cost Estimates

| Service | Free Tier | Paid |
|---------|-----------|------|
| Cloudflare Workers | 100k requests/day | $5/mo per 10M |
| Workers AI (Llama-3.1-8B) | 100k requests/day | Pay per token |
| OpenAI GPT-4o-mini | No | ~$0.15/1M tokens |
| Anthropic Haiku | No | ~$0.25/1M tokens |

---

## Testing Locally

```bash
# With Wrangler
wrangler dev

# Test with curl
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"message": "What classes do you offer?"}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS error | Check `Access-Control-Allow-Origin` matches your domain exactly |
| "AI binding not found" | Add AI binding in Worker settings → Bindings |
| 401 Unauthorized | Verify secret name matches (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) |
| Worker times out | Reduce `max_tokens` or increase timeout in `wrangler.toml` |

---

## Files in This Project

- `app.js` - Updated to call your Worker endpoint
- `cloudflare-worker.js` - Deploy this to Cloudflare Workers
- `CHATBOT_DEPLOYMENT.md` - This guide

---

## Next Steps After Deployment

1. Test the chatbot on your live site
2. Customize the system prompt in `cloudflare-worker.js` for MCDA-specific knowledge
3. Add conversation history for multi-turn conversations (optional)
4. Monitor usage in Cloudflare Dashboard → Workers → Metrics