# API Documentation

## Overview

The HackRX RAG Document Q&A System provides a comprehensive REST API for programmatic access to all system features including query processing, document analysis, audit trails, and administrative functions.

## Base URL

\`\`\`
http://localhost:5000
\`\`\`

## Authentication

The API supports session-based authentication for secure access to protected endpoints.

### Create Session
\`\`\`http
POST /api/v1/session
Content-Type: application/json

{
  "user_id": "user123",
  "permissions": ["read", "query", "admin"]
}
\`\`\`

**Response:**
\`\`\`json
{
  "session_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": "user123",
  "permissions": ["read", "query", "admin"],
  "expires_in": 3600
}
\`\`\`

## Core Endpoints

### Health Check

Check system health and status.

\`\`\`http
GET /health
\`\`\`

**Response:**
\`\`\`json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
\`\`\`

### Process Single Query

Process a single document query with intelligent analysis.

\`\`\`http
POST /api/v1/query
Content-Type: application/json

{
  "query": "46-year-old male, knee surgery in Pune, 3-month policy",
  "session_id": "session_123",
  "user_id": "user_456",
  "session_token": "optional_auth_token"
}
\`\`\`

**Response:**
\`\`\`json
{
  "query": "46-year-old male, knee surgery in Pune, 3-month policy",
  "decision": "approved",
  "amount": "₹50000",
  "confidence": 0.85,
  "justification": "Knee surgery is covered for patients aged 18-65. The policy duration meets the minimum requirement of 3 months.",
  "evidence_clauses": [
    {
      "clause_id": "section_3_2",
      "text": "Knee surgery is covered under the policy for patients aged 18-65...",
      "relevance_score": 0.95,
      "decision_impact": "positive"
    }
  ],
  "parsed_entities": {
    "age": "46",
    "gender": "M",
    "procedure": "knee surgery",
    "location": "Pune",
    "policy_duration": "3 months"
  },
  "structured_response": {
    "decision": {
      "status": "approved",
      "amount": "₹50000",
      "confidence": 0.85
    },
    "evidence": {
      "total_clauses": 3,
      "supporting_clauses": 2,
      "opposing_clauses": 0
    }
  },
  "audit_id": "audit_123456789",
  "processing_time": 1.2,
  "timestamp": "2024-01-01T12:00:00Z"
}
\`\`\`

### Process Batch Queries

Process multiple queries in a single request for efficiency.

\`\`\`http
POST /api/v1/batch-query
Content-Type: application/json

{
  "queries": [
    {
      "query": "Root canal treatment for 25-year-old",
      "session_id": "session_123",
      "user_id": "user_456"
    },
    {
      "query": "Emergency surgery for 50-year-old male",
      "session_id": "session_123", 
      "user_id": "user_456"
    }
  ],
  "session_token": "optional_auth_token"
}
\`\`\`

**Response:**
\`\`\`json
{
  "batch_id": "batch_1704110400.123",
  "total_queries": 2,
  "results": [
    {
      "query": "Root canal treatment for 25-year-old",
      "result": {
        "decision": "approved",
        "amount": "₹15000",
        "confidence": 0.92
      },
      "status": "success"
    },
    {
      "query": "Emergency surgery for 50-year-old male",
      "result": {
        "decision": "approved",
        "amount": "₹75000",
        "confidence": 0.88
      },
      "status": "success"
    }
  ]
}
\`\`\`

### Document Processing

Upload and process documents for knowledge base integration.

\`\`\`http
POST /api/v1/documents
Content-Type: application/json

{
  "documents": [
    {
      "id": "doc_123",
      "type": "pdf",
      "content": "base64_encoded_content",
      "metadata": {
        "filename": "policy_document.pdf",
        "source": "insurance_company"
      }
    }
  ],
  "session_token": "optional_auth_token"
}
\`\`\`

**Response:**
\`\`\`json
{
  "processing_id": "proc_1704110400.456",
  "total_documents": 1,
  "results": [
    {
      "document_id": "doc_123",
      "type": "pdf",
      "status": "processed",
      "chunks_created": 25,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ]
}
\`\`\`

## Analytics Endpoints

### Audit Trail

Retrieve comprehensive audit logs with filtering options.

\`\`\`http
GET /api/v1/audit-trail?session_id=session_123&start_date=2024-01-01&end_date=2024-01-31&action_type=decision_made
\`\`\`

**Query Parameters:**
- `session_id` (optional): Filter by session ID
- `user_id` (optional): Filter by user ID
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `action_type` (optional): Filter by action type

**Response:**
\`\`\`json
{
  "audit_trail": [
    {
      "audit_id": "audit_123456789",
      "timestamp": "2024-01-01T12:00:00Z",
      "session_id": "session_123",
      "user_id": "user_456",
      "action": "decision_made",
      "query": "46-year-old male, knee surgery",
      "decision": {
        "status": "approved",
        "amount": "₹50000",
        "confidence": 0.85
      },
      "processing_time": 1.2
    }
  ],
  "total_entries": 1,
  "filters": {
    "session_id": "session_123",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
\`\`\`

### Cache Statistics

Get performance metrics and cache statistics.

\`\`\`http
GET /api/v1/cache/stats
\`\`\`

**Response:**
\`\`\`json
{
  "hit_rate": "85.2%",
  "total_cache_entries": 1247,
  "cache_size_mb": 156.7,
  "cache_types": {
    "document_embeddings": {
      "entries": 423,
      "hit_rate": "92.1%",
      "size_mb": 89.3
    },
    "query_processing": {
      "entries": 567,
      "hit_rate": "78.4%",
      "size_mb": 45.2
    },
    "decision_results": {
      "entries": 257,
      "hit_rate": "88.9%",
      "size_mb": 22.2
    }
  },
  "last_cleanup": "2024-01-01T11:30:00Z"
}
\`\`\`

### Security Statistics

Get security metrics and compliance status.

\`\`\`http
GET /api/v1/security/stats
\`\`\`

**Response:**
\`\`\`json
{
  "active_sessions": 15,
  "total_users": 42,
  "security_events": {
    "login_attempts": 156,
    "failed_logins": 3,
    "data_access_events": 1247,
    "gdpr_requests": 2
  },
  "compliance_status": {
    "gdpr_compliant": true,
    "data_retention_policy": "active",
    "encryption_enabled": true,
    "audit_logging": "enabled"
  },
  "last_security_scan": "2024-01-01T10:00:00Z"
}
\`\`\`

## GDPR Compliance Endpoints

### Export User Data

Export all data associated with a user for GDPR compliance.

\`\`\`http
GET /api/v1/gdpr/export/user123
\`\`\`

**Response:**
\`\`\`json
{
  "user_id": "user123",
  "export_timestamp": "2024-01-01T12:00:00Z",
  "session_data": [
    {
      "session_id": "session_123",
      "created_at": "2024-01-01T10:00:00Z",
      "queries_count": 15
    }
  ],
  "query_history": [
    {
      "timestamp": "2024-01-01T11:00:00Z",
      "query": "knee surgery coverage",
      "decision": "approved"
    }
  ],
  "decisions": [
    {
      "decision_id": "dec_123",
      "timestamp": "2024-01-01T11:00:00Z",
      "status": "approved",
      "amount": "₹50000"
    }
  ]
}
\`\`\`

### Delete User Data

Delete all data associated with a user for GDPR compliance.

\`\`\`http
DELETE /api/v1/gdpr/delete/user123
\`\`\`

**Response:**
\`\`\`json
{
  "status": "success",
  "message": "Data deleted for user user123",
  "deleted_items": {
    "sessions": 3,
    "queries": 15,
    "decisions": 8,
    "audit_entries": 23
  },
  "deletion_timestamp": "2024-01-01T12:00:00Z"
}
\`\`\`

## Webhook Management

### Register Webhook

Register a webhook endpoint for real-time notifications.

\`\`\`http
POST /api/v1/webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["decision_made", "error_occurred"],
  "secret": "optional_webhook_secret"
}
\`\`\`

**Response:**
\`\`\`json
{
  "webhook_id": "webhook_1704110400.789",
  "status": "registered",
  "config": {
    "url": "https://your-app.com/webhook",
    "events": ["decision_made", "error_occurred"],
    "active": true,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
\`\`\`

### Unregister Webhook

Remove a webhook endpoint.

\`\`\`http
DELETE /api/v1/webhooks/webhook_1704110400.789
\`\`\`

**Response:**
\`\`\`json
{
  "status": "unregistered",
  "webhook_id": "webhook_1704110400.789"
}
\`\`\`

## Session Management

### Invalidate Session

Invalidate an active session for security.

\`\`\`http
DELETE /api/v1/session/eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
\`\`\`

**Response:**
\`\`\`json
{
  "status": "invalidated",
  "session_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
\`\`\`

## Webhook Events

The system sends webhook notifications for various events:

### Decision Made Event
\`\`\`json
{
  "event_type": "decision_made",
  "webhook_id": "webhook_123",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "query": "46-year-old male, knee surgery",
    "session_id": "session_123",
    "user_id": "user_456",
    "result": "approved",
    "decision": {
      "status": "approved",
      "amount": "₹50000",
      "confidence": 0.85
    },
    "processing_time": 1.2,
    "audit_id": "audit_123456789"
  }
}
\`\`\`

### Error Occurred Event
\`\`\`json
{
  "event_type": "error_occurred",
  "webhook_id": "webhook_123",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "error": "Document processing failed",
    "query": "invalid query format",
    "session_id": "session_123",
    "user_id": "user_456"
  }
}
\`\`\`

## Error Handling

### Standard Error Response
\`\`\`json
{
  "error": "Error description",
  "error_code": "INVALID_REQUEST",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
\`\`\`

### Common Error Codes
- `INVALID_REQUEST` (400): Malformed request
- `UNAUTHORIZED` (401): Invalid or missing authentication
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `RATE_LIMITED` (429): Rate limit exceeded
- `INTERNAL_ERROR` (500): Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default Limit**: 60 requests per minute per IP
- **Burst Limit**: 10 requests per second
- **Headers**: Rate limit information in response headers

\`\`\`http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704110460
\`\`\`

## SDK Examples

### Python SDK Example
\`\`\`python
import requests

class HackRXClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session_token = None
    
    def create_session(self, user_id, permissions):
        response = requests.post(f"{self.base_url}/api/v1/session", json={
            "user_id": user_id,
            "permissions": permissions
        })
        self.session_token = response.json()["session_token"]
        return self.session_token
    
    def query(self, query_text, session_id, user_id):
        response = requests.post(f"{self.base_url}/api/v1/query", json={
            "query": query_text,
            "session_id": session_id,
            "user_id": user_id,
            "session_token": self.session_token
        })
        return response.json()

# Usage
client = HackRXClient()
client.create_session("user123", ["read", "query"])
result = client.query("46-year-old male, knee surgery", "session_123", "user123")
print(result["decision"])
\`\`\`

### JavaScript SDK Example
\`\`\`javascript
class HackRXClient {
    constructor(baseUrl = 'http://localhost:5000') {
        this.baseUrl = baseUrl;
        this.sessionToken = null;
    }
    
    async createSession(userId, permissions) {
        const response = await fetch(`${this.baseUrl}/api/v1/session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, permissions })
        });
        const data = await response.json();
        this.sessionToken = data.session_token;
        return this.sessionToken;
    }
    
    async query(queryText, sessionId, userId) {
        const response = await fetch(`${this.baseUrl}/api/v1/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: queryText,
                session_id: sessionId,
                user_id: userId,
                session_token: this.sessionToken
            })
        });
        return await response.json();
    }
}

// Usage
const client = new HackRXClient();
await client.createSession('user123', ['read', 'query']);
const result = await client.query('46-year-old male, knee surgery', 'session_123', 'user123');
console.log(result.decision);
\`\`\`

---

**For more examples and advanced usage, see the `/examples` directory in the repository.**
