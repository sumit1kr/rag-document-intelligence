# Configuration Guide

## Overview

The HackRX RAG Document Q&A System uses a hierarchical configuration system with JSON files organized by functionality. This guide covers all configuration options and customization possibilities.

## Configuration Structure

\`\`\`
config/
├── api/                    # API-related configurations
│   ├── webhook.json       # Webhook settings
│   └── rate_limit.json    # Rate limiting configuration
├── models/                # Model configurations
│   └── model_config.json  # LLM model parameters
└── ui/                    # UI configurations
    └── components.json    # UI component settings
\`\`\`

## API Configuration

### Webhook Configuration (`config/api/webhook.json`)

Configure webhook endpoints for real-time event notifications.

\`\`\`json
{
  "url": "https://your-webhook-endpoint.com/webhook",
  "events": [
    "decision_made",
    "error_occurred", 
    "session_started",
    "session_ended",
    "batch_query_processed",
    "documents_processed"
  ],
  "secret": "your_webhook_secret_key",
  "timeout": 10,
  "retry_attempts": 3,
  "retry_delay": 5,
  "configured_at": "2024-01-01T12:00:00Z",
  "status": "active"
}
\`\`\`

**Configuration Options:**
- `url`: Webhook endpoint URL (required)
- `events`: Array of events to subscribe to
- `secret`: Secret key for HMAC signature verification
- `timeout`: Request timeout in seconds (default: 10)
- `retry_attempts`: Number of retry attempts on failure (default: 3)
- `retry_delay`: Delay between retries in seconds (default: 5)
- `status`: "active" or "inactive"

**Available Events:**
- `decision_made`: When a decision is made on a query
- `error_occurred`: When an error occurs during processing
- `session_started`: When a new session is created
- `session_ended`: When a session is terminated
- `batch_query_processed`: When batch processing completes
- `documents_processed`: When document processing completes

### Rate Limiting Configuration (`config/api/rate_limit.json`)

Configure API rate limiting to prevent abuse and ensure system stability.

\`\`\`json
{
  "enabled": true,
  "rate_limit": 60,
  "max_requests_per_minute": 60,
  "burst_limit": 10,
  "window_size": 60,
  "cleanup_interval": 300,
  "whitelist_ips": [
    "127.0.0.1",
    "192.168.1.0/24"
  ],
  "blacklist_ips": [],
  "updated_at": "2024-01-01T12:00:00Z"
}
\`\`\`

**Configuration Options:**
- `enabled`: Enable/disable rate limiting
- `rate_limit`: Requests per minute per IP
- `max_requests_per_minute`: Maximum requests per minute
- `burst_limit`: Maximum requests in a short burst
- `window_size`: Time window in seconds for rate calculation
- `cleanup_interval`: Cleanup interval for old entries (seconds)
- `whitelist_ips`: IPs exempt from rate limiting
- `blacklist_ips`: IPs that are blocked

## Model Configuration

### LLM Model Configuration (`config/models/model_config.json`)

Configure the language model parameters for optimal performance.

\`\`\`json
{
  "model_name": "llama3-70b-8192",
  "temperature": 0.1,
  "max_tokens": 4000,
  "top_p": 0.9,
  "top_k": 50,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stop_sequences": [],
  "timeout": 30,
  "retry_attempts": 3,
  "fallback_model": "llama3-8b-8192",
  "saved_at": "2024-01-01T12:00:00Z"
}
\`\`\`

**Configuration Options:**
- `model_name`: Primary model to use (Groq model names)
- `temperature`: Randomness in responses (0.0-1.0)
- `max_tokens`: Maximum tokens in response
- `top_p`: Nucleus sampling parameter
- `top_k`: Top-k sampling parameter
- `frequency_penalty`: Penalty for frequent tokens
- `presence_penalty`: Penalty for repeated tokens
- `stop_sequences`: Sequences that stop generation
- `timeout`: Request timeout in seconds
- `retry_attempts`: Number of retry attempts
- `fallback_model`: Model to use if primary fails

**Model Selection Guidelines:**
- `llama3-70b-8192`: Best quality, slower response
- `llama3-8b-8192`: Good balance of speed and quality
- `mixtral-8x7b-32768`: Good for longer contexts
- `gemma-7b-it`: Lightweight option

### Embedding Model Configuration

\`\`\`json
{
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "batch_size": 32,
  "normalize_embeddings": true,
  "cache_embeddings": true,
  "embedding_timeout": 30
}
\`\`\`

## UI Configuration

### Component Configuration (`config/ui/components.json`)

Configure UI components and theming for the Gradio interface.

\`\`\`json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide",
  "theme": {
    "primary_hue": "blue",
    "secondary_hue": "purple",
    "text_size": "lg",
    "spacing": "md",
    "radius": "md"
  }
}
\`\`\`

## Cache Configuration

### Cache Settings

Configure caching behavior for optimal performance.

\`\`\`json
{
  "enabled": true,
  "default_ttl": 3600,
  "max_size": 1000,
  "cleanup_interval": 300,
  "cache_types": {
    "document_embeddings": {
      "ttl": 7200,
      "max_size": 500,
      "enabled": true
    },
    "query_processing": {
      "ttl": 1800,
      "max_size": 200,
      "enabled": true
    },
    "decision_results": {
      "ttl": 3600,
      "max_size": 300,
      "enabled": true
    },
    "reasoning_results": {
      "ttl": 3600,
      "max_size": 200,
      "enabled": true
    }
  }
}
\`\`\`

## Security Configuration

### Security Settings

Configure security and compliance features.

\`\`\`json
{
  "encryption": {
    "enabled": true,
    "algorithm": "AES-256-GCM",
    "key_rotation_days": 90
  },
  "sessions": {
    "timeout": 3600,
    "max_sessions_per_user": 5,
    "secure_cookies": true
  },
  "audit": {
    "enabled": true,
    "retention_days": 365,
    "log_level": "INFO"
  },
  "gdpr": {
    "enabled": true,
    "data_retention_days": 730,
    "auto_delete_expired": true
  }
}
\`\`\`

## Database Configuration

### Vector Database Settings

Configure Pinecone vector database connection.

\`\`\`json
{
  "pinecone": {
    "environment": "us-west1-gcp-free",
    "index_name": "hackrx-doc-qa",
    "dimension": 384,
    "metric": "cosine",
    "replicas": 1,
    "shards": 1,
    "timeout": 30,
    "batch_size": 100
  }
}
\`\`\`

## Environment Variables

### Required Environment Variables

Set these in your `.env` file or system environment:

\`\`\`bash
# API Keys (Required)
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key

# Pinecone Configuration
PINECONE_ENVIRONMENT=us-west1-gcp-free
PINECONE_INDEX_NAME=hackrx-doc-qa

# Optional Configuration Overrides
MODEL_TEMPERATURE=0.1
MAX_TOKENS=4000
CACHE_TTL=3600
SESSION_TIMEOUT=3600
RATE_LIMIT=60

# Security Configuration
ENCRYPTION_KEY=your_32_character_encryption_key
SESSION_SECRET=your_session_secret_key

# Development Settings
DEBUG=false
LOG_LEVEL=INFO
\`\`\`

## Configuration Loading

### Configuration Priority

The system loads configuration in this order (later overrides earlier):

1. Default configuration (hardcoded)
2. Configuration files (`config/*.json`)
3. Environment variables
4. Runtime configuration updates

### Dynamic Configuration Updates

Some configurations can be updated at runtime through the API:

\`\`\`python
# Update model configuration
POST /api/v1/config/model
{
  "temperature": 0.2,
  "max_tokens": 3000
}

# Update rate limiting
POST /api/v1/config/rate-limit
{
  "rate_limit": 100
}
\`\`\`

## Configuration Validation

### Validation Rules

The system validates all configuration values:

- **Temperature**: Must be between 0.0 and 1.0
- **Max Tokens**: Must be between 100 and 8192
- **Rate Limit**: Must be between 1 and 1000
- **TTL**: Must be positive integer
- **URLs**: Must be valid HTTP/HTTPS URLs

### Configuration Testing

Test your configuration:

\`\`\`bash
# Validate all configurations
python -c "
from src.api.setup_api import APIKeyManager
config = APIKeyManager.load_and_validate()
print('✅ Configuration is valid')
"

# Test specific configuration
python -c "
import json
with open('config/models/model_config.json') as f:
    config = json.load(f)
    assert 0.0 <= config['temperature'] <= 1.0
    print('✅ Model configuration is valid')
"
\`\`\`

## Performance Tuning

### Recommended Settings

#### For High Throughput
\`\`\`json
{
  "temperature": 0.1,
  "max_tokens": 2000,
  "rate_limit": 120,
  "cache_ttl": 7200,
  "batch_size": 50
}
\`\`\`

#### For High Quality
\`\`\`json
{
  "temperature": 0.05,
  "max_tokens": 4000,
  "model_name": "llama3-70b-8192",
  "top_p": 0.95
}
\`\`\`

#### For Development
\`\`\`json
{
  "temperature": 0.2,
  "max_tokens": 1000,
  "rate_limit": 1000,
  "cache_ttl": 300,
  "debug": true
}
\`\`\`

## Troubleshooting

### Common Configuration Issues

#### 1. Invalid API Keys
\`\`\`bash
# Test API key validity
python -c "
import os
from groq import Groq
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
print('✅ Groq API key is valid')
"
\`\`\`

#### 2. Configuration File Errors
\`\`\`bash
# Validate JSON syntax
python -c "
import json
with open('config/models/model_config.json') as f:
    json.load(f)
print('✅ JSON is valid')
"
\`\`\`

#### 3. Permission Issues
\`\`\`bash
# Check file permissions
ls -la config/
chmod 644 config/*.json
\`\`\`

### Configuration Backup

Always backup your configuration before making changes:

\`\`\`bash
# Create backup
cp -r config config_backup_$(date +%Y%m%d)

# Restore from backup
cp -r config_backup_20240101 config
\`\`\`

---

**For advanced configuration scenarios, consult the source code or create an issue in the repository.**
