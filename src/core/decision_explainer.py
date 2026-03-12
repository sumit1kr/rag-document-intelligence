import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.api.setup_api import logger

# -----------------------------
# Decision Explanation Templates
# -----------------------------
class DecisionExplainer:
    """Generates human-readable decision explanations with structured reasoning"""
    
    def __init__(self):
        self.explanation_templates = {
            "approved": {
                "template": "Based on the policy analysis, your claim for {procedure} has been **APPROVED** with a coverage amount of {amount}. This decision was made based on the following factors:\n\n{factors}\n\n**Key Supporting Evidence:**\n{evidence}\n\n**Confidence Level:** {confidence}%",
                "factors_template": "• Age and eligibility criteria met ({age} years old)\n• Procedure covered under policy terms\n• Policy duration requirements satisfied ({duration})\n• No exclusions or restrictions apply",
                "evidence_template": "• {clause_id}: {clause_summary}\n• Policy coverage confirmed for {procedure}\n• Amount within standard coverage limits"
            },
            "rejected": {
                "template": "After careful review of your claim for {procedure}, the decision is **REJECTED**. Here's the detailed explanation:\n\n{factors}\n\n**Primary Reasons for Rejection:**\n{evidence}\n\n**Confidence Level:** {confidence}%",
                "factors_template": "• {rejection_reason}\n• Policy terms and conditions not met\n• Coverage exclusions apply\n• Additional documentation may be required",
                "evidence_template": "• {clause_id}: {clause_summary}\n• Policy exclusion applies\n• Coverage criteria not satisfied"
            },
            "conditional": {
                "template": "Your claim for {procedure} has been **CONDITIONALLY APPROVED** with the following requirements:\n\n{factors}\n\n**Conditions for Approval:**\n{evidence}\n\n**Next Steps:**\n{next_steps}\n\n**Confidence Level:** {confidence}%",
                "factors_template": "• Additional documentation required\n• Pre-authorization needed\n• Specific conditions must be met\n• Coverage amount may vary based on final review",
                "evidence_template": "• {clause_id}: {clause_summary}\n• Conditional approval criteria met\n• Further review required",
                "next_steps_template": "• Submit required documentation\n• Obtain pre-authorization\n• Complete additional forms\n• Contact customer service for assistance"
            },
            "unclear": {
                "template": "The decision for your claim regarding {procedure} is **UNCLEAR** due to insufficient information. Here's what we found:\n\n{factors}\n\n**Missing Information:**\n{missing_info}\n\n**Recommendations:**\n{recommendations}\n\n**Confidence Level:** {confidence}%",
                "factors_template": "• Insufficient information provided\n• Policy terms unclear\n• Additional documentation needed\n• Manual review required",
                "missing_info_template": "• Complete medical documentation\n• Policy details and duration\n• Procedure specifications\n• Supporting medical reports",
                "recommendations_template": "• Provide additional documentation\n• Contact customer service\n• Submit complete claim form\n• Include all relevant medical records"
            }
        }
        
        # Explanation components
        self.explanation_components = {
            "risk_factors": {
                "high": "⚠️ **High Risk Factors Detected:** This case involves multiple risk factors that may affect coverage.",
                "medium": "⚠️ **Moderate Risk Factors:** Some risk factors were identified but are manageable.",
                "low": "✅ **Low Risk Factors:** Standard risk assessment with no significant concerns."
            },
            "complexity_levels": {
                "high": "🔍 **Complex Case:** This case requires detailed analysis due to multiple factors.",
                "medium": "📋 **Standard Complexity:** Normal processing with standard review procedures.",
                "low": "✅ **Simple Case:** Straightforward processing with minimal complexity."
            },
            "urgency_levels": {
                "high": "🚨 **Urgent Case:** This case requires immediate attention and expedited processing.",
                "medium": "⏰ **Standard Processing:** Normal processing timeline applies.",
                "low": "📅 **Regular Processing:** Standard processing timeline with no urgency."
            }
        }
        
        logger.info("Decision Explainer initialized")
    
    def generate_explanation(self, 
                           decision: Dict[str, Any],
                           query_context: Dict[str, Any],
                           reasoning_result: Dict[str, Any],
                           consistency_validation: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive decision explanation"""
        try:
            decision_status = decision.get("status", "unknown").lower()
            template = self.explanation_templates.get(decision_status, self.explanation_templates["unclear"])
            
            # Extract context information
            parsed = query_context.get("parsed_entities", {})
            procedure = parsed.get("procedure", "the procedure")
            amount = decision.get("amount", "N/A")
            confidence = int(decision.get("confidence", 0.0) * 100)
            
            # Generate explanation components
            factors = self._generate_factors(decision, parsed, reasoning_result)
            evidence = self._generate_evidence(reasoning_result, consistency_validation)
            
            # Generate additional components based on decision type
            additional_components = {}
            if decision_status == "conditional":
                additional_components["next_steps"] = self._generate_next_steps(decision, parsed)
            elif decision_status == "unclear":
                additional_components["missing_info"] = self._generate_missing_info(parsed)
                additional_components["recommendations"] = self._generate_recommendations(decision, parsed)
            
            # Build explanation text with all required components
            format_kwargs = {
                "procedure": procedure,
                "amount": amount,
                "factors": factors,
                "evidence": evidence,
                "confidence": confidence
            }
            
            # Add additional components if they exist
            if decision_status == "conditional":
                format_kwargs["next_steps"] = additional_components.get("next_steps", "Contact customer service for guidance")
            elif decision_status == "unclear":
                format_kwargs["missing_info"] = additional_components.get("missing_info", "Complete medical documentation")
                format_kwargs["recommendations"] = additional_components.get("recommendations", "Contact customer service for assistance")
            
            explanation_text = template["template"].format(**format_kwargs)
            
            # Add risk and complexity information
            risk_info = self._generate_risk_information(reasoning_result, consistency_validation)
            complexity_info = self._generate_complexity_information(query_context, reasoning_result)
            
            if risk_info:
                explanation_text += f"\n\n{risk_info}"
            if complexity_info:
                explanation_text += f"\n\n{complexity_info}"
            
            return {
                "explanation_text": explanation_text,
                "decision_summary": self._generate_decision_summary(decision, parsed),
                "key_factors": self._extract_key_factors(reasoning_result),
                "evidence_summary": self._generate_evidence_summary(reasoning_result),
                "confidence_breakdown": self._generate_confidence_breakdown(decision, consistency_validation),
                "next_actions": self._generate_next_actions(decision, parsed),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "template_used": decision_status,
                    "explanation_length": len(explanation_text)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return {
                "explanation_text": f"Error generating explanation: {str(e)}",
                "error": str(e)
            }
    
    def _generate_factors(self, 
                         decision: Dict[str, Any], 
                         parsed: Dict[str, Any], 
                         reasoning_result: Dict[str, Any]) -> str:
        """Generate factors that influenced the decision"""
        try:
            factors = []
            
            # Age factor
            if parsed.get("age"):
                age = int(parsed["age"])
                if age < 18:
                    factors.append("• Pediatric patient - special coverage considerations apply")
                elif age > 65:
                    factors.append("• Geriatric patient - age-related coverage factors considered")
                else:
                    factors.append(f"• Age {age} - within standard coverage range")
            
            # Gender factor
            if parsed.get("gender"):
                gender = "Male" if parsed["gender"] == "M" else "Female"
                factors.append(f"• Gender: {gender} - standard coverage applies")
            
            # Procedure factor
            if parsed.get("procedure"):
                factors.append(f"• Procedure: {parsed['procedure']} - coverage verified")
            
            # Policy duration factor
            if parsed.get("policy_duration"):
                factors.append(f"• Policy duration: {parsed['policy_duration']} - eligibility confirmed")
            
            # Medical condition factor
            if parsed.get("medical_condition"):
                factors.append(f"• Medical condition: {parsed['medical_condition']} - reviewed for coverage")
            
            # Urgency factor
            if parsed.get("urgency") == "high":
                factors.append("• Urgent case - expedited processing applied")
            
            # Add reasoning chain factors
            if reasoning_result.get("reasoning_chains"):
                for chain_name, chain_result in reasoning_result["reasoning_chains"].items():
                    decision_status = chain_result.get("chain_decision", {}).get("status", "unknown")
                    factors.append(f"• {chain_name.replace('_', ' ').title()}: {decision_status}")
            
            return "\n".join(factors) if factors else "• Standard policy review completed"
            
        except Exception as e:
            logger.error(f"Failed to generate factors: {e}")
            return "• Standard policy review completed"
    
    def _generate_evidence(self, 
                          reasoning_result: Dict[str, Any], 
                          consistency_validation: Dict[str, Any] = None) -> str:
        """Generate evidence summary"""
        try:
            evidence_items = []
            
            # Add reasoning evidence
            if reasoning_result.get("reasoning_chains"):
                for chain_name, chain_result in reasoning_result["reasoning_chains"].items():
                    decision = chain_result.get("chain_decision", {})
                    reason = decision.get("reason", "No specific reason provided")
                    evidence_items.append(f"• {chain_name.replace('_', ' ').title()}: {reason}")
            
            # Add consistency evidence
            if consistency_validation:
                if consistency_validation.get("is_consistent", True):
                    evidence_items.append("• Decision consistency: Validated against historical patterns")
                else:
                    warnings = consistency_validation.get("warnings", [])
                    for warning in warnings[:3]:  # Limit to 3 warnings
                        evidence_items.append(f"• Consistency note: {warning}")
            
            return "\n".join(evidence_items) if evidence_items else "• Policy terms and conditions reviewed"
            
        except Exception as e:
            logger.error(f"Failed to generate evidence: {e}")
            return "• Policy terms and conditions reviewed"
    
    def _generate_next_steps(self, decision: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        """Generate next steps for conditional approvals"""
        try:
            steps = []
            
            # Standard next steps
            steps.append("• Submit complete medical documentation")
            steps.append("• Provide detailed procedure information")
            steps.append("• Include supporting medical reports")
            
            # Procedure-specific steps
            procedure = parsed.get("procedure", "").lower()
            if "surgery" in procedure:
                steps.append("• Obtain pre-authorization from insurance provider")
                steps.append("• Submit surgeon's recommendation")
            
            if "heart" in procedure or "cardiac" in procedure:
                steps.append("• Provide cardiologist's evaluation")
                steps.append("• Submit cardiac test results")
            
            if "cosmetic" in procedure:
                steps.append("• Provide medical necessity documentation")
                steps.append("• Submit detailed cost breakdown")
            
            return "\n".join(steps)
            
        except Exception as e:
            logger.error(f"Failed to generate next steps: {e}")
            return "• Contact customer service for guidance"
    
    def _generate_missing_info(self, parsed: Dict[str, Any]) -> str:
        """Generate missing information list"""
        try:
            missing = []
            
            if not parsed.get("age"):
                missing.append("• Patient age")
            
            if not parsed.get("procedure"):
                missing.append("• Specific procedure details")
            
            if not parsed.get("policy_duration"):
                missing.append("• Policy duration information")
            
            if not parsed.get("location"):
                missing.append("• Treatment location")
            
            # Always include standard items
            missing.extend([
                "• Complete medical documentation",
                "• Supporting medical reports",
                "• Detailed cost breakdown"
            ])
            
            return "\n".join(missing)
            
        except Exception as e:
            logger.error(f"Failed to generate missing info: {e}")
            return "• Complete medical documentation\n• Supporting medical reports"
    
    def _generate_recommendations(self, decision: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        """Generate recommendations for unclear cases"""
        try:
            recommendations = [
                "• Provide complete medical documentation",
                "• Include detailed procedure information",
                "• Submit supporting medical reports",
                "• Contact customer service for assistance"
            ]
            
            # Add specific recommendations based on what's missing
            if not parsed.get("age"):
                recommendations.append("• Specify patient age")
            
            if not parsed.get("procedure"):
                recommendations.append("• Provide specific procedure details")
            
            return "\n".join(recommendations)
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return "• Contact customer service for guidance"
    
    def _generate_risk_information(self, 
                                 reasoning_result: Dict[str, Any], 
                                 consistency_validation: Dict[str, Any] = None) -> str:
        """Generate risk factor information"""
        try:
            risk_level = "low"
            
            # Determine risk level based on reasoning
            if reasoning_result.get("reasoning_chains"):
                for chain_name, chain_result in reasoning_result["reasoning_chains"].items():
                    if chain_name == "medical_complexity":
                        complexity = chain_result.get("chain_decision", {}).get("status", "unknown")
                        if complexity in ["complex", "high"]:
                            risk_level = "high"
                        elif complexity == "medium":
                            risk_level = "medium"
            
            # Check consistency validation
            if consistency_validation and not consistency_validation.get("is_consistent", True):
                if len(consistency_validation.get("warnings", [])) > 2:
                    risk_level = "high"
                elif len(consistency_validation.get("warnings", [])) > 0:
                    risk_level = "medium"
            
            return self.explanation_components["risk_factors"].get(risk_level, "")
            
        except Exception as e:
            logger.error(f"Failed to generate risk information: {e}")
            return ""
    
    def _generate_complexity_information(self, 
                                       query_context: Dict[str, Any], 
                                       reasoning_result: Dict[str, Any]) -> str:
        """Generate complexity level information"""
        try:
            complexity_level = "medium"
            
            # Determine complexity based on query context
            parsed = query_context.get("parsed_entities", {})
            
            # Check for complex factors
            complex_factors = 0
            if parsed.get("medical_condition"):
                complex_factors += 1
            if parsed.get("urgency") == "high":
                complex_factors += 1
            if parsed.get("coverage_type") == "premium":
                complex_factors += 1
            
            if complex_factors >= 2:
                complexity_level = "high"
            elif complex_factors == 0:
                complexity_level = "low"
            
            return self.explanation_components["complexity_levels"].get(complexity_level, "")
            
        except Exception as e:
            logger.error(f"Failed to generate complexity information: {e}")
            return ""
    
    def _generate_decision_summary(self, decision: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        """Generate a concise decision summary"""
        try:
            status = decision.get("status", "unknown").upper()
            amount = decision.get("amount", "N/A")
            procedure = parsed.get("procedure", "the procedure")
            
            return f"Decision: {status} | Amount: {amount} | Procedure: {procedure}"
            
        except Exception as e:
            logger.error(f"Failed to generate decision summary: {e}")
            return "Decision summary unavailable"
    
    def _extract_key_factors(self, reasoning_result: Dict[str, Any]) -> List[str]:
        """Extract key factors from reasoning result"""
        try:
            factors = []
            
            if reasoning_result.get("reasoning_chains"):
                for chain_name, chain_result in reasoning_result["reasoning_chains"].items():
                    decision = chain_result.get("chain_decision", {})
                    reason = decision.get("reason", "")
                    if reason:
                        factors.append(f"{chain_name.replace('_', ' ').title()}: {reason}")
            
            return factors
            
        except Exception as e:
            logger.error(f"Failed to extract key factors: {e}")
            return []
    
    def _generate_evidence_summary(self, reasoning_result: Dict[str, Any]) -> str:
        """Generate evidence summary"""
        try:
            evidence_count = 0
            if reasoning_result.get("reasoning_chains"):
                evidence_count = len(reasoning_result["reasoning_chains"])
            
            return f"Evidence reviewed: {evidence_count} reasoning chains analyzed"
            
        except Exception as e:
            logger.error(f"Failed to generate evidence summary: {e}")
            return "Evidence summary unavailable"
    
    def _generate_confidence_breakdown(self, 
                                     decision: Dict[str, Any], 
                                     consistency_validation: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate confidence breakdown"""
        try:
            confidence = decision.get("confidence", 0.0)
            
            breakdown = {
                "overall_confidence": confidence,
                "decision_confidence": confidence,
                "consistency_confidence": 1.0
            }
            
            if consistency_validation:
                breakdown["consistency_confidence"] = consistency_validation.get("confidence_score", 1.0)
                breakdown["overall_confidence"] = (confidence + breakdown["consistency_confidence"]) / 2
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Failed to generate confidence breakdown: {e}")
            return {"overall_confidence": 0.0}
    
    def _generate_next_actions(self, decision: Dict[str, Any], parsed: Dict[str, Any]) -> List[str]:
        """Generate next actions for the user"""
        try:
            actions = []
            
            status = decision.get("status", "unknown").lower()
            
            if status == "approved":
                actions.extend([
                    "Submit claim for processing",
                    "Provide supporting documentation",
                    "Follow up on payment timeline"
                ])
            elif status == "rejected":
                actions.extend([
                    "Review rejection reasons",
                    "Contact customer service",
                    "Consider appeal process"
                ])
            elif status == "conditional":
                actions.extend([
                    "Provide requested documentation",
                    "Complete additional forms",
                    "Follow up on conditions"
                ])
            else:  # unclear
                actions.extend([
                    "Provide additional information",
                    "Contact customer service",
                    "Submit complete documentation"
                ])
            
            return actions
            
        except Exception as e:
            logger.error(f"Failed to generate next actions: {e}")
            return ["Contact customer service for assistance"] 