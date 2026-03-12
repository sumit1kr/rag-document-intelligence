import re
import logging
from typing import List, Dict, Any, Optional
from src.api.setup_api import logger

# -----------------------------
# Clause Extraction and Mapping
# -----------------------------
class ClauseExtractor:
    """Extracts and maps clauses from documents to decisions"""
    
    def __init__(self):
        # Common clause patterns
        self.clause_patterns = [
            r'(?:Section|Clause|Article|Paragraph)\s+(\d+(?:\.\d+)*)',
            r'(?:Chapter|Part)\s+(\d+)',
            r'(?:Subsection|Subclause)\s+(\d+(?:\.\d+)*)',
            r'(\d+\.\d+\.\d+)',  # Numbered sections like 3.2.1
            r'(\d+\.\d+)',        # Numbered sections like 3.2
        ]
        
        # Decision keywords for mapping
        self.approval_keywords = [
            "covered", "eligible", "approved", "included", "admissible", 
            "payable", "reimbursable", "authorized", "permitted", "allowed"
        ]
        
        self.rejection_keywords = [
            "not covered", "not eligible", "rejected", "excluded", 
            "declined", "denied", "not payable", "not admissible",
            "prohibited", "restricted", "excluded from coverage"
        ]
        
        self.conditional_keywords = [
            "subject to", "conditional upon", "depends on", "may be",
            "if approved", "pending", "under review", "requires"
        ]
        
        logger.info("Clause Extractor initialized")
    
    def extract_clauses(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """Extract structured clauses from documents"""
        clauses = []
        
        for i, doc in enumerate(documents):
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            metadata = getattr(doc, 'metadata', {})
            
            # Extract clause information
            clause_info = self._extract_clause_info(content, i, metadata)
            if clause_info:
                clauses.append(clause_info)
        
        logger.info(f"Extracted {len(clauses)} clauses from {len(documents)} documents")
        return clauses
    
    def _extract_clause_info(self, content: str, doc_index: int, metadata: Dict) -> Optional[Dict[str, Any]]:
        """Extract structured information from a document clause"""
        try:
            # Find clause identifier
            clause_id = self._find_clause_id(content)
            
            # Determine clause type and decision impact
            clause_type, decision_impact = self._analyze_clause_impact(content)
            
            # Calculate relevance score (simplified)
            relevance_score = self._calculate_relevance_score(content)
            
            return {
                "clause_id": clause_id or f"doc_{doc_index}",
                "clause_text": content.strip(),
                "clause_type": clause_type,
                "decision_impact": decision_impact,
                "relevance_score": relevance_score,
                "metadata": metadata,
                "source_document": metadata.get('source', f"Document {doc_index + 1}")
            }
            
        except Exception as e:
            logger.error(f"Error extracting clause info: {e}")
            return None
    
    def _find_clause_id(self, content: str) -> Optional[str]:
        """Find clause identifier in content"""
        for pattern in self.clause_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _analyze_clause_impact(self, content: str) -> tuple:
        """Analyze clause type and decision impact"""
        content_lower = content.lower()
        
        # Check for approval indicators
        if any(keyword in content_lower for keyword in self.approval_keywords):
            return "approval", "positive"
        
        # Check for rejection indicators
        if any(keyword in content_lower for keyword in self.rejection_keywords):
            return "rejection", "negative"
        
        # Check for conditional indicators
        if any(keyword in content_lower for keyword in self.conditional_keywords):
            return "conditional", "neutral"
        
        # Default to informational
        return "informational", "neutral"
    
    def _calculate_relevance_score(self, content: str) -> float:
        """Calculate relevance score for clause (0.0 to 1.0)"""
        # Simple heuristic based on content length and keyword density
        words = content.split()
        if not words:
            return 0.0
        
        # Count relevant keywords
        relevant_keywords = (
            self.approval_keywords + 
            self.rejection_keywords + 
            self.conditional_keywords
        )
        
        keyword_count = sum(1 for word in words if any(kw in word.lower() for kw in relevant_keywords))
        
        # Calculate score based on keyword density and content length
        keyword_density = keyword_count / len(words)
        length_factor = min(len(words) / 100, 1.0)  # Normalize by expected length
        
        score = (keyword_density * 0.7) + (length_factor * 0.3)
        return min(score, 1.0)

class EvidenceMapper:
    """Maps evidence clauses to decisions and provides structured output"""
    
    def __init__(self):
        self.clause_extractor = ClauseExtractor()
        logger.info("Evidence Mapper initialized")
    
    def create_structured_response(self, 
                                 question: str, 
                                 answer: str, 
                                 documents: List[Any],
                                 decision: str,
                                 amount: str) -> Dict[str, Any]:
        """Create structured JSON response with evidence mapping"""
        
        # Extract clauses from documents
        clauses = self.clause_extractor.extract_clauses(documents)
        
        # Map clauses to decision
        mapped_clauses = self._map_clauses_to_decision(clauses, decision, answer)
        
        # Create structured response
        structured_response = {
            "query": {
                "original": question,
                "parsed": self._parse_query_structure(question)
            },
            "decision": {
                "status": decision,
                "amount": amount,
                "confidence": self._calculate_decision_confidence(mapped_clauses, decision)
            },
            "justification": answer.strip(),
            "evidence": {
                "clauses": mapped_clauses,
                "total_clauses": len(mapped_clauses),
                "supporting_clauses": len([c for c in mapped_clauses if c['decision_impact'] == 'positive']),
                "opposing_clauses": len([c for c in mapped_clauses if c['decision_impact'] == 'negative'])
            },
            "metadata": {
                "timestamp": self._get_timestamp(),
                "processing_time": None,  # Could be added later
                "model_used": "llama-3.3-70b-versatile"
            }
        }
        
        return structured_response
    
    def _map_clauses_to_decision(self, 
                                clauses: List[Dict], 
                                decision: str, 
                                answer: str) -> List[Dict]:
        """Map clauses to the final decision"""
        mapped_clauses = []
        
        for clause in clauses:
            # Enhance clause with decision mapping
            enhanced_clause = clause.copy()
            
            # Add decision relevance
            enhanced_clause['decision_relevance'] = self._calculate_decision_relevance(
                clause, decision, answer
            )
            
            # Add evidence strength
            enhanced_clause['evidence_strength'] = self._calculate_evidence_strength(clause)
            
            # Add clause summary
            enhanced_clause['summary'] = self._generate_clause_summary(clause)
            
            mapped_clauses.append(enhanced_clause)
        
        # Sort by relevance score
        mapped_clauses.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return mapped_clauses
    
    def _calculate_decision_relevance(self, 
                                    clause: Dict, 
                                    decision: str, 
                                    answer: str) -> str:
        """Calculate how relevant a clause is to the final decision"""
        decision_lower = decision.lower()
        clause_impact = clause.get('decision_impact', 'neutral')
        
        if decision_lower == 'approved' and clause_impact == 'positive':
            return 'high'
        elif decision_lower == 'rejected' and clause_impact == 'negative':
            return 'high'
        elif clause_impact == 'neutral':
            return 'medium'
        else:
            return 'low'
    
    def _calculate_evidence_strength(self, clause: Dict) -> str:
        """Calculate the strength of evidence provided by a clause"""
        relevance_score = clause.get('relevance_score', 0.0)
        
        if relevance_score >= 0.8:
            return 'strong'
        elif relevance_score >= 0.5:
            return 'moderate'
        else:
            return 'weak'
    
    def _generate_clause_summary(self, clause: Dict) -> str:
        """Generate a brief summary of the clause"""
        text = clause.get('clause_text', '')
        if len(text) <= 100:
            return text
        
        # Take first 100 characters and add ellipsis
        return text[:100] + "..."
    
    def _parse_query_structure(self, question: str) -> Dict[str, Any]:
        """Parse query into structured components"""
        # This could be enhanced with the QueryInterpreter later
        return {
            "original_query": question,
            "query_type": "insurance_claim",
            "extracted_entities": {}  # Could be populated by QueryInterpreter
        }
    
    def _calculate_decision_confidence(self, 
                                     clauses: List[Dict], 
                                     decision: str) -> float:
        """Calculate confidence in the decision based on evidence"""
        if not clauses:
            return 0.0
        
        # Calculate confidence based on evidence strength and consistency
        supporting_clauses = [c for c in clauses if c['decision_impact'] == 'positive']
        opposing_clauses = [c for c in clauses if c['decision_impact'] == 'negative']
        
        total_relevance = sum(c['relevance_score'] for c in clauses)
        supporting_relevance = sum(c['relevance_score'] for c in supporting_clauses)
        opposing_relevance = sum(c['relevance_score'] for c in opposing_clauses)
        
        if total_relevance == 0:
            return 0.5  # Neutral confidence
        
        # Calculate confidence based on evidence balance
        if decision.lower() == 'approved':
            confidence = supporting_relevance / total_relevance
        elif decision.lower() == 'rejected':
            confidence = opposing_relevance / total_relevance
        else:
            confidence = 0.5  # Neutral for unclear decisions
        
        return min(confidence, 1.0)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat() 