import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from src.api.setup_api import logger

# -----------------------------
# Consistency & Interpretability System
# -----------------------------
class ConsistencyValidator:
    """Validates decision consistency against historical cases and patterns"""
    
    def __init__(self):
        self.decision_patterns = {
            "age_based": {
                "pediatric": {"age_range": (0, 18), "typical_decisions": ["approved", "conditional"]},
                "adult": {"age_range": (18, 65), "typical_decisions": ["approved", "rejected", "conditional"]},
                "geriatric": {"age_range": (65, 120), "typical_decisions": ["conditional", "rejected"]}
            },
            "procedure_based": {
                "knee_surgery": {"typical_amount": "₹50000", "confidence_range": (0.7, 1.0)},
                "heart_bypass": {"typical_amount": "₹100000", "confidence_range": (0.8, 1.0)},
                "cataract": {"typical_amount": "₹25000", "confidence_range": (0.6, 0.9)},
                "cosmetic": {"typical_amount": "₹0", "confidence_range": (0.9, 1.0)}
            },
            "policy_duration": {
                "short": {"range": (0, 3), "risk_factor": "high"},
                "medium": {"range": (3, 12), "risk_factor": "medium"},
                "long": {"range": (12, 60), "risk_factor": "low"}
            }
        }
        
        # Historical decision patterns
        self.historical_patterns = {
            "decision_frequency": {
                "approved": 0.65,
                "rejected": 0.25,
                "conditional": 0.10
            },
            "amount_ranges": {
                "knee_surgery": {"min": "₹40000", "max": "₹60000", "avg": "₹50000"},
                "heart_bypass": {"min": "₹80000", "max": "₹120000", "avg": "₹100000"},
                "cataract": {"min": "₹20000", "max": "₹30000", "avg": "₹25000"}
            }
        }
        
        logger.info("Consistency Validator initialized")
    
    def validate_decision_consistency(self, 
                                    current_decision: Dict[str, Any], 
                                    query_context: Dict[str, Any],
                                    historical_cases: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate decision consistency against patterns and historical cases"""
        try:
            validation_results = {
                "is_consistent": True,
                "confidence_score": 0.0,
                "warnings": [],
                "anomalies": [],
                "pattern_matches": [],
                "historical_comparison": {}
            }
            
            # Step 1: Pattern-based validation
            pattern_validation = self._validate_against_patterns(current_decision, query_context)
            validation_results.update(pattern_validation)
            
            # Step 2: Historical comparison
            if historical_cases:
                historical_validation = self._compare_with_historical_cases(
                    current_decision, query_context, historical_cases
                )
                validation_results["historical_comparison"] = historical_validation
            
            # Step 3: Decision frequency validation
            frequency_validation = self._validate_decision_frequency(current_decision)
            validation_results.update(frequency_validation)
            
            # Step 4: Amount consistency validation
            amount_validation = self._validate_amount_consistency(current_decision, query_context)
            validation_results.update(amount_validation)
            
            # Calculate overall consistency score
            validation_results["confidence_score"] = self._calculate_consistency_score(validation_results)
            
            # Determine if decision is consistent
            validation_results["is_consistent"] = (
                len(validation_results["warnings"]) == 0 and 
                len(validation_results["anomalies"]) == 0 and
                validation_results["confidence_score"] > 0.7
            )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Consistency validation failed: {e}")
            return {
                "is_consistent": False,
                "confidence_score": 0.0,
                "error": str(e),
                "warnings": ["Consistency validation failed"],
                "anomalies": []
            }
    
    def _validate_against_patterns(self, 
                                 current_decision: Dict[str, Any], 
                                 query_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate decision against known patterns"""
        warnings = []
        anomalies = []
        pattern_matches = []
        
        parsed = query_context.get("parsed_entities", {})
        decision_status = current_decision.get("status", "").lower()
        decision_amount = current_decision.get("amount", "₹0")
        
        # Age-based pattern validation
        if parsed.get("age"):
            age = int(parsed["age"])
            age_category = self._get_age_category(age)
            age_pattern = self.decision_patterns["age_based"].get(age_category, {})
            
            if age_pattern:
                typical_decisions = age_pattern.get("typical_decisions", [])
                if decision_status not in typical_decisions:
                    warnings.append(f"Decision '{decision_status}' unusual for age category '{age_category}'")
                else:
                    pattern_matches.append(f"Age-based decision pattern matches ({age_category})")
        
        # Procedure-based pattern validation
        if parsed.get("procedure"):
            procedure = parsed["procedure"].lower()
            procedure_category = self._get_procedure_category(procedure)
            procedure_pattern = self.decision_patterns["procedure_based"].get(procedure_category, {})
            
            if procedure_pattern:
                typical_amount = procedure_pattern.get("typical_amount", "₹0")
                confidence_range = procedure_pattern.get("confidence_range", (0.0, 1.0))
                
                # Check amount consistency
                if decision_amount != typical_amount and decision_status == "approved":
                    warnings.append(f"Amount '{decision_amount}' differs from typical '{typical_amount}' for {procedure_category}")
                
                # Check confidence range
                current_confidence = current_decision.get("confidence", 0.0)
                if not (confidence_range[0] <= current_confidence <= confidence_range[1]):
                    warnings.append(f"Confidence {current_confidence:.2f} outside typical range {confidence_range} for {procedure_category}")
                else:
                    pattern_matches.append(f"Procedure-based pattern matches ({procedure_category})")
        
        # Policy duration validation
        if parsed.get("policy_duration"):
            duration_months = self._extract_duration_months(parsed["policy_duration"])
            duration_category = self._get_duration_category(duration_months)
            duration_pattern = self.decision_patterns["policy_duration"].get(duration_category, {})
            
            if duration_pattern:
                risk_factor = duration_pattern.get("risk_factor", "medium")
                if risk_factor == "high" and decision_status == "approved":
                    warnings.append(f"Approval with high-risk policy duration ({duration_category})")
                else:
                    pattern_matches.append(f"Policy duration pattern matches ({duration_category})")
        
        return {
            "warnings": warnings,
            "anomalies": anomalies,
            "pattern_matches": pattern_matches
        }
    
    def _compare_with_historical_cases(self, 
                                     current_decision: Dict[str, Any], 
                                     query_context: Dict[str, Any],
                                     historical_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare current decision with historical cases"""
        comparison_results = {
            "similar_cases": [],
            "decision_consistency": 0.0,
            "amount_consistency": 0.0,
            "confidence_consistency": 0.0
        }
        
        if not historical_cases:
            return comparison_results
        
        # Find similar cases
        similar_cases = self._find_similar_cases(query_context, historical_cases)
        comparison_results["similar_cases"] = similar_cases
        
        if similar_cases:
            # Calculate consistency metrics
            decision_consistency = self._calculate_decision_consistency(current_decision, similar_cases)
            amount_consistency = self._calculate_amount_consistency(current_decision, similar_cases)
            confidence_consistency = self._calculate_confidence_consistency(current_decision, similar_cases)
            
            comparison_results.update({
                "decision_consistency": decision_consistency,
                "amount_consistency": amount_consistency,
                "confidence_consistency": confidence_consistency
            })
        
        return comparison_results
    
    def _validate_decision_frequency(self, current_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Validate decision against historical frequency patterns"""
        warnings = []
        decision_status = current_decision.get("status", "").lower()
        
        # Check against historical frequency
        expected_frequency = self.historical_patterns["decision_frequency"].get(decision_status, 0.0)
        
        if expected_frequency < 0.1:  # Less than 10% frequency
            warnings.append(f"Decision '{decision_status}' has low historical frequency ({expected_frequency:.1%})")
        
        return {"warnings": warnings}
    
    def _validate_amount_consistency(self, 
                                   current_decision: Dict[str, Any], 
                                   query_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate amount consistency against typical ranges"""
        warnings = []
        anomalies = []
        
        parsed = query_context.get("parsed_entities", {})
        decision_amount = current_decision.get("amount", "₹0")
        decision_status = current_decision.get("status", "").lower()
        
        if parsed.get("procedure") and decision_status == "approved":
            procedure = parsed["procedure"].lower()
            procedure_category = self._get_procedure_category(procedure)
            amount_ranges = self.historical_patterns["amount_ranges"].get(procedure_category, {})
            
            if amount_ranges:
                min_amount = self._parse_amount(amount_ranges.get("min", "₹0"))
                max_amount = self._parse_amount(amount_ranges.get("max", "₹0"))
                current_amount = self._parse_amount(decision_amount)
                
                if current_amount < min_amount:
                    warnings.append(f"Amount {decision_amount} below typical minimum {amount_ranges['min']}")
                elif current_amount > max_amount:
                    warnings.append(f"Amount {decision_amount} above typical maximum {amount_ranges['max']}")
                else:
                    # Amount is within expected range
                    pass
        
        return {"warnings": warnings, "anomalies": anomalies}
    
    def _get_age_category(self, age: int) -> str:
        """Categorize age into age groups"""
        if age < 18:
            return "pediatric"
        elif age < 65:
            return "adult"
        else:
            return "geriatric"
    
    def _get_procedure_category(self, procedure: str) -> str:
        """Categorize procedure into procedure groups"""
        if "knee" in procedure:
            return "knee_surgery"
        elif "heart" in procedure or "bypass" in procedure:
            return "heart_bypass"
        elif "cataract" in procedure or "eye" in procedure:
            return "cataract"
        elif "cosmetic" in procedure:
            return "cosmetic"
        else:
            return "general"
    
    def _get_duration_category(self, months: int) -> str:
        """Categorize policy duration"""
        if months < 3:
            return "short"
        elif months < 12:
            return "medium"
        else:
            return "long"
    
    def _extract_duration_months(self, duration_str: str) -> int:
        """Extract duration in months from string"""
        try:
            parts = duration_str.split()
            value = int(parts[0])
            unit = parts[1].lower()
            
            if "month" in unit:
                return value
            elif "year" in unit:
                return value * 12
            else:
                return 0
        except:
            return 0
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        try:
            # Remove currency symbols and commas
            clean_amount = amount_str.replace("₹", "").replace(",", "").replace("Rs", "").replace(".", "")
            return float(clean_amount)
        except:
            return 0.0
    
    def _find_similar_cases(self, 
                           query_context: Dict[str, Any], 
                           historical_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find similar historical cases based on query context"""
        similar_cases = []
        parsed = query_context.get("parsed_entities", {})
        
        for case in historical_cases:
            similarity_score = self._calculate_case_similarity(parsed, case)
            if similarity_score > 0.7:  # High similarity threshold
                case["similarity_score"] = similarity_score
                similar_cases.append(case)
        
        # Sort by similarity score
        similar_cases.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        return similar_cases[:5]  # Return top 5 similar cases
    
    def _calculate_case_similarity(self, 
                                 current_parsed: Dict[str, Any], 
                                 historical_case: Dict[str, Any]) -> float:
        """Calculate similarity between current case and historical case"""
        similarity_score = 0.0
        matching_fields = 0
        total_fields = 0
        
        # Compare key fields
        fields_to_compare = ["age", "gender", "procedure", "location", "policy_duration"]
        
        for field in fields_to_compare:
            if field in current_parsed and field in historical_case:
                total_fields += 1
                if current_parsed[field] == historical_case[field]:
                    matching_fields += 1
                elif field == "age":
                    # Age similarity (within 10 years)
                    current_age = int(current_parsed[field])
                    historical_age = int(historical_case[field])
                    if abs(current_age - historical_age) <= 10:
                        matching_fields += 0.5
        
        if total_fields > 0:
            similarity_score = matching_fields / total_fields
        
        return similarity_score
    
    def _calculate_decision_consistency(self, 
                                      current_decision: Dict[str, Any], 
                                      similar_cases: List[Dict[str, Any]]) -> float:
        """Calculate decision consistency with similar cases"""
        if not similar_cases:
            return 0.0
        
        current_status = current_decision.get("status", "").lower()
        matching_decisions = sum(1 for case in similar_cases 
                               if case.get("decision", "").lower() == current_status)
        
        return matching_decisions / len(similar_cases)
    
    def _calculate_amount_consistency(self, 
                                    current_decision: Dict[str, Any], 
                                    similar_cases: List[Dict[str, Any]]) -> float:
        """Calculate amount consistency with similar cases"""
        if not similar_cases:
            return 0.0
        
        current_amount = self._parse_amount(current_decision.get("amount", "₹0"))
        similar_amounts = [self._parse_amount(case.get("amount", "₹0")) for case in similar_cases]
        
        if not similar_amounts:
            return 0.0
        
        avg_amount = sum(similar_amounts) / len(similar_amounts)
        if avg_amount == 0:
            return 0.0
        
        # Calculate consistency based on how close current amount is to average
        deviation = abs(current_amount - avg_amount) / avg_amount
        return max(0.0, 1.0 - deviation)
    
    def _calculate_confidence_consistency(self, 
                                       current_decision: Dict[str, Any], 
                                       similar_cases: List[Dict[str, Any]]) -> float:
        """Calculate confidence consistency with similar cases"""
        if not similar_cases:
            return 0.0
        
        current_confidence = current_decision.get("confidence", 0.0)
        similar_confidences = [case.get("confidence", 0.0) for case in similar_cases]
        
        if not similar_confidences:
            return 0.0
        
        avg_confidence = sum(similar_confidences) / len(similar_confidences)
        if avg_confidence == 0:
            return 0.0
        
        # Calculate consistency based on how close current confidence is to average
        deviation = abs(current_confidence - avg_confidence) / avg_confidence
        return max(0.0, 1.0 - deviation)
    
    def _calculate_consistency_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall consistency score"""
        base_score = 1.0
        
        # Deduct for warnings
        warning_penalty = len(validation_results.get("warnings", [])) * 0.1
        base_score -= min(warning_penalty, 0.5)
        
        # Deduct for anomalies
        anomaly_penalty = len(validation_results.get("anomalies", [])) * 0.2
        base_score -= min(anomaly_penalty, 0.5)
        
        # Bonus for pattern matches
        pattern_bonus = len(validation_results.get("pattern_matches", [])) * 0.05
        base_score += min(pattern_bonus, 0.2)
        
        return max(0.0, min(1.0, base_score)) 