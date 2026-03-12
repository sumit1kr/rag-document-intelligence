import os, re
import logging
import traceback
import json
from typing import Dict, Any, List
from src.utils.conv_mem import ConversationMemory
from src.api.setup_api import logger
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from .clause_extractor import EvidenceMapper
from .enhanced_query_processor import EnhancedQueryProcessor
from .multi_hop_reasoner import MultiHopReasoner
from .consistency_validator import ConsistencyValidator
from src.utils.audit_trail import AuditTrail
from .decision_explainer import DecisionExplainer
from .optimizer import HackathonOptimizer

# -----------------------------
# Enhanced QA Chain with Hackathon Optimization
# -----------------------------
class QAChain:
    """Handles question answering with retrieval, memory, and comprehensive analysis"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.memory = ConversationMemory()
        self.evidence_mapper = EvidenceMapper()
        self.query_processor = EnhancedQueryProcessor()
        self.reasoner = MultiHopReasoner()
        self.consistency_validator = ConsistencyValidator()
        self.audit_trail = AuditTrail()
        self.decision_explainer = DecisionExplainer()
        self.hackathon_optimizer = HackathonOptimizer()  # Add hackathon optimizer
        
        self.llm = ChatGroq(
            api_key=config['GROQ_API_KEY'],
            model_name=config['LLM_MODEL'],
            max_tokens=4000,
            temperature=0.1
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Use only the information from the context to answer questions. "
                "If you cannot find the answer in the context, reply with 'I don't know based on the provided documents.' "
                "Mention your decision clearly if applicable and also the amount to be given if at all it's there."
                "Be concise but comprehensive in your answers.\n\n"
                "Context: {context}"
            )),
            ("human", "{question}")
        ])
        
        logger.info("Enhanced QA Chain with hackathon optimization initialized")
    
    def _extract_decision(self, answer: str) -> str:
        ans = answer.lower()

        # Normalize spaces, remove special characters for better matching
        ans_clean = re.sub(r'[^a-zA-Z\s]', '', ans)

        negative_keywords = [
            "not covered", "not eligible", "rejected", "excluded",
            "declined", "denied", "not payable", "not admissible",
            "claim denied", "claim rejected", "cannot be claimed",
            "no coverage", "not claimable"
        ]

        positive_keywords = [
            "covered", "eligible", "approved", "included",
            "admissible", "payable", "reimbursable", "can be claimed",
            "claim allowed", "claim approved", "claim accepted"
        ]

        unclear_keywords = [
            "depends", "cannot determine", "unclear", "subject to",
            "may be", "might be", "need more", "check with",
            "conditional", "unsure", "ambiguous", "context not clear",
            "insufficient info", "needs clarification"
        ]

        for kw in negative_keywords:
            if kw in ans_clean:
                return "Rejected"

        for kw in positive_keywords:
            if kw in ans_clean:
                return "Approved"

        for kw in unclear_keywords:
            if kw in ans_clean:
                return "Unclear"

        return "Unknown"

    def _extract_amount(self, answer: str) -> str:
        # Match ₹, Rs., or $ followed by numbers (with optional spaces and commas)
        matches = re.findall(r'(₹|Rs\.?|INR|\$)\s?:?\s?\d[\d,]*', answer)

        if not matches:
            return "N/A"

        # Clean up and extract numeric part
        for raw in matches:
            # Remove symbols and punctuation
            num_match = re.search(r'\d[\d,]*', raw)
            if num_match:
                amount = num_match.group(0).replace(",", "")
                if amount.isdigit():
                    return f"₹{amount}"

        return "N/A"
 
    def run(self, question: str, retriever, session_id: str, user_id: str = "default_user") -> Dict[str, Any]:
        """Process question and return structured response with comprehensive analysis"""
        if not question or not question.strip():
            return {
                'answer': "Please enter a valid question.",
                'history': self.memory.get_history(session_id),
                'structured_response': None
            }
        
        try:
            # Log activity start
            self.audit_trail.log_activity(session_id, user_id, "query_started", {"question": question})
            
            # Add human message to memory
            self.memory.add_message(session_id, 'human', question)
            
            # Step 1: Enhanced Query Processing
            query_analysis = self.query_processor.process_query(question)
            logger.info(f"Query analysis completed: {query_analysis['processing_metadata']['entities_found']} entities found")
            
            # Step 2: Retrieve relevant documents
            docs = []
            try:
                # Use expanded query terms for better retrieval
                expanded_terms = query_analysis.get('expanded_query', {}).get('expanded_terms', [])
                if expanded_terms:
                    # Create enhanced query with expanded terms
                    enhanced_query = f"{question} {' '.join(expanded_terms)}"
                    docs = retriever.get_relevant_documents(enhanced_query)
                else:
                    docs = retriever.get_relevant_documents(question)
                
                logger.info(f"Retrieved {len(docs)} documents for question")
            except Exception as e:
                logger.error(f"Document retrieval failed: {e}")
                self.audit_trail.log_error(session_id, user_id, "retrieval_error", str(e), {"question": question})
            
            # Step 3: Multi-hop reasoning
            reasoning_result = self.reasoner.execute_reasoning_chain(query_analysis, docs)
            logger.info(f"Multi-hop reasoning completed: {len(reasoning_result.get('reasoning_chains', {}))} chains executed")
            
            # Step 4: Use Hackathon Optimizer for precise responses
            # document_texts = [doc.page_content for doc in docs] if docs else []
            # hackathon_response = self.hackathon_optimizer.process_query(question, document_texts)
            hackathon_response = {"decision": {"status": "unclear", "confidence": 0.0}}

            # Step 5: Generate LLM answer with enhanced context (fallback)
            context = self._prepare_enhanced_context(docs, query_analysis, reasoning_result)
            
            try:
                formatted_prompt = self.prompt.format_prompt(
                    context=context, 
                    question=question
                )
                
                response = self.llm.invoke(formatted_prompt.to_messages())
                llm_answer = response.content

            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                self.audit_trail.log_error(session_id, user_id, "llm_error", str(e), {"question": question})
                llm_answer = "I apologize, but I encountered an error while generating the answer. Please try again."
            
            # Step 6: Use hackathon response if available, otherwise fallback to LLM
            if hackathon_response.get('decision', {}).get('status') != 'unclear':
                # Use hackathon optimizer response
                answer = hackathon_response.get('justification', llm_answer)
                decision = hackathon_response.get('decision', {}).get('status', 'unclear')
                amount = hackathon_response.get('decision', {}).get('amount', 'N/A')
                confidence = hackathon_response.get('decision', {}).get('confidence', 0.0)
            else:
                # Fallback to LLM processing
                answer = llm_answer
                decision = self._extract_decision(answer)
                amount = self._extract_amount(answer)
                confidence = 0.7  # Default confidence for LLM responses
            
            # Add AI response to memory
            self.memory.add_message(session_id, 'assistant', answer)
            
            # Step 7: Create structured response with enhanced information
            if hackathon_response.get('decision', {}).get('status') != 'unclear':
                # Use hackathon structured response
                structured_response = {
                    "question": question,
                    "answer": answer,
                    "decision": {
                        "status": decision,
                        "amount": amount,
                        "confidence": confidence
                    },
                    "evidence_clauses": hackathon_response.get('evidence_clauses', []),
                    "clause_mapping": hackathon_response.get('clause_mapping', {}),
                    "parsed_entities": hackathon_response.get('parsed_entities', {}),
                    "metadata": hackathon_response.get('metadata', {})
                }
            else:
                # Create structured response with enhanced information
                structured_response = self.evidence_mapper.create_structured_response(
                    question=question,
                    answer=answer,
                    documents=docs,
                    decision=decision,
                    amount=amount
                )
            
            # Step 8: Consistency validation
            consistency_validation = self.consistency_validator.validate_decision_consistency(
                structured_response.get('decision', {}),
                query_analysis,
                historical_cases=None  # Could be loaded from database
            )
            
            # Step 9: Generate decision explanation
            decision_explanation = self.decision_explainer.generate_explanation(
                structured_response.get('decision', {}),
                query_analysis,
                reasoning_result,
                consistency_validation
            )
            
            # Step 10: Enhance structured response with all analysis
            enhanced_response = self._enhance_structured_response(
                structured_response, query_analysis, reasoning_result, 
                consistency_validation, decision_explanation
            )
            
            # Add retrieved documents to the response for debugging
            enhanced_response['retrieved_documents'] = [
                {
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'metadata': doc.metadata,
                    'source': doc.metadata.get('source', 'Unknown')
                } for doc in docs
            ]
            
            # Step 11: Log decision to audit trail
            audit_id = self.audit_trail.log_decision(
                session_id=session_id,
                user_id=user_id,
                query=question,
                decision=structured_response.get('decision', {}),
                query_context=query_analysis,
                reasoning_result=reasoning_result,
                consistency_validation=consistency_validation
            )
            
            # Step 12: Log activity completion
            self.audit_trail.log_activity(session_id, user_id, "query_completed", {
                "audit_id": audit_id,
                "decision": decision,
                "amount": amount,
                "confidence": enhanced_response.get('decision', {}).get('confidence', 0.0)
            })
            
            # Create backward-compatible response for existing interface
            legacy_response = {
                "decision": decision,
                "amount": amount,
                "justification": answer.strip(),
                "evidence_clauses": enhanced_response.get('evidence_clauses', []),
                "query_details": {
                    "interpreted_from": question,
                    "enhanced_analysis": query_analysis
                },
                "answer": answer,
                "history": self.memory.get_history(session_id)
            }
            
            # Combine both responses
            combined_response = {
                **legacy_response,
                "structured_response": enhanced_response,
                "json_output": json.dumps(enhanced_response, indent=2),
                "query_analysis": query_analysis,
                "reasoning_result": reasoning_result,
                "consistency_validation": consistency_validation,
                "decision_explanation": decision_explanation,
                "audit_id": audit_id,
                "hackathon_optimized": hackathon_response.get('decision', {}).get('status') != 'unclear'
            }
            
            return combined_response

            
        except Exception as e:
            logger.error(f"QA chain execution failed: {e}")
            self.audit_trail.log_error(session_id, user_id, "qa_chain_error", str(e), {"question": question})
            return {
                'answer': "An error occurred while processing your question. Please try again.",
                'history': self.memory.get_history(session_id),
                'structured_response': None
            }
    
    def _prepare_enhanced_context(self, 
                                 docs: List[Any], 
                                 query_analysis: Dict[str, Any], 
                                 reasoning_result: Dict[str, Any]) -> str:
        """Prepare enhanced context with query analysis and reasoning information"""
        # Basic document context
        doc_context = "\n---\n".join([doc.page_content for doc in docs])
        
        # Add query analysis context
        parsed = query_analysis.get('parsed_entities', {})
        query_context = f"""
Query Analysis:
- Age: {parsed.get('age', 'Not specified')}
- Gender: {parsed.get('gender', 'Not specified')}
- Procedure: {parsed.get('procedure', 'Not specified')}
- Location: {parsed.get('location', 'Not specified')}
- Policy Duration: {parsed.get('policy_duration', 'Not specified')}
- Medical Condition: {parsed.get('medical_condition', 'Not specified')}
- Urgency: {parsed.get('urgency', 'Normal')}
- Coverage Type: {parsed.get('coverage_type', 'Standard')}

Validation: {query_analysis.get('validation', {}).get('is_valid', False)}
Confidence: {query_analysis.get('processing_metadata', {}).get('confidence_score', 0.0):.2f}
"""
        
        # Add reasoning context
        reasoning_context = ""
        if reasoning_result.get('reasoning_chains'):
            reasoning_context = "\nReasoning Analysis:\n"
            for chain_name, chain_result in reasoning_result['reasoning_chains'].items():
                decision = chain_result.get('chain_decision', {})
                reasoning_context += f"- {chain_name}: {decision.get('status', 'unknown')} - {decision.get('reason', 'No reason provided')}\n"
        
        # Combine all context
        enhanced_context = f"{query_context}\n{reasoning_context}\n\nDocument Context:\n{doc_context}"
        
        return enhanced_context
    
    def _enhance_structured_response(self, 
                                   structured_response: Dict[str, Any], 
                                   query_analysis: Dict[str, Any], 
                                   reasoning_result: Dict[str, Any],
                                   consistency_validation: Dict[str, Any],
                                   decision_explanation: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance structured response with all analysis information"""
        enhanced = structured_response.copy()
        
        # Add query analysis
        enhanced['query_analysis'] = {
            'parsed_entities': query_analysis.get('parsed_entities', {}),
            'validation': query_analysis.get('validation', {}),
            'expanded_query': query_analysis.get('expanded_query', {}),
            'disambiguated': query_analysis.get('disambiguated', {}),
            'processing_metadata': query_analysis.get('processing_metadata', {})
        }
        
        # Add reasoning information
        enhanced['reasoning'] = {
            'final_decision': reasoning_result.get('final_decision', {}),
            'confidence_score': reasoning_result.get('confidence_score', 0.0),
            'reasoning_path': reasoning_result.get('reasoning_path', []),
            'active_chains': list(reasoning_result.get('reasoning_chains', {}).keys())
        }
        
        # Add consistency validation
        enhanced['consistency_validation'] = consistency_validation
        
        # Add decision explanation
        enhanced['decision_explanation'] = decision_explanation
        
        # Enhance decision with reasoning
        if reasoning_result.get('final_decision'):
            final_decision = reasoning_result['final_decision']
            enhanced['decision']['status'] = final_decision.get('status', enhanced['decision']['status'])
            enhanced['decision']['reasoning'] = final_decision.get('reason', 'No reasoning provided')
            enhanced['decision']['supporting_chains'] = final_decision.get('supporting_chains', [])
            enhanced['decision']['opposing_chains'] = final_decision.get('opposing_chains', [])
        
        return enhanced
    
    def get_audit_trail(self, session_id: str = None, user_id: str = None, **kwargs) -> List[Dict[str, Any]]:
        """Get audit trail for the session"""
        return self.audit_trail.get_audit_trail(session_id=session_id, user_id=user_id, **kwargs)
    
    def get_decision_history(self, session_id: str = None, user_id: str = None, **kwargs) -> List[Dict[str, Any]]:
        """Get decision history for the session"""
        return self.audit_trail.get_decision_history(session_id=session_id, user_id=user_id, **kwargs)
    
    def export_audit_report(self, **kwargs) -> str:
        """Export audit report"""
        return self.audit_trail.export_audit_report(**kwargs)