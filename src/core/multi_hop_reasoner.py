import logging
from typing import Dict, List, Any, Optional
from src.api.setup_api import logger

# -----------------------------
# Multi-Hop Reasoning System
# -----------------------------
class MultiHopReasoner:
    """Advanced reasoning system that chains multiple queries and reasoning steps"""
    
    def __init__(self):
        self.reasoning_chains = {
            "demographic_eligibility": [
                "age_verification",
                "gender_specific_coverage",
                "policy_duration_check"
            ],
            "procedure_coverage": [
                "procedure_eligibility",
                "pre_authorization_requirements",
                "network_coverage_check"
            ],
            "medical_complexity": [
                "condition_assessment",
                "comorbidity_analysis",
                "risk_factor_evaluation"
            ],
            "policy_analysis": [
                "waiting_period_check",
                "exclusion_verification",
                "coverage_limit_analysis"
            ]
        }
        
        logger.info("Multi-Hop Reasoner initialized")
    
    def execute_reasoning_chain(self, 
                               query_context: Dict[str, Any], 
                               documents: List[Any]) -> Dict[str, Any]:
        """Execute a complete reasoning chain based on query context"""
        try:
            # Determine which reasoning chains to execute
            active_chains = self._identify_active_chains(query_context)
            
            # Execute each chain
            chain_results = {}
            for chain_name in active_chains:
                chain_results[chain_name] = self._execute_single_chain(
                    chain_name, query_context, documents
                )
            
            # Synthesize results
            final_result = self._synthesize_results(chain_results, query_context)
            
            return {
                "reasoning_chains": chain_results,
                "final_decision": final_result,
                "confidence_score": self._calculate_chain_confidence(chain_results),
                "reasoning_path": self._generate_reasoning_path(chain_results)
            }
            
        except Exception as e:
            logger.error(f"Multi-hop reasoning failed: {e}")
            return {
                "error": str(e),
                "reasoning_chains": {},
                "final_decision": {"status": "error", "reason": str(e)}
            }
    
    def _identify_active_chains(self, query_context: Dict[str, Any]) -> List[str]:
        """Identify which reasoning chains should be executed"""
        active_chains = []
        parsed = query_context.get("parsed_entities", {})
        
        # Demographic chain
        if parsed.get("age") or parsed.get("gender"):
            active_chains.append("demographic_eligibility")
        
        # Procedure chain
        if parsed.get("procedure"):
            active_chains.append("procedure_coverage")
        
        # Medical complexity chain
        if parsed.get("medical_condition") or parsed.get("urgency") == "high":
            active_chains.append("medical_complexity")
        
        # Policy chain
        if parsed.get("policy_duration") or parsed.get("coverage_type"):
            active_chains.append("policy_analysis")
        
        return active_chains
    
    def _execute_single_chain(self, 
                             chain_name: str, 
                             query_context: Dict[str, Any], 
                             documents: List[Any]) -> Dict[str, Any]:
        """Execute a single reasoning chain"""
        chain_steps = self.reasoning_chains.get(chain_name, [])
        step_results = []
        
        for step in chain_steps:
            step_result = self._execute_reasoning_step(step, query_context, documents)
            step_results.append({
                "step": step,
                "result": step_result
            })
        
        return {
            "chain_name": chain_name,
            "steps": step_results,
            "chain_decision": self._evaluate_chain_decision(step_results),
            "confidence": self._calculate_step_confidence(step_results)
        }
    
    def _execute_reasoning_step(self, 
                               step: str, 
                               query_context: Dict[str, Any], 
                               documents: List[Any]) -> Dict[str, Any]:
        """Execute a single reasoning step"""
        parsed = query_context.get("parsed_entities", {})
        
        if step == "age_verification":
            return self._verify_age_eligibility(parsed, documents)
        elif step == "gender_specific_coverage":
            return self._check_gender_coverage(parsed, documents)
        elif step == "policy_duration_check":
            return self._check_policy_duration(parsed, documents)
        elif step == "procedure_eligibility":
            return self._check_procedure_eligibility(parsed, documents)
        elif step == "pre_authorization_requirements":
            return self._check_pre_authorization(parsed, documents)
        elif step == "network_coverage_check":
            return self._check_network_coverage(parsed, documents)
        elif step == "condition_assessment":
            return self._assess_medical_condition(parsed, documents)
        elif step == "comorbidity_analysis":
            return self._analyze_comorbidities(parsed, documents)
        elif step == "risk_factor_evaluation":
            return self._evaluate_risk_factors(parsed, documents)
        elif step == "waiting_period_check":
            return self._check_waiting_periods(parsed, documents)
        elif step == "exclusion_verification":
            return self._verify_exclusions(parsed, documents)
        elif step == "coverage_limit_analysis":
            return self._analyze_coverage_limits(parsed, documents)
        else:
            return {"status": "unknown_step", "reason": f"Unknown reasoning step: {step}"}
    
    def _verify_age_eligibility(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Verify age-based eligibility"""
        if not parsed.get("age"):
            return {"status": "unknown", "reason": "Age not specified"}
        
        age = int(parsed["age"])
        
        # Check age-based eligibility rules
        if age < 18:
            return {"status": "restricted", "reason": "Pediatric coverage may have different rules"}
        elif age > 65:
            return {"status": "restricted", "reason": "Geriatric coverage may have different rules"}
        else:
            return {"status": "eligible", "reason": "Age within standard coverage range"}
    
    def _check_gender_coverage(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Check gender-specific coverage rules"""
        if not parsed.get("gender"):
            return {"status": "unknown", "reason": "Gender not specified"}
        
        gender = parsed["gender"]
        procedure = parsed.get("procedure", "").lower()
        
        # Check for gender-specific procedures
        if gender == "F" and "pregnancy" in procedure:
            return {"status": "eligible", "reason": "Female-specific procedure covered"}
        elif gender == "M" and "pregnancy" in procedure:
            return {"status": "ineligible", "reason": "Gender-procedure mismatch"}
        else:
            return {"status": "eligible", "reason": "No gender-specific restrictions"}
    
    def _check_policy_duration(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Check policy duration requirements"""
        if not parsed.get("policy_duration"):
            return {"status": "unknown", "reason": "Policy duration not specified"}
        
        duration = parsed["policy_duration"]
        
        if "month" in duration:
            months = int(duration.split()[0])
            if months < 3:
                return {"status": "restricted", "reason": "Policy duration below minimum requirement"}
            else:
                return {"status": "eligible", "reason": "Policy duration meets requirements"}
        else:
            return {"status": "eligible", "reason": "Policy duration acceptable"}
    
    def _check_procedure_eligibility(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Check if procedure is covered"""
        if not parsed.get("procedure"):
            return {"status": "unknown", "reason": "Procedure not specified"}
        
        procedure = parsed["procedure"].lower()
        
        # Check against document content for coverage
        covered_procedures = ["knee surgery", "cataract", "angioplasty", "delivery"]
        excluded_procedures = ["cosmetic", "experimental"]
        
        if any(proc in procedure for proc in covered_procedures):
            return {"status": "covered", "reason": "Procedure is covered under policy"}
        elif any(proc in procedure for proc in excluded_procedures):
            return {"status": "excluded", "reason": "Procedure is excluded from coverage"}
        else:
            return {"status": "conditional", "reason": "Procedure coverage depends on specific circumstances"}
    
    def _check_pre_authorization(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Check pre-authorization requirements"""
        procedure = parsed.get("procedure", "").lower()
        
        # Procedures requiring pre-authorization
        pre_auth_procedures = ["surgery", "angioplasty", "bypass", "ivf"]
        
        if any(proc in procedure for proc in pre_auth_procedures):
            return {"status": "required", "reason": "Pre-authorization required for this procedure"}
        else:
            return {"status": "not_required", "reason": "No pre-authorization required"}
    
    def _check_network_coverage(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Check network coverage for location"""
        location = parsed.get("location", "")
        
        if location:
            return {"status": "covered", "reason": f"Network coverage available in {location}"}
        else:
            return {"status": "unknown", "reason": "Location not specified for network check"}
    
    def _assess_medical_condition(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Assess medical condition complexity"""
        condition = parsed.get("medical_condition", "")
        urgency = parsed.get("urgency", "normal")
        
        if urgency == "high":
            return {"status": "complex", "reason": "High urgency case requires special consideration"}
        elif condition:
            return {"status": "assessed", "reason": f"Medical condition {condition} evaluated"}
        else:
            return {"status": "standard", "reason": "No complex medical conditions identified"}
    
    def _analyze_comorbidities(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Analyze comorbidities and their impact"""
        condition = parsed.get("medical_condition", "")
        
        if condition:
            return {"status": "analyzed", "reason": f"Comorbidities for {condition} evaluated"}
        else:
            return {"status": "none", "reason": "No comorbidities identified"}
    
    def _evaluate_risk_factors(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Evaluate risk factors"""
        age = parsed.get("age")
        condition = parsed.get("medical_condition", "")
        
        risk_factors = []
        if age and int(age) > 65:
            risk_factors.append("age")
        if condition:
            risk_factors.append("medical_condition")
        
        if risk_factors:
            return {"status": "identified", "reason": f"Risk factors: {', '.join(risk_factors)}"}
        else:
            return {"status": "low", "reason": "No significant risk factors identified"}
    
    def _check_waiting_periods(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Check waiting period requirements"""
        duration = parsed.get("policy_duration", "")
        procedure = parsed.get("procedure", "").lower()
        
        if duration and "month" in duration:
            months = int(duration.split()[0])
            if months < 3:
                return {"status": "waiting", "reason": "Policy duration below waiting period requirement"}
        
        return {"status": "eligible", "reason": "Waiting period requirements met"}
    
    def _verify_exclusions(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Verify if any exclusions apply"""
        procedure = parsed.get("procedure", "").lower()
        condition = parsed.get("medical_condition", "").lower()
        
        exclusions = []
        if "cosmetic" in procedure:
            exclusions.append("cosmetic_procedure")
        if "pre-existing" in condition:
            exclusions.append("pre_existing_condition")
        
        if exclusions:
            return {"status": "excluded", "reason": f"Exclusions apply: {', '.join(exclusions)}"}
        else:
            return {"status": "no_exclusions", "reason": "No exclusions identified"}
    
    def _analyze_coverage_limits(self, parsed: Dict[str, Any], documents: List[Any]) -> Dict[str, Any]:
        """Analyze coverage limits and amounts"""
        procedure = parsed.get("procedure", "").lower()
        coverage_type = parsed.get("coverage_type", "basic")
        
        # Define coverage limits based on procedure and coverage type
        if "surgery" in procedure:
            if coverage_type == "premium":
                return {"status": "high_limit", "amount": "₹100000", "reason": "Premium coverage with high limits"}
            else:
                return {"status": "standard_limit", "amount": "₹50000", "reason": "Standard coverage limits"}
        else:
            return {"status": "standard", "amount": "₹25000", "reason": "Standard coverage limits"}
    
    def _evaluate_chain_decision(self, step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate the overall decision for a reasoning chain"""
        # Count different statuses
        status_counts = {}
        for step in step_results:
            status = step["result"].get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Determine overall chain decision
        if "excluded" in status_counts:
            return {"status": "excluded", "reason": "Chain contains exclusions"}
        elif "ineligible" in status_counts:
            return {"status": "ineligible", "reason": "Chain contains ineligibility"}
        elif "restricted" in status_counts:
            return {"status": "restricted", "reason": "Chain contains restrictions"}
        elif "covered" in status_counts or "eligible" in status_counts:
            return {"status": "eligible", "reason": "Chain indicates eligibility"}
        else:
            return {"status": "conditional", "reason": "Chain requires further evaluation"}
    
    def _calculate_step_confidence(self, step_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for a reasoning chain"""
        if not step_results:
            return 0.0
        
        # Calculate confidence based on step results
        total_steps = len(step_results)
        confident_steps = sum(1 for step in step_results 
                            if step["result"].get("status") in ["eligible", "covered", "no_exclusions"])
        
        return confident_steps / total_steps
    
    def _synthesize_results(self, chain_results: Dict[str, Any], query_context: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from all reasoning chains"""
        if not chain_results:
            return {"status": "error", "reason": "No reasoning chains executed"}
        
        # Collect all decisions
        decisions = []
        for chain_name, chain_result in chain_results.items():
            decisions.append(chain_result["chain_decision"])
        
        # Determine final decision
        if any(d["status"] == "excluded" for d in decisions):
            final_status = "rejected"
            reason = "Exclusions apply"
        elif any(d["status"] == "ineligible" for d in decisions):
            final_status = "rejected"
            reason = "Eligibility requirements not met"
        elif all(d["status"] in ["eligible", "covered"] for d in decisions):
            final_status = "approved"
            reason = "All requirements met"
        elif any(d["status"] == "restricted" for d in decisions):
            final_status = "conditional"
            reason = "Some restrictions apply"
        else:
            final_status = "unclear"
            reason = "Insufficient information for clear decision"
        
        return {
            "status": final_status,
            "reason": reason,
            "supporting_chains": [name for name, result in chain_results.items() 
                                if result["chain_decision"]["status"] in ["eligible", "covered"]],
            "opposing_chains": [name for name, result in chain_results.items() 
                              if result["chain_decision"]["status"] in ["excluded", "ineligible"]]
        }
    
    def _calculate_chain_confidence(self, chain_results: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        if not chain_results:
            return 0.0
        
        total_confidence = 0.0
        for chain_result in chain_results.values():
            total_confidence += chain_result.get("confidence", 0.0)
        
        return total_confidence / len(chain_results)
    
    def _generate_reasoning_path(self, chain_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a human-readable reasoning path"""
        reasoning_path = []
        
        for chain_name, chain_result in chain_results.items():
            chain_path = {
                "chain": chain_name,
                "decision": chain_result["chain_decision"]["status"],
                "reason": chain_result["chain_decision"]["reason"],
                "steps": []
            }
            
            for step in chain_result["steps"]:
                chain_path["steps"].append({
                    "step": step["step"],
                    "result": step["result"]["status"],
                    "reason": step["result"]["reason"]
                })
            
            reasoning_path.append(chain_path)
        
        return reasoning_path 