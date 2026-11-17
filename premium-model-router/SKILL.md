# Premium Model Router — Skill

## Pricing
- **Standalone:** $29 one-time — unlocks Model Router Pro
- **Bundle:** $39 one-time — Stock Alert System + Model Router (save $9)

Buy via [GitHub Sponsors](https://github.com/sponsors/Hermesplayground2?amount=39&frequency=one).

## Commands

### `route` — Intelligent model selection
Routes a request to the optimal model based on current conditions.

```bash
# Cost-optimized routing (default)
@jarvis route "Summarize this article: <article text>"

# Quality-first routing
@jarvis route --priority quality "Write a detailed analysis"

# Force specific provider
@jarvis route --provider nous "Simple question"

# Force specific model
@jarvis route --model poolside/laguna-s-2.1:free "Hello"
```

### `status` — System health dashboard
Shows current tier, supported models, and provider health.

```bash
@jarvis model status
```

### `dead` — Check dead model cache
Lists models currently marked as unavailable.

```bash
@jarvis model dead
```

### `refresh` — Clear dead model cache
Forces re-testing of all models on next use.

```bash
@jarvis model refresh
```

### `tiers` — Show pricing and features
Lists all available tiers and their features.

```bash
@jarvis model tiers
```

## Features

| Feature | Basic ($19) | Pro ($29) | Enterprise ($99/yr) |
|---------|-------------|-----------|---------------------|
| Cost optimization | ✓ | ✓ | ✓ |
| Basic fallback | ✓ | ✓ | ✓ |
| Quality routing | | ✓ | ✓ |
| Auto fallback | | ✓ | ✓ |
| Health monitoring | | ✓ | ✓ |
| Dead model cache | | ✓ | ✓ |
| Priority support | | | ✓ |
| Custom models | | | ✓ |
| Dedicated endpoint | | | ✓ |

## Supported Models (9 free, 9 paid)

**Free models (currently working):**
- poolside/laguna-s-2.1:free — quality: 7/10
- poolside/laguna-xs-2.1:free — quality: 6/10
- meituan/longcat-2.5-preview:free — quality: 7/10
- upstage/solar-mini4:free — quality: 7/10
- stepfun/step-5-preview:free — quality: 7/10

**Paid models:**
- stepfun/step-5-preview — $0.05/M tokens, quality: 8/10
- stepfun/step-3.7-flash — $0.08/M tokens, quality: 6/10

**Local models (Ollama):**
- llama3.2:latest — quality: 8/10
- qwen2.5:7b — quality: 7/10
- qwen2.5:14b — quality: 8/10

Note: 6 models with `:free` suffix are **broken** (return 400). Use non-suffixed versions.
