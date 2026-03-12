#!/usr/bin/env python3
"""
Demo script to show hackathon-optimized responses
Demonstrates precise clause mapping and structured decisions
"""

from src.core.hackathon_optimizer import HackathonOptimizer

def demo_hackathon_responses():
    """Demo the improved hackathon responses"""
    
    optimizer = HackathonOptimizer()
    
    # Sample insurance policy documents
    documents = [
        "Dental surgery does not cover surgical treatment that relates to dental implants. All investigative procedures that establish the need for dental surgery such as laboratory tests, X-rays, CT scans, and MRI(s) are included under this benefit. Root canal treatment is covered under basic dental coverage. Teeth whitening is considered cosmetic and not covered.",
        "There is a 30-day waiting period for all claims except those arising out of Accidental Injury. All surgical procedures are covered up to ₹2,00,000. Pre-authorization is required for surgeries above ₹50,000. Network hospitals provide 100% coverage while non-network hospitals provide 80% coverage.",
        "Policies less than 6 months old have limited coverage. Full coverage applies after 6 months of policy duration. Emergency coverage is available from day 1. Adults aged 18-65 have standard coverage, senior citizens (65+) have 90% coverage, and children under 18 have 100% coverage."
    ]
    
    # Test queries from the problem statement
    test_queries = [
        "Will the plan cover root canal and some teeth whitening if I just got the policy?",
        "46-year-old male, knee surgery in Pune, 3-month-old insurance policy",
        "Root canal treatment for 25-year-old with 6-month policy",
        "Teeth whitening for 30-year-old female with 1-year policy",
        "Emergency heart surgery for 50-year-old male with 2-month policy"
    ]
    
    print("🚀 HACKATHON OPTIMIZED RESPONSES")
    print("=" * 80)
    print("Problem Statement: LLM Document Processing System")
    print("Objective: Parse queries, find relevant clauses, make decisions, return structured JSON")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 QUERY {i}: {query}")
        print("-" * 60)
        
        # Process query
        response = optimizer.process_query(query, documents)
        
        # Display results
        print(f"✅ DECISION: {response['decision']['status'].upper()}")
        print(f"💰 AMOUNT: {response['decision']['amount']}")
        print(f"🎯 CONFIDENCE: {response['decision']['confidence']:.2f}")
        print(f"📝 JUSTIFICATION: {response['justification']}")
        
        # Show clause mapping
        print(f"🔗 PRIMARY CLAUSE: {response['clause_mapping']['primary_clause']}")
        
        if response['clause_mapping']['supporting_clauses']:
            print(f"📋 SUPPORTING CLAUSES:")
            for clause in response['clause_mapping']['supporting_clauses']:
                print(f"   • {clause}")
        
        # Show parsed entities
        parsed = response.get('parsed_entities', {})
        print(f"🔍 PARSED ENTITIES:")
        for key, value in parsed.items():
            if value is not None:
                print(f"   • {key}: {value}")
        
        # Show evidence clauses
        if response['evidence_clauses']:
            print(f"📄 EVIDENCE CLAUSES ({len(response['evidence_clauses'])} found):")
            for clause in response['evidence_clauses'][:2]:  # Show first 2
                print(f"   • {clause['text'][:100]}...")
        
        print("-" * 60)
    
    print("\n🎯 HACKATHON BENEFITS:")
    print("✅ Precise clause mapping instead of generic responses")
    print("✅ Structured JSON output with decision, amount, justification")
    print("✅ Exact clause references for audit trail")
    print("✅ Confidence scoring for decision reliability")
    print("✅ Parsed entities for better understanding")
    print("✅ Evidence-based reasoning with specific clauses")

def demo_structured_json():
    """Demo the structured JSON output format"""
    
    optimizer = HackathonOptimizer()
    
    # Sample query and documents
    query = "46-year-old male, knee surgery in Pune, 3-month-old insurance policy"
    documents = [
        "All surgical procedures are covered up to ₹2,00,000. There is a 30-day waiting period for all claims except those arising out of Accidental Injury. Network hospitals provide 100% coverage."
    ]
    
    response = optimizer.process_query(query, documents)
    
    print("\n📊 STRUCTURED JSON OUTPUT:")
    print("=" * 60)
    print(json.dumps(response, indent=2))
    
    print("\n🎯 JSON STRUCTURE ANALYSIS:")
    print("✅ query: Original user query")
    print("✅ parsed_entities: Extracted age, gender, procedure, location, policy_duration")
    print("✅ decision: status (approved/rejected/conditional), amount, confidence")
    print("✅ justification: Human-readable explanation")
    print("✅ evidence_clauses: Specific clauses from documents")
    print("✅ clause_mapping: Primary clause, supporting clauses, decision factors")
    print("✅ metadata: Processing timestamp, complexity, confidence level")

if __name__ == "__main__":
    import json
    
    print("🎯 HACKATHON DOCUMENT PROCESSING SYSTEM DEMO")
    print("=" * 80)
    
    # Demo 1: Show improved responses
    demo_hackathon_responses()
    
    # Demo 2: Show structured JSON
    demo_structured_json()
    
    print("\n🎉 DEMO COMPLETE!")
    print("The system now provides precise, structured responses with exact clause mapping!") 