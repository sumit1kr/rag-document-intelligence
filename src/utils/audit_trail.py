import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.api.setup_api import logger

# -----------------------------
# Audit Trail System
# -----------------------------
class AuditTrail:
    """Comprehensive audit trail system for tracking decisions and activities"""
    
    def __init__(self):
        self.audit_log = []
        self.session_trails = {}
        self.decision_history = []
        self.activity_log = []
        
        # Audit configuration
        self.audit_config = {
            "retention_days": 365,
            "max_log_size": 10000,
            "sensitive_fields": ["api_keys", "passwords", "personal_data"],
            "required_fields": ["timestamp", "action", "user_id", "session_id"]
        }
        
        logger.info("Audit Trail system initialized")
    
    def log_decision(self, 
                    session_id: str,
                    user_id: str,
                    query: str,
                    decision: Dict[str, Any],
                    query_context: Dict[str, Any],
                    reasoning_result: Dict[str, Any],
                    consistency_validation: Dict[str, Any] = None) -> str:
        """Log a complete decision with all context - SAFE VERSION"""
        try:
            audit_id = str(uuid.uuid4())
            
            # Create safe versions of complex objects to prevent recursion
            safe_decision = self._create_safe_dict(decision)
            safe_query_context = self._create_safe_dict(query_context)
            safe_reasoning_result = self._create_safe_dict(reasoning_result)
            safe_consistency_validation = self._create_safe_dict(consistency_validation) if consistency_validation else None
            
            audit_entry = {
                "audit_id": audit_id,
                "timestamp": datetime.now().isoformat(),
                "action": "decision_made",
                "user_id": user_id,
                "session_id": session_id,
                "query": query,
                "decision": safe_decision,
                "query_context": safe_query_context,
                "reasoning_result": safe_reasoning_result,
                "consistency_validation": safe_consistency_validation,
                "metadata": {
                    "decision_id": f"dec_{audit_id[:8]}",
                    "processing_time": self._calculate_processing_time(),
                    "system_version": "1.0.0"
                }
            }
            
            # Add to audit log
            self.audit_log.append(audit_entry)
            
            # Add to decision history - SAFE VERSION
            safe_decision_history_entry = {
                "audit_id": audit_id,
                "timestamp": audit_entry["timestamp"],
                "decision": safe_decision.get("status", "unknown"),
                "amount": safe_decision.get("amount", "N/A"),
                "confidence": safe_decision.get("confidence", 0.0),
                "query_summary": self._create_query_summary(safe_query_context)
            }
            self.decision_history.append(safe_decision_history_entry)
            
            # Add to session trail
            if session_id not in self.session_trails:
                self.session_trails[session_id] = []
            self.session_trails[session_id].append(audit_entry)
            
            # Cleanup old entries
            self._cleanup_old_entries()
            
            logger.info(f"Decision logged with audit ID: {audit_id}")
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")
            return None
    
    def log_activity(self, 
                    session_id: str,
                    user_id: str,
                    action: str,
                    details: Dict[str, Any] = None) -> str:
        """Log general system activity - SAFE VERSION"""
        try:
            audit_id = str(uuid.uuid4())
            
            # Create safe version of details
            safe_details = self._create_safe_dict(details or {})
            
            activity_entry = {
                "audit_id": audit_id,
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "user_id": user_id,
                "session_id": session_id,
                "details": safe_details,
                "metadata": {
                    "activity_id": f"act_{audit_id[:8]}",
                    "system_version": "1.0.0"
                }
            }
            
            # Add to activity log
            self.activity_log.append(activity_entry)
            
            # Add to session trail
            if session_id not in self.session_trails:
                self.session_trails[session_id] = []
            self.session_trails[session_id].append(activity_entry)
            
            # Cleanup old entries
            self._cleanup_old_entries()
            
            logger.info(f"Activity logged: {action} with audit ID: {audit_id}")
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return None
    
    def log_error(self, 
                 session_id: str,
                 user_id: str,
                 error_type: str,
                 error_message: str,
                 context: Dict[str, Any] = None) -> str:
        """Log system errors - SAFE VERSION"""
        try:
            audit_id = str(uuid.uuid4())
            
            # Create safe version of context
            safe_context = self._create_safe_dict(context or {})
            
            error_entry = {
                "audit_id": audit_id,
                "timestamp": datetime.now().isoformat(),
                "action": "error_occurred",
                "user_id": user_id,
                "session_id": session_id,
                "error_type": error_type,
                "error_message": error_message,
                "context": safe_context,
                "metadata": {
                    "error_id": f"err_{audit_id[:8]}",
                    "system_version": "1.0.0"
                }
            }
            
            # Add to activity log
            self.activity_log.append(error_entry)
            
            # Add to session trail
            if session_id not in self.session_trails:
                self.session_trails[session_id] = []
            self.session_trails[session_id].append(error_entry)
            
            # Cleanup old entries
            self._cleanup_old_entries()
            
            logger.error(f"Error logged: {error_type} - {error_message} with audit ID: {audit_id}")
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
            return None
    
    def get_audit_trail(self, 
                        session_id: str = None,
                        user_id: str = None,
                        start_date: datetime = None,
                        end_date: datetime = None,
                        action_type: str = None) -> List[Dict[str, Any]]:
        """Retrieve audit trail with filtering options"""
        try:
            filtered_trail = []
            
            # Determine which log to search
            search_log = self.audit_log
            
            for entry in search_log:
                try:
                    # Create a safe copy of the entry to prevent recursion
                    safe_entry = {}
                    
                    # Copy only simple fields
                    for key, value in entry.items():
                        if isinstance(value, (str, int, float, bool, type(None))):
                            safe_entry[key] = value
                        elif isinstance(value, dict):
                            # For dicts, only copy simple values
                            safe_dict = {}
                            for k, v in value.items():
                                if isinstance(v, (str, int, float, bool, type(None))):
                                    safe_dict[k] = v
                                else:
                                    safe_dict[k] = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
                            safe_entry[key] = safe_dict
                        elif isinstance(value, list):
                            # For lists, only copy simple values
                            safe_list = []
                            for item in value:
                                if isinstance(item, (str, int, float, bool, type(None))):
                                    safe_list.append(item)
                                else:
                                    safe_list.append(str(item)[:100] + "..." if len(str(item)) > 100 else str(item))
                            safe_entry[key] = safe_list
                        else:
                            # For any other type, convert to string
                            safe_entry[key] = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    
                    # Apply filters
                    if session_id and safe_entry.get("session_id") != session_id:
                        continue
                        
                    if user_id and safe_entry.get("user_id") != user_id:
                        continue
                        
                    if action_type and safe_entry.get("action") != action_type:
                        continue
                        
                    # Date filtering
                    if start_date or end_date:
                        try:
                            entry_timestamp = datetime.fromisoformat(safe_entry["timestamp"])
                            
                            if start_date and entry_timestamp < start_date:
                                continue
                                
                            if end_date and entry_timestamp > end_date:
                                continue
                        except:
                            # If timestamp parsing fails, skip this entry
                            continue
                    
                    filtered_trail.append(safe_entry)
                    
                except Exception as e:
                    # If processing an entry fails, skip it and continue
                    logger.error(f"Error processing audit entry: {e}")
                    continue
            
            return filtered_trail
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {e}")
            return []
    
    def get_decision_history(self, 
                           session_id: str = None,
                           user_id: str = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve decision history with filtering"""
        try:
            filtered_history = []
            
            for decision in self.decision_history:
                try:
                    # Create a safe copy of the decision to prevent recursion
                    safe_decision = {}
                    
                    # Copy only simple fields
                    for key, value in decision.items():
                        if isinstance(value, (str, int, float, bool, type(None))):
                            safe_decision[key] = value
                        elif isinstance(value, dict):
                            # For dicts, only copy simple values
                            safe_dict = {}
                            for k, v in value.items():
                                if isinstance(v, (str, int, float, bool, type(None))):
                                    safe_dict[k] = v
                                else:
                                    safe_dict[k] = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
                            safe_decision[key] = safe_dict
                        elif isinstance(value, list):
                            # For lists, only copy simple values
                            safe_list = []
                            for item in value:
                                if isinstance(item, (str, int, float, bool, type(None))):
                                    safe_list.append(item)
                                else:
                                    safe_list.append(str(item)[:100] + "..." if len(str(item)) > 100 else str(item))
                            safe_decision[key] = safe_list
                        else:
                            # For any other type, convert to string
                            safe_decision[key] = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    
                    # Apply filters
                    if session_id and safe_decision.get("session_id") != session_id:
                        continue
                        
                    if user_id and safe_decision.get("user_id") != user_id:
                        continue
                    
                    filtered_history.append(safe_decision)
                    
                    # Apply limit
                    if len(filtered_history) >= limit:
                        break
                        
                except Exception as e:
                    # If processing a decision fails, skip it and continue
                    logger.error(f"Error processing decision entry: {e}")
                    continue
            
            return filtered_history
            
        except Exception as e:
            logger.error(f"Failed to retrieve decision history: {e}")
            return []
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of a session"""
        try:
            if session_id not in self.session_trails:
                return {"error": "Session not found"}
            
            session_entries = self.session_trails[session_id]
            
            # Calculate session statistics
            decisions_made = sum(1 for entry in session_entries if entry.get("action") == "decision_made")
            errors_occurred = sum(1 for entry in session_entries if entry.get("action") == "error_occurred")
            
            # Get decision breakdown
            decision_breakdown = {}
            for entry in session_entries:
                if entry.get("action") == "decision_made":
                    decision_status = entry.get("decision", {}).get("status", "unknown")
                    decision_breakdown[decision_status] = decision_breakdown.get(decision_status, 0) + 1
            
            # Calculate session duration
            if session_entries:
                first_entry = min(session_entries, key=lambda x: x["timestamp"])
                last_entry = max(session_entries, key=lambda x: x["timestamp"])
                
                start_time = datetime.fromisoformat(first_entry["timestamp"])
                end_time = datetime.fromisoformat(last_entry["timestamp"])
                duration = end_time - start_time
            else:
                duration = timedelta(0)
            
            return {
                "session_id": session_id,
                "total_entries": len(session_entries),
                "decisions_made": decisions_made,
                "errors_occurred": errors_occurred,
                "decision_breakdown": decision_breakdown,
                "session_duration": str(duration),
                "first_activity": session_entries[0]["timestamp"] if session_entries else None,
                "last_activity": session_entries[-1]["timestamp"] if session_entries else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get session summary: {e}")
            return {"error": str(e)}
    
    def export_audit_report(self, 
                           start_date: datetime = None,
                           end_date: datetime = None,
                           format: str = "json") -> str:
        """Export audit report in specified format"""
        try:
            # Get filtered audit trail
            audit_trail = self.get_audit_trail(start_date=start_date, end_date=end_date)
            
            # Create report structure
            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "total_entries": len(audit_trail),
                    "format": format
                },
                "summary": {
                    "total_decisions": sum(1 for entry in audit_trail if entry.get("action") == "decision_made"),
                    "total_errors": sum(1 for entry in audit_trail if entry.get("action") == "error_occurred"),
                    "unique_users": len(set(entry.get("user_id") for entry in audit_trail)),
                    "unique_sessions": len(set(entry.get("session_id") for entry in audit_trail))
                },
                "audit_trail": audit_trail
            }
            
            if format.lower() == "json":
                return json.dumps(report, indent=2)
            elif format.lower() == "csv":
                return self._convert_to_csv(report)
            else:
                return json.dumps(report, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to export audit report: {e}")
            return f"Error generating report: {str(e)}"
    
    def _create_safe_dict(self, data: Any) -> Dict[str, Any]:
        """Create a safe dictionary from complex objects to prevent recursion"""
        if data is None:
            return {}
        
        if isinstance(data, dict):
            safe_dict = {}
            for key, value in data.items():
                if key.lower() in self.audit_config["sensitive_fields"]:
                    safe_dict[key] = "[REDACTED]"
                elif isinstance(value, (str, int, float, bool, type(None))):
                    safe_dict[key] = value
                elif isinstance(value, dict):
                    # Recursively process nested dicts but with limits
                    safe_dict[key] = self._create_safe_dict(value)
                elif isinstance(value, list):
                    # Process lists safely
                    safe_list = []
                    for item in value:
                        if isinstance(item, (str, int, float, bool, type(None))):
                            safe_list.append(item)
                        elif isinstance(item, dict):
                            safe_list.append(self._create_safe_dict(item))
                        else:
                            safe_list.append(str(item)[:100] + "..." if len(str(item)) > 100 else str(item))
                    safe_dict[key] = safe_list
                else:
                    # Convert any other type to string
                    safe_dict[key] = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            return safe_dict
        
        elif isinstance(data, list):
            safe_list = []
            for item in data:
                if isinstance(item, (str, int, float, bool, type(None))):
                    safe_list.append(item)
                elif isinstance(item, dict):
                    safe_list.append(self._create_safe_dict(item))
                else:
                    safe_list.append(str(item)[:100] + "..." if len(str(item)) > 100 else str(item))
            return safe_list
        
        else:
            # For any other type, return as string
            return str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
    
    def _create_query_summary(self, query_context: Dict[str, Any]) -> str:
        """Create a summary of the query context"""
        try:
            parsed = query_context.get("parsed_entities", {})
            summary_parts = []
            
            if parsed.get("age"):
                summary_parts.append(f"Age: {parsed['age']}")
            if parsed.get("gender"):
                summary_parts.append(f"Gender: {parsed['gender']}")
            if parsed.get("procedure"):
                summary_parts.append(f"Procedure: {parsed['procedure']}")
            if parsed.get("location"):
                summary_parts.append(f"Location: {parsed['location']}")
            
            return " | ".join(summary_parts) if summary_parts else "No details available"
            
        except Exception as e:
            logger.error(f"Failed to create query summary: {e}")
            return "Summary unavailable"
    
    def _calculate_processing_time(self) -> float:
        """Calculate processing time (placeholder for now)"""
        # In a real implementation, this would track actual processing time
        return 0.5  # Placeholder value
    
    def _cleanup_old_entries(self):
        """Remove old audit entries based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.audit_config["retention_days"])
            
            # Cleanup audit log
            self.audit_log = [
                entry for entry in self.audit_log
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
            ]
            
            # Cleanup decision history
            self.decision_history = [
                entry for entry in self.decision_history
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
            ]
            
            # Cleanup activity log
            self.activity_log = [
                entry for entry in self.activity_log
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
            ]
            
            # Cleanup session trails
            for session_id in list(self.session_trails.keys()):
                self.session_trails[session_id] = [
                    entry for entry in self.session_trails[session_id]
                    if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
                ]
                
                # Remove empty sessions
                if not self.session_trails[session_id]:
                    del self.session_trails[session_id]
            
            # Limit log size
            if len(self.audit_log) > self.audit_config["max_log_size"]:
                self.audit_log = self.audit_log[-self.audit_config["max_log_size"]:]
            
        except Exception as e:
            logger.error(f"Failed to cleanup old entries: {e}")
    
    def _convert_to_csv(self, report: Dict[str, Any]) -> str:
        """Convert audit report to CSV format"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Timestamp", "Action", "User ID", "Session ID", 
                "Decision Status", "Amount", "Confidence", "Query Summary"
            ])
            
            # Write data
            for entry in report["audit_trail"]:
                if entry.get("action") == "decision_made":
                    decision = entry.get("decision", {})
                    writer.writerow([
                        entry.get("timestamp", ""),
                        entry.get("action", ""),
                        entry.get("user_id", ""),
                        entry.get("session_id", ""),
                        decision.get("status", ""),
                        decision.get("amount", ""),
                        decision.get("confidence", ""),
                        entry.get("query", "")[:100]  # Truncate long queries
                    ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to convert to CSV: {e}")
            return f"Error converting to CSV: {str(e)}" 