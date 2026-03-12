#!/usr/bin/env python3
"""
Test script for structured JSON response functionality
Tests clause extraction, evidence mapping, and structured output
"""

import json
from src.core.clause_extractor import ClauseExtractor, EvidenceMapper

def create_test_documents():
    """Create test documents with clauses"""
    documents = [
        {
            "page_content": "Section 3.2: Knee surgery is covered under the policy for patients aged 18-65. The maximum coverage amount is ₹50,000 for this procedure.",
            "metadata": {"source": "policy_document.pdf", "page": 5}
        },
        {
            "page_content": "Section 4.1: Pre-existing conditions are not covered under this policy. Any treatment related to pre-existing conditions will be excluded from coverage.",
            "metadata": {"source": "policy_document.pdf", "page": 8}
        },
        {
            "page_content": "Section 2.3: Policy duration must be at least 3 months for coverage to be effective. Claims submitted before the 3-month waiting period will be rejected.",
            "metadata": {"source": "policy_document.pdf", "page": 3}
        },
        {
            "page_content": "Section 5.1: All surgical procedures require pre-authorization from the insurance provider. Failure to obtain pre-authorization may result in claim rejection.",
            "metadata": {"source": "policy_document.pdf", "page": 12}
        }
    ]
    return documents

def test_clause_extraction():
    """Test clause extraction functionality"""
    print("🧪 Testing Clause Extraction")
    print("=" * 50)
    
    extractor = ClauseExtractor()
    documents = create_test_documents()
    
    clauses = extractor.extract_clauses(documents)
    
    print(f"✅ Extracted {len(clauses)} clauses")
    
    for i, clause in enumerate(clauses):
        print(f"\n📋 Clause {i+1}:")
        print(f"  ID: {clause['clause_id']}")
        print(f"  Type: {clause['clause_type']}")
        print(f"  Impact: {clause['decision_impact']}")
        print(f"  Relevance: {clause['relevance_score']:.2f}")
        print(f"  Summary: {clause.get('summary', 'N/A')[:100]}...")
    
    return clauses

def test_evidence_mapping():
    """Test evidence mapping functionality"""
    print("\n🧪 Testing Evidence Mapping")
    print("=" * 50)
    
    mapper = EvidenceMapper()
    documents = create_test_documents()
    
    # Test with an approval scenario
    test_question = "46-year-old male, knee surgery in Pune, 3-month-old insurance policy"
    test_answer = "Based on the policy documents, knee surgery is covered for patients aged 18-65. The claim is approved with a coverage amount of ₹50,000."
    test_decision = "Approved"
    test_amount = "₹50000"
    
    structured_response = mapper.create_structured_response(
        question=test_question,
        answer=test_answer,
        documents=documents,
        decision=test_decision,
        amount=test_amount
    )
    
    print("✅ Created structured response")
    print(f"📊 Decision: {structured_response['decision']['status']}")
    print(f"💰 Amount: {structured_response['decision']['amount']}")
    print(f"🎯 Confidence: {structured_response['decision']['confidence']:.2f}")
    print(f"📋 Total Clauses: {structured_response['evidence']['total_clauses']}")
    print(f"✅ Supporting Clauses: {structured_response['evidence']['supporting_clauses']}")
    print(f"❌ Opposing Clauses: {structured_response['evidence']['opposing_clauses']}")
    
    return structured_response

def test_json_output():
    """Test JSON output formatting"""
    print("\n🧪 Testing JSON Output")
    print("=" * 50)
    
    structured_response = test_evidence_mapping()
    
    # Format JSON output
    json_output = json.dumps(structured_response, indent=2)
    
    print("✅ Generated JSON output:")
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
    
    return json_output

def test_clause_mapping():
    """Test clause-to-decision mapping"""
    print("\n🧪 Testing Clause-to-Decision Mapping")
    print("=" * 50)
    
    mapper = EvidenceMapper()
    documents = create_test_documents()
    
    # Test different scenarios
    scenarios = [
        {
            "name": "Approval Scenario",
            "question": "46M, knee surgery, Pune, 3-month policy",
            "answer": "Knee surgery is covered and approved.",
            "decision": "Approved",
            "amount": "₹50000"
        },
        {
            "name": "Rejection Scenario", 
            "question": "70M, pre-existing condition, heart surgery",
            "answer": "Pre-existing conditions are not covered.",
            "decision": "Rejected",
            "amount": "N/A"
        },
        {
            "name": "Unclear Scenario",
            "question": "25M, cosmetic surgery, Mumbai",
            "answer": "Cosmetic procedures require pre-authorization.",
            "decision": "Unclear",
            "amount": "N/A"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        
        response = mapper.create_structured_response(
            question=scenario['question'],
            answer=scenario['answer'],
            documents=documents,
            decision=scenario['decision'],
            amount=scenario['amount']
        )
        
        print(f"  Decision: {response['decision']['status']}")
        print(f"  Confidence: {response['decision']['confidence']:.2f}")
        print(f"  Supporting: {response['evidence']['supporting_clauses']}")
        print(f"  Opposing: {response['evidence']['opposing_clauses']}")

def main():
    """Run all tests"""
    print("🚀 Testing Structured JSON Response System")
    print("=" * 60)
    
    try:
        # Test clause extraction
        test_clause_extraction()
        
        # Test evidence mapping
        test_evidence_mapping()
        
        # Test JSON output
        test_json_output()
        
        # Test clause mapping scenarios
        test_clause_mapping()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 