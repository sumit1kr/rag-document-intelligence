import re
import spacy
import logging
from typing import Dict, Optional, List, Any, Tuple
from src.api.setup_api import logger

# -----------------------------
# Enhanced Query Processing
# -----------------------------
class EnhancedQueryProcessor:
    """Advanced query processing with semantic understanding and validation"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_trf")
        except OSError:
            # Fallback to smaller model
            self.nlp = spacy.load("en_core_web_sm")
        
        # Enhanced procedure keywords with synonyms
        self.procedure_keywords = {
            "knee replacement": ["knee replacement", "knee surgery", "knee operation", "arthroplasty", "knee procedure"],
            "hip replacement": ["hip replacement", "hip surgery", "hip arthroplasty", "hip procedure"],
            "cataract surgery": ["cataract", "eye surgery", "cataract removal", "ophthalmic surgery"],
            "angioplasty": ["angioplasty", "heart stent", "stent placement", "coronary angioplasty", "pci"],
            "heart bypass": ["bypass surgery", "cabg", "heart bypass", "coronary bypass", "cardiac bypass"],
            "appendectomy": ["appendix removal", "appendectomy", "appendicitis surgery"],
            "delivery": ["childbirth", "delivery", "labour", "normal delivery", "cesarean", "c-section", "obstetric"],
            "fracture": ["bone fracture", "fractured", "broken bone", "orthopedic injury"],
            "ivf": ["ivf", "fertility treatment", "infertility", "insemination", "in vitro fertilization"],
            "abortion": ["abortion", "medical termination", "mtp", "ectopic pregnancy", "pregnancy termination"],
            "cosmetic": ["rhinoplasty", "nose job", "cosmetic surgery", "plastic surgery", "aesthetic surgery"],
        }
        
        # Medical condition synonyms
        self.condition_synonyms = {
            "diabetes": ["diabetic", "diabetes mellitus", "type 1", "type 2"],
            "hypertension": ["high blood pressure", "htn", "hypertensive"],
            "asthma": ["bronchial asthma", "respiratory condition"],
            "cancer": ["malignancy", "tumor", "carcinoma", "oncology"],
            "heart disease": ["cardiac", "cardiovascular", "heart condition"],
        }
        
        # Query validation rules
        self.validation_rules = {
            "required_fields": ["procedure"],  # At least procedure should be mentioned
            "optional_fields": ["age", "gender", "location", "policy_duration"],
            "min_query_length": 5,
            "max_query_length": 500
        }
        
        logger.info("Enhanced Query Processor initialized")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Main entry point for enhanced query processing"""
        try:
            # Step 1: Basic parsing
            parsed = self._parse_basic(query)
            
            # Step 2: Query validation
            validation_result = self._validate_query(query, parsed)
            
            # Step 3: Semantic expansion
            expanded_query = self._semantic_expansion(query, parsed)
            
            # Step 4: Query disambiguation
            disambiguated = self._disambiguate_query(query, parsed)
            
            # Step 5: Multi-hop reasoning preparation
            reasoning_context = self._prepare_reasoning_context(query, parsed)
            
            return {
                "original_query": query,
                "parsed_entities": parsed,
                "validation": validation_result,
                "expanded_query": expanded_query,
                "disambiguated": disambiguated,
                "reasoning_context": reasoning_context,
                "processing_metadata": {
                    "query_length": len(query),
                    "entities_found": len([v for v in parsed.values() if v]),
                    "confidence_score": self._calculate_confidence(parsed, validation_result)
                }
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "original_query": query,
                "error": str(e),
                "parsed_entities": {},
                "validation": {"is_valid": False, "errors": [str(e)]}
            }
    
    def _parse_basic(self, query: str) -> Dict[str, Optional[str]]:
        """Enhanced basic parsing with better entity extraction"""
        query = query.lower().strip()
        doc = self.nlp(query)
        
        parsed = {
            "age": None,
            "gender": None,
            "procedure": None,
            "location": None,
            "policy_duration": None,
            "medical_condition": None,
            "urgency": None,
            "coverage_type": None
        }
        
        # Enhanced AGE extraction
        age_patterns = [
            r'(\d{1,3})\s*(year[- ]?old|yrs?|y/o|age)',
            r'age\s*(\d{1,3})',
            r'(\d{1,3})\s*yo',
        ]
        
        for pattern in age_patterns:
            age_match = re.search(pattern, query)
            if age_match:
                age = int(age_match.group(1))
                if 0 < age < 120:
                    parsed["age"] = str(age)
                    break
        
        # Enhanced GENDER extraction
        gender_patterns = [
            r'\b(male|female|m\b|f\b)\b',
            r'\b(man|woman|boy|girl)\b',
            r'\b(he|she|his|her)\b'
        ]
        
        for pattern in gender_patterns:
            gender_match = re.search(pattern, query)
            if gender_match:
                g = gender_match.group(1).lower()
                if g in ['male', 'm', 'man', 'he', 'his']:
                    parsed["gender"] = "M"
                elif g in ['female', 'f', 'woman', 'girl', 'she', 'her']:
                    parsed["gender"] = "F"
                break
        
        # Enhanced POLICY DURATION extraction
        duration_patterns = [
            r'(\d{1,2})\s*[- ]?(month|months|year|years)\b',
            r'(\d{1,2})\s*(month|year)\s*old\s*policy',
            r'policy\s*duration\s*(\d{1,2})\s*(month|year)',
        ]
        
        for pattern in duration_patterns:
            dur_match = re.search(pattern, query)
            if dur_match:
                value, unit = dur_match.groups()
                parsed["policy_duration"] = f"{value} {unit}"
                break
        
        # Enhanced LOCATION extraction
        for ent in doc.ents:
            if ent.label_ in ("GPE", "LOC", "FAC"):
                parsed["location"] = ent.text.title()
                break
        
        # Enhanced PROCEDURE extraction with synonyms
        for proc, aliases in self.procedure_keywords.items():
            for alias in aliases:
                if alias in query:
                    parsed["procedure"] = proc.title()
                    break
            if parsed["procedure"]:
                break
        
        # Fallback procedure extraction
        if not parsed["procedure"]:
            medical_keywords = ["surgery", "treatment", "procedure", "operation", "therapy"]
            noun_phrases = [
                chunk.text.strip()
                for chunk in doc.noun_chunks
                if any(word in chunk.text.lower() for word in medical_keywords)
            ]
            if noun_phrases:
                parsed["procedure"] = max(noun_phrases, key=len).replace("my ", "").strip().title()
        
        # MEDICAL CONDITION extraction
        for condition, synonyms in self.condition_synonyms.items():
            for synonym in synonyms:
                if synonym in query:
                    parsed["medical_condition"] = condition.title()
                    break
            if parsed["medical_condition"]:
                break
        
        # URGENCY detection
        urgency_keywords = ["emergency", "urgent", "immediate", "critical", "acute"]
        if any(keyword in query for keyword in urgency_keywords):
            parsed["urgency"] = "high"
        
        # COVERAGE TYPE detection
        coverage_keywords = {
            "comprehensive": ["comprehensive", "full coverage", "complete"],
            "basic": ["basic", "standard", "essential"],
            "premium": ["premium", "gold", "platinum", "premium coverage"]
        }
        
        for coverage_type, keywords in coverage_keywords.items():
            if any(keyword in query for keyword in keywords):
                parsed["coverage_type"] = coverage_type
                break
        
        return parsed
    
    def _validate_query(self, query: str, parsed: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Validate query and provide suggestions for improvement"""
        errors = []
        warnings = []
        suggestions = []
        
        # Length validation
        if len(query) < self.validation_rules["min_query_length"]:
            errors.append("Query too short. Please provide more details.")
        
        if len(query) > self.validation_rules["max_query_length"]:
            warnings.append("Query is very long. Consider being more concise.")
        
        # Required fields validation
        required_fields = self.validation_rules["required_fields"]
        missing_required = [field for field in required_fields if not parsed.get(field)]
        
        if missing_required:
            errors.append(f"Missing required information: {', '.join(missing_required)}")
            suggestions.append("Please specify the medical procedure or treatment.")
        
        # Optional fields suggestions
        optional_fields = self.validation_rules["optional_fields"]
        missing_optional = [field for field in optional_fields if not parsed.get(field)]
        
        if missing_optional:
            suggestions.append(f"Consider adding: {', '.join(missing_optional)}")
        
        # Age validation
        if parsed.get("age"):
            age = int(parsed["age"])
            if age < 0 or age > 120:
                errors.append("Invalid age specified.")
        
        # Gender validation
        if parsed.get("gender") and parsed["gender"] not in ["M", "F"]:
            errors.append("Invalid gender specification.")
        
        # Policy duration validation
        if parsed.get("policy_duration"):
            if "month" in parsed["policy_duration"]:
                months = int(parsed["policy_duration"].split()[0])
                if months < 1 or months > 60:
                    warnings.append("Policy duration seems unusual. Please verify.")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "completeness_score": self._calculate_completeness(parsed)
        }
    
    def _semantic_expansion(self, query: str, parsed: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Expand query semantically for better retrieval"""
        expanded_terms = []
        related_concepts = []
        
        # Expand procedure terms
        if parsed.get("procedure"):
            procedure = parsed["procedure"].lower()
            for proc, aliases in self.procedure_keywords.items():
                if proc in procedure or any(alias in procedure for alias in aliases):
                    expanded_terms.extend(aliases)
                    # Add related medical concepts
                    if "surgery" in proc:
                        related_concepts.extend(["pre-operative", "post-operative", "recovery"])
                    if "heart" in proc:
                        related_concepts.extend(["cardiology", "cardiovascular", "cardiac"])
                    if "eye" in proc or "cataract" in proc:
                        related_concepts.extend(["ophthalmology", "vision", "optical"])
                    break
        
        # Expand medical conditions
        if parsed.get("medical_condition"):
            condition = parsed["medical_condition"].lower()
            for cond, synonyms in self.condition_synonyms.items():
                if cond in condition or any(syn in condition for syn in synonyms):
                    expanded_terms.extend(synonyms)
                    break
        
        # Add demographic context
        if parsed.get("age"):
            age = int(parsed["age"])
            if age < 18:
                related_concepts.append("pediatric")
            elif age > 65:
                related_concepts.append("geriatric")
        
        # Add urgency context
        if parsed.get("urgency") == "high":
            related_concepts.extend(["emergency", "urgent care", "critical"])
        
        return {
            "original_query": query,
            "expanded_terms": list(set(expanded_terms)),
            "related_concepts": list(set(related_concepts)),
            "semantic_context": {
                "medical_domain": self._identify_medical_domain(parsed),
                "urgency_level": parsed.get("urgency", "normal"),
                "complexity": self._assess_complexity(parsed)
            }
        }
    
    def _disambiguate_query(self, query: str, parsed: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Disambiguate vague or unclear queries"""
        ambiguities = []
        clarifications = []
        
        # Check for vague procedures
        if parsed.get("procedure"):
            procedure = parsed["procedure"].lower()
            if "surgery" in procedure and len(procedure.split()) == 1:
                ambiguities.append("Vague procedure: 'surgery' could refer to multiple types")
                clarifications.append("Please specify the type of surgery (e.g., knee surgery, heart surgery)")
        
        # Check for missing critical information
        if not parsed.get("age") and "pediatric" not in query and "child" not in query:
            clarifications.append("Age information would help determine coverage eligibility")
        
        if not parsed.get("location"):
            clarifications.append("Location information would help determine network coverage")
        
        # Check for conflicting information
        if parsed.get("age") and parsed.get("procedure"):
            age = int(parsed["age"])
            procedure = parsed["procedure"].lower()
            
            if age < 18 and "adult" in procedure:
                ambiguities.append("Age-procedure mismatch detected")
            elif age > 65 and "pediatric" in procedure:
                ambiguities.append("Age-procedure mismatch detected")
        
        return {
            "ambiguities": ambiguities,
            "clarifications": clarifications,
            "confidence": "high" if len(ambiguities) == 0 else "medium" if len(ambiguities) < 2 else "low"
        }
    
    def _prepare_reasoning_context(self, query: str, parsed: Dict[str, Optional[str]]) -> Dict[str, Any]:
        """Prepare context for multi-hop reasoning"""
        reasoning_steps = []
        
        # Step 1: Demographic analysis
        if parsed.get("age") or parsed.get("gender"):
            reasoning_steps.append({
                "step": "demographic_analysis",
                "description": "Analyzing patient demographics for coverage eligibility",
                "data": {
                    "age": parsed.get("age"),
                    "gender": parsed.get("gender")
                }
            })
        
        # Step 2: Procedure analysis
        if parsed.get("procedure"):
            reasoning_steps.append({
                "step": "procedure_analysis",
                "description": "Evaluating procedure coverage and requirements",
                "data": {
                    "procedure": parsed.get("procedure"),
                    "medical_condition": parsed.get("medical_condition")
                }
            })
        
        # Step 3: Policy analysis
        if parsed.get("policy_duration"):
            reasoning_steps.append({
                "step": "policy_analysis",
                "description": "Checking policy duration and waiting periods",
                "data": {
                    "policy_duration": parsed.get("policy_duration"),
                    "coverage_type": parsed.get("coverage_type")
                }
            })
        
        # Step 4: Location analysis
        if parsed.get("location"):
            reasoning_steps.append({
                "step": "location_analysis",
                "description": "Evaluating network coverage and regional policies",
                "data": {
                    "location": parsed.get("location")
                }
            })
        
        return {
            "reasoning_steps": reasoning_steps,
            "total_steps": len(reasoning_steps),
            "complexity_level": "high" if len(reasoning_steps) > 3 else "medium" if len(reasoning_steps) > 1 else "low"
        }
    
    def _calculate_confidence(self, parsed: Dict[str, Optional[str]], validation: Dict[str, Any]) -> float:
        """Calculate confidence score for the parsed query"""
        confidence = 0.0
        
        # Base confidence from validation
        if validation.get("is_valid", False):
            confidence += 0.3
        
        # Completeness bonus
        completeness = validation.get("completeness_score", 0.0)
        confidence += completeness * 0.4
        
        # Entity extraction bonus
        entities_found = len([v for v in parsed.values() if v])
        confidence += min(entities_found / 8.0, 0.3)  # Max 0.3 for entities
        
        return min(confidence, 1.0)
    
    def _calculate_completeness(self, parsed: Dict[str, Optional[str]]) -> float:
        """Calculate completeness score of the query"""
        total_fields = len(parsed)
        filled_fields = len([v for v in parsed.values() if v])
        return filled_fields / total_fields
    
    def _identify_medical_domain(self, parsed: Dict[str, Optional[str]]) -> str:
        """Identify the medical domain of the query"""
        if parsed.get("procedure"):
            procedure = parsed["procedure"].lower()
            if any(word in procedure for word in ["heart", "cardiac", "angioplasty", "bypass"]):
                return "cardiology"
            elif any(word in procedure for word in ["eye", "cataract", "ophthalmic"]):
                return "ophthalmology"
            elif any(word in procedure for word in ["knee", "hip", "fracture", "orthopedic"]):
                return "orthopedics"
            elif any(word in procedure for word in ["delivery", "pregnancy", "obstetric"]):
                return "obstetrics"
            elif any(word in procedure for word in ["ivf", "fertility"]):
                return "reproductive_medicine"
            else:
                return "general_surgery"
        return "unknown"
    
    def _assess_complexity(self, parsed: Dict[str, Optional[str]]) -> str:
        """Assess the complexity of the medical case"""
        complexity_score = 0
        
        # Age complexity
        if parsed.get("age"):
            age = int(parsed["age"])
            if age < 18 or age > 65:
                complexity_score += 1
        
        # Procedure complexity
        if parsed.get("procedure"):
            procedure = parsed["procedure"].lower()
            complex_procedures = ["heart bypass", "angioplasty", "ivf", "cosmetic"]
            if any(proc in procedure for proc in complex_procedures):
                complexity_score += 2
        
        # Medical condition complexity
        if parsed.get("medical_condition"):
            complexity_score += 1
        
        # Urgency complexity
        if parsed.get("urgency") == "high":
            complexity_score += 1
        
        if complexity_score >= 3:
            return "high"
        elif complexity_score >= 1:
            return "medium"
        else:
            return "low" 