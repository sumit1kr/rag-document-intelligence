#!/usr/bin/env python3
"""
Test script for webhook functionality
"""

import json
import os
from src.utils.app_state import app_state
from src.api.endpoints import APIEndpoints

def test_webhook():
    """Test webhook functionality"""
    print("🧪 Testing Webhook Functionality")
    print("=" * 50)
    
    # Initialize app state
    print("1. Initializing application...")
    app_state.initialize()
    print("✅ Application initialized")
    
    # Create API endpoints
    print("2. Creating API endpoints...")
    api = APIEndpoints(app_state.qa_chain, app_state.cache_manager, app_state.security_manager)
    print("✅ API endpoints created")
    
    # Check webhook configuration
    print("3. Checking webhook configuration...")
    if api.webhook_endpoints:
        for webhook_id, config in api.webhook_endpoints.items():
            print(f"   Webhook ID: {webhook_id}")
            print(f"   URL: {config.get('url', 'No URL')}")
            print(f"   Events: {config.get('events', [])}")
            print(f"   Active: {config.get('active', False)}")
    else:
        print("   ❌ No webhook endpoints configured")
    
    # Test webhook triggering
    print("4. Testing webhook triggering...")
    test_data = {
        "query": "Test query for webhook",
        "session_id": "test_session",
        "user_id": "test_user",
        "result": "Test result",
        "decision": {"status": "Approved", "amount": "₹10,000"},
        "processing_time": 1.5,
        "audit_id": "test_audit_123"
    }
    
    print("   Triggering 'decision_made' webhook...")
    api._trigger_webhooks("decision_made", test_data)
    print("   ✅ Webhook triggered")
    
    print("5. Testing webhook with different event...")
    api._trigger_webhooks("query_processed", test_data)
    print("   ✅ Query processed webhook triggered")
    
    print("6. Testing error webhook...")
    error_data = {
        "error": "Test error message",
        "query": "Test query",
        "session_id": "test_session",
        "user_id": "test_user"
    }
    api._trigger_webhooks("error_occurred", error_data)
    print("   ✅ Error webhook triggered")
    
    print("\n🎉 Webhook testing completed!")
    print("Check your webhook endpoint (webhook.site) for incoming requests")

if __name__ == "__main__":
    test_webhook() 