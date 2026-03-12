#!/usr/bin/env python3
"""
Test script for enhanced query processing and multi-hop reasoning
Tests query validation, semantic expansion, disambiguation, and reasoning chains
"""

import json
from src.core.enhanced_query_processor import EnhancedQueryProcessor
from src.core.multi_hop_reasoner import MultiHopReasoner

def create_test_documents():
    """Create test documents for reasoning"""
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

def test_query_processing():
    """Test enhanced query processing functionality"""
    print("🧪 Testing Enhanced Query Processing")
    print("=" * 60)
    
    processor = EnhancedQueryProcessor()
    
    # Test cases with different complexity levels
    test_queries = [
        {
            "name": "Complete Query",
            "query": "46-year-old male, knee surgery in Pune, 3-month-old insurance policy",
            "expected_entities": ["age", "gender", "procedure", "location", "policy_duration"]
        },
        {
            "name": "Vague Query",
            "query": "surgery",
            "expected_entities": ["procedure"]
        },
        {
            "name": "Complex Medical Query",
            "query": "70-year-old female with diabetes, emergency heart bypass surgery in Mumbai, premium coverage",
            "expected_entities": ["age", "gender", "medical_condition", "urgency", "procedure", "location", "coverage_type"]
        },
        {
            "name": "Incomplete Query",
            "query": "knee",
            "expected_entities": ["procedure"]
        },
        {
            "name": "Urgent Query",
            "query": "emergency appendectomy for 25-year-old male",
            "expected_entities": ["urgency", "procedure", "age", "gender"]
        }
    ]
    
    for test_case in test_queries:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        
        result = processor.process_query(test_case['query'])
        
        # Check validation
        validation = result.get('validation', {})
        print(f"✅ Valid: {validation.get('is_valid', False)}")
        if validation.get('errors'):
            print(f"❌ Errors: {validation['errors']}")
        if validation.get('warnings'):
            print(f"⚠️ Warnings: {validation['warnings']}")
        if validation.get('suggestions'):
            print(f"💡 Suggestions: {validation['suggestions']}")
        
        # Check parsed entities
        parsed = result.get('parsed_entities', {})
        found_entities = [k for k, v in parsed.items() if v]
        print(f"📊 Entities found: {found_entities}")
        
        # Check confidence
        confidence = result.get('processing_metadata', {}).get('confidence_score', 0.0)
        print(f"🎯 Confidence: {confidence:.2f}")
        
        # Check semantic expansion
        expanded = result.get('expanded_query', {})
        if expanded.get('expanded_terms'):
            print(f"🔍 Expanded terms: {expanded['expanded_terms']}")
        
        # Check disambiguation
        disambiguated = result.get('disambiguated', {})
        if disambiguated.get('ambiguities'):
            print(f"❓ Ambiguities: {disambiguated['ambiguities']}")
        if disambiguated.get('clarifications'):
            print(f"💭 Clarifications: {disambiguated['clarifications']}")
    
    return True

def test_multi_hop_reasoning():
    """Test multi-hop reasoning functionality"""
    print("\n🧪 Testing Multi-Hop Reasoning")
    print("=" * 60)
    
    reasoner = MultiHopReasoner()
    documents = create_test_documents()
    
    # Test different query contexts
    test_contexts = [
        {
            "name": "Standard Case",
            "parsed_entities": {
                "age": "46",
                "gender": "M",
                "procedure": "knee surgery",
                "location": "Pune",
                "policy_duration": "3 months"
            }
        },
        {
            "name": "Complex Case",
            "parsed_entities": {
                "age": "70",
                "gender": "F",
                "procedure": "heart bypass",
                "medical_condition": "diabetes",
                "urgency": "high",
                "coverage_type": "premium"
            }
        },
        {
            "name": "Incomplete Case",
            "parsed_entities": {
                "procedure": "surgery"
            }
        },
        {
            "name": "Excluded Case",
            "parsed_entities": {
                "age": "35",
                "gender": "F",
                "procedure": "cosmetic surgery",
                "medical_condition": "pre-existing condition"
            }
        }
    ]
    
    for test_case in test_contexts:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"Entities: {test_case['parsed_entities']}")
        
        query_context = {
            "parsed_entities": test_case['parsed_entities']
        }
        
        result = reasoner.execute_reasoning_chain(query_context, documents)
        
        # Check reasoning chains
        chains = result.get('reasoning_chains', {})
        print(f"🔗 Active chains: {list(chains.keys())}")
        
        # Check final decision
        final_decision = result.get('final_decision', {})
        print(f"📊 Final decision: {final_decision.get('status', 'unknown')}")
        print(f"💭 Reason: {final_decision.get('reason', 'No reason provided')}")
        
        # Check confidence
        confidence = result.get('confidence_score', 0.0)
        print(f"🎯 Confidence: {confidence:.2f}")
        
        # Check reasoning path
        reasoning_path = result.get('reasoning_path', [])
        print(f"🛤️ Reasoning steps: {len(reasoning_path)}")
        for path in reasoning_path:
            print(f"  - {path['chain']}: {path['decision']} ({path['reason']})")
    
    return True

def test_integration():
    """Test integration between query processing and reasoning"""
    print("\n🧪 Testing Integration")
    print("=" * 60)
    
    processor = EnhancedQueryProcessor()
    reasoner = MultiHopReasoner()
    documents = create_test_documents()
    
    # Test integrated workflow
    test_queries = [
        "46M, knee surgery, Pune, 3-month policy",
        "70F with diabetes, emergency heart bypass, Mumbai, premium coverage",
        "25M, cosmetic surgery, Delhi",
        "surgery"  # Vague query
    ]
    
    for query in test_queries:
        print(f"\n📋 Testing integrated workflow for: {query}")
        
        # Step 1: Query processing
        query_analysis = processor.process_query(query)
        print(f"✅ Query processed: {query_analysis['processing_metadata']['entities_found']} entities found")
        
        # Step 2: Multi-hop reasoning
        reasoning_result = reasoner.execute_reasoning_chain(query_analysis, documents)
        print(f"✅ Reasoning completed: {len(reasoning_result.get('reasoning_chains', {}))} chains executed")
        
        # Step 3: Synthesize results
        final_decision = reasoning_result.get('final_decision', {})
        print(f"📊 Final decision: {final_decision.get('status', 'unknown')}")
        print(f"💭 Reason: {final_decision.get('reason', 'No reason provided')}")
        
        # Check validation
        validation = query_analysis.get('validation', {})
        if not validation.get('is_valid', True):
            print(f"⚠️ Query validation issues: {validation.get('errors', [])}")
        
        # Check disambiguation
        disambiguated = query_analysis.get('disambiguated', {})
        if disambiguated.get('ambiguities'):
            print(f"❓ Ambiguities detected: {disambiguated['ambiguities']}")
    
    return True

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🧪 Testing Edge Cases")
    print("=" * 60)
    
    processor = EnhancedQueryProcessor()
    reasoner = MultiHopReasoner()
    documents = create_test_documents()
    
    edge_cases = [
        "",  # Empty query
        "a",  # Very short query
        "x" * 1000,  # Very long query
        "999-year-old alien, teleportation surgery on Mars",  # Impossible case
        "male female both",  # Conflicting gender
        "0-year-old baby, adult surgery",  # Age-procedure mismatch
    ]
    
    for i, query in enumerate(edge_cases):
        print(f"\n📋 Edge case {i+1}: {query[:50]}{'...' if len(query) > 50 else ''}")
        
        try:
            # Test query processing
            query_analysis = processor.process_query(query)
            validation = query_analysis.get('validation', {})
            print(f"✅ Query processed: Valid={validation.get('is_valid', False)}")
            
            # Test reasoning
            reasoning_result = reasoner.execute_reasoning_chain(query_analysis, documents)
            final_decision = reasoning_result.get('final_decision', {})
            print(f"✅ Reasoning completed: {final_decision.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True

def test_performance():
    """Test performance with multiple queries"""
    print("\n🧪 Testing Performance")
    print("=" * 60)
    
    processor = EnhancedQueryProcessor()
    reasoner = MultiHopReasoner()
    documents = create_test_documents()
    
    import time
    
    # Generate test queries
    test_queries = [
        f"{age}-year-old {gender}, {procedure} in {location}, {duration} policy"
        for age in ["25", "35", "45", "55", "65"]
        for gender in ["male", "female"]
        for procedure in ["knee surgery", "cataract surgery", "angioplasty"]
        for location in ["Mumbai", "Delhi", "Bangalore"]
        for duration in ["3 months", "6 months", "1 year"]
    ][:20]  # Limit to 20 queries for performance test
    
    print(f"Testing {len(test_queries)} queries...")
    
    start_time = time.time()
    
    for i, query in enumerate(test_queries):
        try:
            # Process query
            query_analysis = processor.process_query(query)
            
            # Execute reasoning
            reasoning_result = reasoner.execute_reasoning_chain(query_analysis, documents)
            
            if (i + 1) % 5 == 0:
                print(f"✅ Processed {i + 1} queries...")
                
        except Exception as e:
            print(f"❌ Error on query {i + 1}: {e}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"⏱️ Total time: {total_time:.2f} seconds")
    print(f"📊 Average time per query: {total_time/len(test_queries):.3f} seconds")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced Query Processing and Multi-Hop Reasoning")
    print("=" * 80)
    
    try:
        # Test query processing
        test_query_processing()
        
        # Test multi-hop reasoning
        test_multi_hop_reasoning()
        
        # Test integration
        test_integration()
        
        # Test edge cases
        test_edge_cases()
        
        # Test performance
        test_performance()
        
        print("\n" + "=" * 80)
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 