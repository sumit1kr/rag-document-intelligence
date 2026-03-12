import traceback
import uuid
import json
import pandas as pd
from datetime import datetime, timedelta
from src.api.setup_api import APIKeyManager, logger
from src.utils.file_processing import FileProcessor
from src.core.text_processing import TextProcessor
from src.utils.app_state import app_state
import gradio as gr
import json

# -----------------------------
# Fixed Interface Functions with Real Backend Integration
# -----------------------------

def get_real_audit_trail(start_date, end_date, decision_type):
    """Get real audit trail with proper filtering"""
    try:
        if not hasattr(app_state, 'qa_chain') or not hasattr(app_state.qa_chain, 'audit_trail'):
            return pd.DataFrame(columns=["Timestamp", "Action", "Decision", "Amount", "Query"])
        
        # Convert dates if provided
        start_dt = None
        end_dt = None
        
        if start_date and start_date.strip():
            try:
                start_dt = datetime.fromisoformat(start_date)
            except:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        
        if end_date and end_date.strip():
            try:
                end_dt = datetime.fromisoformat(end_date)
            except:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get real audit trail
        trail = app_state.qa_chain.audit_trail.get_audit_trail(
            session_id=app_state.session_id,
            start_date=start_dt,
            end_date=end_dt,
            action_type=decision_type if decision_type != "All" else None
        )
        
        # Convert to DataFrame for display
        if trail:
            df_data = []
            for entry in trail:
                decision_data = entry.get("decision", {})
                df_data.append({
                    "Timestamp": entry.get("timestamp", ""),
                    "Action": entry.get("action", ""),
                    "Decision": decision_data.get("status", ""),
                    "Amount": decision_data.get("amount", ""),
                    "Query": entry.get("query", "")[:50] + "..." if len(entry.get("query", "")) > 50 else entry.get("query", "")
                })
            return pd.DataFrame(df_data)
        else:
            return pd.DataFrame(columns=["Timestamp", "Action", "Decision", "Amount", "Query"])
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        return pd.DataFrame(columns=["Timestamp", "Action", "Decision", "Amount", "Query"])

def get_real_cache_statistics():
    """Get real cache statistics"""
    try:
        if hasattr(app_state, 'cache_manager') and app_state.cache_manager:
            stats = app_state.cache_manager.get_cache_statistics()
            return json.dumps(stats, indent=2)
        else:
            # Initialize cache manager if not available
            from src.utils.cache_manager import CacheManager
            app_state.cache_manager = CacheManager()
            stats = app_state.cache_manager.get_cache_statistics()
            return json.dumps(stats, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

def get_real_performance_metrics():
    """Get real system performance metrics"""
    try:
        # Get real metrics from backend components
        cache_stats = {}
        if hasattr(app_state, 'cache_manager') and app_state.cache_manager:
            cache_stats = app_state.cache_manager.get_cache_statistics()
        
        audit_stats = {}
        if hasattr(app_state, 'qa_chain') and hasattr(app_state.qa_chain, 'audit_trail'):
            audit_stats = {
                "total_decisions": len(app_state.qa_chain.audit_trail.decision_history),
                "total_activities": len(app_state.qa_chain.audit_trail.activity_log)
            }
        
        metrics = {
            "session_id": app_state.session_id,
            "user_id": f"user_{app_state.session_id[:8]}",
            "documents_indexed": app_state.documents_indexed,
            "session_start_time": datetime.now().isoformat(),
            "cache_hit_rate": cache_stats.get("hit_rate", "0%"),
            "total_cache_entries": cache_stats.get("total_cache_entries", 0),
            "total_decisions": audit_stats.get("total_decisions", 0),
            "total_activities": audit_stats.get("total_activities", 0),
            "system_status": "Healthy",
            "vector_store_status": "Connected" if app_state.vector_store else "Not Connected",
            "qa_chain_status": "Ready" if app_state.qa_chain else "Not Ready"
        }
        return json.dumps(metrics, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

def get_real_query_validation(query):
    """Get real query validation results"""
    try:
        if not query:
            return "Please enter a query to validate."
        
        # Use the actual query processor
        if hasattr(app_state, 'qa_chain') and hasattr(app_state.qa_chain, 'query_processor'):
            validation_result = app_state.qa_chain.query_processor.process_query(query)
            
            # Format validation result
            validation = {
                "query": query,
                "is_valid": validation_result.get('validation', {}).get('is_valid', True),
                "entities_found": validation_result.get('parsed_entities', {}),
                "confidence_score": validation_result.get('processing_metadata', {}).get('confidence_score', 0.0),
                "suggestions": validation_result.get('validation', {}).get('suggestions', []),
                "warnings": validation_result.get('validation', {}).get('warnings', []),
                "errors": validation_result.get('validation', {}).get('errors', [])
            }
            
            return json.dumps(validation, indent=2)
        else:
            return "❌ Query processor not available."
    except Exception as e:
        return f"❌ Validation failed: {str(e)}"

def get_real_query_history():
    """Get real query history"""
    try:
        if hasattr(app_state, 'qa_chain') and hasattr(app_state.qa_chain, 'memory'):
            history = app_state.qa_chain.memory.get_history(app_state.session_id)
            
            # Convert to DataFrame format
            df_data = []
            for entry in history:
                if entry.get('role') == 'human':
                    df_data.append({
                        "Timestamp": entry.get('timestamp', datetime.now().isoformat()),
                        "Query": entry.get('content', ''),
                        "Decision": "N/A",  # Would need to cross-reference with audit trail
                        "Status": "Processed"
                    })
            
            return pd.DataFrame(df_data)
        else:
            return pd.DataFrame(columns=["Timestamp", "Query", "Decision", "Status"])
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        return pd.DataFrame(columns=["Timestamp", "Query", "Decision", "Status"])

def export_real_user_data(user_id):
    """Export real user data for GDPR compliance"""
    try:
        if not user_id:
            return "❌ Please provide a user ID."
        
        # Get real data from audit trail
        export_data = {
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "session_data": [],
            "query_history": [],
            "decisions": []
        }
        
        if hasattr(app_state, 'qa_chain') and hasattr(app_state.qa_chain, 'audit_trail'):
            audit_trail = app_state.qa_chain.audit_trail
            
            # Get session data
            if app_state.session_id in audit_trail.session_trails:
                export_data["session_data"] = audit_trail.session_trails[app_state.session_id]
            
            # Get decision history
            export_data["decisions"] = audit_trail.get_decision_history(
                session_id=app_state.session_id,
                user_id=user_id
            )
            
            # Get query history from memory
            if hasattr(app_state.qa_chain, 'memory'):
                query_history = app_state.qa_chain.memory.get_history(app_state.session_id)
                export_data["query_history"] = query_history
        
        return json.dumps(export_data, indent=2)
    except Exception as e:
        return f"❌ Failed to export data: {str(e)}"

def process_real_batch_queries(batch_text):
    """Process multiple queries at once with real backend and progress"""
    try:
        if not app_state.documents_indexed:
            return "Please upload and index documents first."
        
        queries = [q.strip() for q in batch_text.split('\n') if q.strip()]
        if not queries:
            return "No valid queries provided."
        
        results = []
        retriever = app_state.vector_store.get_retriever(app_state.session_id)
        
        # Process each query with real backend
        for i, query in enumerate(queries):
            try:
                result = app_state.qa_chain.run(query, retriever, app_state.session_id)
                results.append({
                    "Query": query,
                    "Decision": result.get('decision', 'Unknown'),
                    "Amount": result.get('amount', 'N/A'),
                    "Confidence": f"{result.get('confidence', 0.0):.2f}",
                    "Status": "Success"
                })
            except Exception as e:
                results.append({
                    "Query": query,
                    "Decision": "Error",
                    "Amount": "N/A",
                    "Confidence": "0.00",
                    "Status": f"Error: {str(e)}"
                })
        
        # Convert to DataFrame for display
        df = pd.DataFrame(results)
        return df.to_html(index=False, classes='table table-striped')
        
    except Exception as e:
        return f"Batch processing failed: {str(e)}"

def get_real_session_info():
    """Get real session information"""
    try:
        session_info = {
            "session_id": app_state.session_id,
            "user_id": f"user_{app_state.session_id[:8]}",
            "documents_indexed": app_state.documents_indexed,
            "session_start_time": datetime.now().isoformat(),
            "status": "Active",
            "vector_store_status": "Connected" if app_state.vector_store else "Not Connected",
            "qa_chain_status": "Ready" if app_state.qa_chain else "Not Ready",
            "audit_trail_available": hasattr(app_state.qa_chain, 'audit_trail') if app_state.qa_chain else False,
            "cache_manager_available": hasattr(app_state, 'cache_manager') and app_state.cache_manager is not None
        }
        return json.dumps(session_info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

# Export the fixed functions
__all__ = [
    'get_real_audit_trail',
    'get_real_cache_statistics', 
    'get_real_performance_metrics',
    'get_real_query_validation',
    'get_real_query_history',
    'export_real_user_data',
    'process_real_batch_queries',
    'get_real_session_info'
] 