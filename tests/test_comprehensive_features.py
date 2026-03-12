#!/usr/bin/env python3
"""
Comprehensive test script for all enhanced features
Tests consistency validation, audit trail, decision explanation, caching, security, and API endpoints
"""

import json
import time
from datetime import datetime, timedelta
from src.core.consistency_validator import ConsistencyValidator
from src.utils.audit_trail import AuditTrail
from src.core.decision_explainer import DecisionExplainer
from src.utils.cache_manager import CacheManager
from src.utils.security_manager import SecurityManager
from src.api.endpoints import APIEndpoints

def create_mock_qa_chain():
    """Create a mock QA chain for testing"""
    class MockQAChain:
        def __init__(self):
            self.audit_trail = AuditTrail()
        
        def get_audit_trail(self, **kwargs):
            return self.audit_trail.get_audit_trail(**kwargs)
        
        def get_decision_history(self, **kwargs):
            return self.audit_trail.get_decision_history(**kwargs)
        
        def export_audit_report(self, **kwargs):
            return self.audit_trail.export_audit_report(**kwargs)
    
    return MockQAChain()

def test_consistency_validation():
    """Test consistency validation functionality"""
    print("🧪 Testing Consistency Validation")
    print("=" * 60)
    
    validator = ConsistencyValidator()
    
    # Test cases
    test_cases = [
        {
            "name": "Standard Approval",
            "decision": {"status": "approved", "amount": "₹50000", "confidence": 0.85},
            "query_context": {
                "parsed_entities": {
                    "age": "46",
                    "gender": "M",
                    "procedure": "knee surgery",
                    "location": "Pune",
                    "policy_duration": "3 months"
                }
            }
        },
        {
            "name": "Unusual Decision",
            "decision": {"status": "approved", "amount": "₹100000", "confidence": 0.95},
            "query_context": {
                "parsed_entities": {
                    "age": "70",
                    "gender": "F",
                    "procedure": "cosmetic surgery",
                    "policy_duration": "1 month"
                }
            }
        },
        {
            "name": "Rejected Case",
            "decision": {"status": "rejected", "amount": "₹0", "confidence": 0.90},
            "query_context": {
                "parsed_entities": {
                    "age": "25",
                    "gender": "M",
                    "procedure": "cosmetic surgery",
                    "policy_duration": "6 months"
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        result = validator.validate_decision_consistency(
            test_case["decision"],
            test_case["query_context"]
        )
        
        print(f"✅ Consistent: {result.get('is_consistent', False)}")
        print(f"🎯 Confidence: {result.get('confidence_score', 0.0):.2f}")
        
        if result.get('warnings'):
            print(f"⚠️ Warnings: {result['warnings']}")
        
        if result.get('anomalies'):
            print(f"❌ Anomalies: {result['anomalies']}")
        
        if result.get('pattern_matches'):
            print(f"✅ Pattern matches: {result['pattern_matches']}")
    
    return True

def test_audit_trail():
    """Test audit trail functionality"""
    print("\n🧪 Testing Audit Trail")
    print("=" * 60)
    
    audit_trail = AuditTrail()
    
    # Test decision logging
    test_decision = {
        "status": "approved",
        "amount": "₹50000",
        "confidence": 0.85
    }
    
    test_query_context = {
        "parsed_entities": {
            "age": "46",
            "gender": "M",
            "procedure": "knee surgery"
        }
    }
    
    test_reasoning_result = {
        "reasoning_chains": {
            "demographic_eligibility": {"status": "approved"},
            "procedure_coverage": {"status": "approved"}
        }
    }
    
    # Log decision
    audit_id = audit_trail.log_decision(
        session_id="test_session",
        user_id="test_user",
        query="46-year-old male, knee surgery",
        decision=test_decision,
        query_context=test_query_context,
        reasoning_result=test_reasoning_result
    )
    
    print(f"✅ Decision logged with audit ID: {audit_id}")
    
    # Log activity
    activity_id = audit_trail.log_activity(
        session_id="test_session",
        user_id="test_user",
        action="document_upload",
        details={"document_count": 3}
    )
    
    print(f"✅ Activity logged with ID: {activity_id}")
    
    # Log error
    error_id = audit_trail.log_error(
        session_id="test_session",
        user_id="test_user",
        error_type="processing_error",
        error_message="Document processing failed",
        context={"document_id": "doc123"}
    )
    
    print(f"✅ Error logged with ID: {error_id}")
    
    # Get audit trail
    trail = audit_trail.get_audit_trail(session_id="test_session")
    print(f"📊 Audit trail entries: {len(trail)}")
    
    # Get session summary
    summary = audit_trail.get_session_summary("test_session")
    print(f"📋 Session summary: {summary}")
    
    # Export audit report
    report = audit_trail.export_audit_report(format="json")
    print(f"📄 Audit report generated: {len(report)} characters")
    
    return True

def test_decision_explainer():
    """Test decision explanation functionality"""
    print("\n🧪 Testing Decision Explainer")
    print("=" * 60)
    
    explainer = DecisionExplainer()
    
    # Test cases
    test_cases = [
        {
            "name": "Approved Decision",
            "decision": {"status": "approved", "amount": "₹50000", "confidence": 0.85},
            "query_context": {
                "parsed_entities": {
                    "age": "46",
                    "gender": "M",
                    "procedure": "knee surgery",
                    "location": "Pune",
                    "policy_duration": "3 months"
                }
            },
            "reasoning_result": {
                "reasoning_chains": {
                    "demographic_eligibility": {
                        "chain_decision": {"status": "approved", "reason": "Age and gender criteria met"}
                    },
                    "procedure_coverage": {
                        "chain_decision": {"status": "approved", "reason": "Procedure covered under policy"}
                    }
                }
            }
        },
        {
            "name": "Rejected Decision",
            "decision": {"status": "rejected", "amount": "₹0", "confidence": 0.90},
            "query_context": {
                "parsed_entities": {
                    "age": "25",
                    "gender": "M",
                    "procedure": "cosmetic surgery",
                    "policy_duration": "6 months"
                }
            },
            "reasoning_result": {
                "reasoning_chains": {
                    "procedure_coverage": {
                        "chain_decision": {"status": "rejected", "reason": "Cosmetic procedures not covered"}
                    }
                }
            }
        },
        {
            "name": "Conditional Decision",
            "decision": {"status": "conditional", "amount": "₹30000", "confidence": 0.75},
            "query_context": {
                "parsed_entities": {
                    "age": "35",
                    "gender": "F",
                    "procedure": "heart surgery",
                    "policy_duration": "1 year"
                }
            },
            "reasoning_result": {
                "reasoning_chains": {
                    "medical_complexity": {
                        "chain_decision": {"status": "conditional", "reason": "Additional documentation required"}
                    }
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        explanation = explainer.generate_explanation(
            test_case["decision"],
            test_case["query_context"],
            test_case["reasoning_result"]
        )
        
        print(f"📝 Explanation length: {len(explanation.get('explanation_text', ''))} characters")
        print(f"🎯 Decision summary: {explanation.get('decision_summary', 'N/A')}")
        print(f"📊 Key factors: {len(explanation.get('key_factors', []))}")
        print(f"📋 Next actions: {len(explanation.get('next_actions', []))}")
        
        # Print a snippet of the explanation
        explanation_text = explanation.get('explanation_text', '')
        if explanation_text:
            print(f"💬 Explanation snippet: {explanation_text[:200]}...")
    
    return True

def test_cache_manager():
    """Test cache management functionality"""
    print("\n🧪 Testing Cache Manager")
    print("=" * 60)
    
    cache_manager = CacheManager()
    
    # Test document embeddings cache
    test_embeddings = [{"vector": [0.1, 0.2, 0.3], "metadata": {"page": 1}}]
    cache_success = cache_manager.cache_document_embeddings("doc123", test_embeddings)
    print(f"✅ Document embeddings cached: {cache_success}")
    
    # Test query processing cache
    test_query_result = {
        "parsed_entities": {"age": "46", "gender": "M"},
        "validation": {"is_valid": True},
        "confidence_score": 0.85
    }
    cache_success = cache_manager.cache_query_processing("test query", test_query_result)
    print(f"✅ Query processing cached: {cache_success}")
    
    # Test decision cache
    test_decision = {"status": "approved", "amount": "₹50000"}
    cache_success = cache_manager.cache_decision_result("query_hash_123", test_decision)
    print(f"✅ Decision cached: {cache_success}")
    
    # Test reasoning cache
    test_reasoning = {
        "reasoning_chains": {"demographic": {"status": "approved"}},
        "confidence_score": 0.85
    }
    cache_success = cache_manager.cache_reasoning_result("query_hash_123", test_reasoning)
    print(f"✅ Reasoning cached: {cache_success}")
    
    # Test cache retrieval
    cached_embeddings = cache_manager.get_cached_document_embeddings("doc123")
    print(f"📥 Cached embeddings retrieved: {cached_embeddings is not None}")
    
    cached_query = cache_manager.get_cached_query_processing("test query")
    print(f"📥 Cached query retrieved: {cached_query is not None}")
    
    cached_decision = cache_manager.get_cached_decision_result("query_hash_123")
    print(f"📥 Cached decision retrieved: {cached_decision is not None}")
    
    cached_reasoning = cache_manager.get_cached_reasoning_result("query_hash_123")
    print(f"📥 Cached reasoning retrieved: {cached_reasoning is not None}")
    
    # Get cache statistics
    stats = cache_manager.get_cache_statistics()
    print(f"📊 Cache statistics: {stats}")
    
    # Test cache invalidation
    invalidated = cache_manager.invalidate_cache("document", "doc123")
    print(f"🗑️ Invalidated cache entries: {invalidated}")
    
    # Clear all caches
    cleared = cache_manager.clear_all_caches()
    print(f"🧹 Cleared cache entries: {cleared}")
    
    return True

def test_security_manager():
    """Test security and compliance functionality"""
    print("\n🧪 Testing Security Manager")
    print("=" * 60)
    
    security_manager = SecurityManager()
    
    # Test data encryption
    sensitive_data = "sensitive_api_key_12345"
    encrypted_data = security_manager.encrypt_sensitive_data(sensitive_data)
    decrypted_data = security_manager.decrypt_sensitive_data(encrypted_data)
    
    print(f"🔐 Data encrypted: {sensitive_data != encrypted_data}")
    print(f"🔓 Data decrypted correctly: {sensitive_data == decrypted_data}")
    
    # Test password hashing
    password = "test_password_123"
    password_hash = security_manager.hash_password(password)
    password_verified = security_manager.verify_password(password, password_hash)
    
    print(f"🔐 Password hashed: {len(password_hash) > 0}")
    print(f"✅ Password verified: {password_verified}")
    
    # Test session management
    session_token = security_manager.create_user_session("test_user", ["read", "query"])
    print(f"🔑 Session created: {session_token is not None}")
    
    session_validation = security_manager.validate_session(session_token)
    print(f"✅ Session validated: {session_validation.get('is_valid', False)}")
    
    # Test permissions
    has_permission = security_manager.check_permission(session_token, "query")
    print(f"🔒 Query permission: {has_permission}")
    
    no_permission = security_manager.check_permission(session_token, "admin")
    print(f"🚫 Admin permission: {no_permission}")
    
    # Test data sanitization
    test_data = {
        "user_id": "user123",
        "password": "secret123",
        "api_key": "key456",
        "normal_data": "public_info"
    }
    sanitized_data = security_manager.sanitize_data_for_export(test_data)
    print(f"🧹 Data sanitized: {sanitized_data}")
    
    # Test GDPR compliance
    security_manager.log_data_access("user123", "query", "process", {"purpose": "insurance_claim"})
    
    gdpr_rights = security_manager.get_data_subject_rights("user123")
    print(f"📋 GDPR rights: {gdpr_rights}")
    
    export_data = security_manager.export_user_data("user123")
    print(f"📤 GDPR export: {len(str(export_data))} characters")
    
    # Test session invalidation
    session_invalidated = security_manager.invalidate_session(session_token)
    print(f"🗑️ Session invalidated: {session_invalidated}")
    
    # Get security statistics
    security_stats = security_manager.get_security_statistics()
    print(f"📊 Security statistics: {security_stats}")
    
    return True

def test_api_endpoints():
    """Test API endpoints functionality"""
    print("\n🧪 Testing API Endpoints")
    print("=" * 60)
    
    # Create mock components
    mock_qa_chain = create_mock_qa_chain()
    cache_manager = CacheManager()
    security_manager = SecurityManager()
    
    # Initialize API endpoints
    api_endpoints = APIEndpoints(mock_qa_chain, cache_manager, security_manager)
    
    print("✅ API Endpoints initialized")
    
    # Test API configuration
    print(f"📋 API Version: {api_endpoints.api_config['version']}")
    print(f"🔒 Rate limiting: {api_endpoints.api_config['rate_limit_enabled']}")
    print(f"🔗 Webhooks enabled: {api_endpoints.api_config['webhook_enabled']}")
    print(f"📦 Batch processing: {api_endpoints.api_config['batch_processing_enabled']}")
    
    # Test rate limiting
    rate_limit_works = api_endpoints._check_rate_limit(type('Request', (), {'remote_addr': '127.0.0.1'})())
    print(f"⏱️ Rate limiting: {rate_limit_works}")
    
    # Test webhook signature generation
    test_payload = {"event": "test", "data": "test_data"}
    test_secret = "test_secret"
    signature = api_endpoints._generate_webhook_signature(test_payload, test_secret)
    print(f"🔐 Webhook signature generated: {len(signature) > 0}")
    
    # Test webhook triggering
    api_endpoints._trigger_webhooks("test_event", {"test": "data"})
    print("🔗 Webhooks triggered (no endpoints registered)")
    
    return True

def test_integration():
    """Test integration between all components"""
    print("\n🧪 Testing Integration")
    print("=" * 60)
    
    # Initialize all components
    consistency_validator = ConsistencyValidator()
    audit_trail = AuditTrail()
    decision_explainer = DecisionExplainer()
    cache_manager = CacheManager()
    security_manager = SecurityManager()
    
    # Test integrated workflow
    test_query = "46-year-old male, knee surgery in Pune, 3-month policy"
    test_decision = {"status": "approved", "amount": "₹50000", "confidence": 0.85}
    test_context = {
        "parsed_entities": {
            "age": "46",
            "gender": "M",
            "procedure": "knee surgery",
            "location": "Pune",
            "policy_duration": "3 months"
        }
    }
    test_reasoning = {
        "reasoning_chains": {
            "demographic_eligibility": {"status": "approved"},
            "procedure_coverage": {"status": "approved"}
        }
    }
    
    # Step 1: Consistency validation
    consistency_result = consistency_validator.validate_decision_consistency(
        test_decision, test_context
    )
    print(f"✅ Consistency validation: {consistency_result.get('is_consistent', False)}")
    
    # Step 2: Decision explanation
    explanation = decision_explainer.generate_explanation(
        test_decision, test_context, test_reasoning, consistency_result
    )
    print(f"✅ Decision explanation generated: {len(explanation.get('explanation_text', ''))} chars")
    
    # Step 3: Audit logging
    audit_id = audit_trail.log_decision(
        "test_session", "test_user", test_query,
        test_decision, test_context, test_reasoning, consistency_result
    )
    print(f"✅ Decision logged: {audit_id}")
    
    # Step 4: Security logging
    security_manager.log_data_access("test_user", "query", "process", {
        "query": test_query,
        "decision": test_decision["status"]
    })
    print("✅ Security logging completed")
    
    # Step 5: Cache management
    cache_manager.cache_decision_result("test_hash", test_decision)
    cache_manager.cache_reasoning_result("test_hash", test_reasoning)
    print("✅ Caching completed")
    
    # Step 6: Data export (sanitized)
    sanitized_decision = security_manager.sanitize_data_for_export(test_decision)
    print(f"✅ Data sanitized: {sanitized_decision}")
    
    print("🎉 All integration tests completed successfully!")
    return True

def main():
    """Run all comprehensive tests"""
    print("🚀 Comprehensive Feature Testing")
    print("=" * 80)
    
    try:
        # Test all components
        test_consistency_validation()
        test_audit_trail()
        test_decision_explainer()
        test_cache_manager()
        test_security_manager()
        test_api_endpoints()
        test_integration()
        
        print("\n" + "=" * 80)
        print("🎉 All comprehensive tests completed successfully!")
        print("\n✅ Features Implemented:")
        print("  • Consistency Validation")
        print("  • Audit Trail System")
        print("  • Decision Explanation Templates")
        print("  • Caching System")
        print("  • Security & Compliance")
        print("  • API Endpoints & Integration")
        print("  • Webhook Support")
        print("  • GDPR Compliance")
        print("  • Rate Limiting")
        print("  • Session Management")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 