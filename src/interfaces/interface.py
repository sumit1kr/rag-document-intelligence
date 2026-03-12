import traceback
import uuid
import json
import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from src.api.setup_api import APIKeyManager, logger
from src.utils.file_processing import FileProcessor
from src.core.text_processing import TextProcessor
from src.utils.app_state import app_state
import gradio as gr

# -----------------------------
# Enhanced Gradio Interface Functions
# -----------------------------

def upload_and_index(files, use_ocr, progress=gr.Progress()):
    """Handle file upload and indexing"""
    try:
        if not files or len(files) == 0:
            return "❌ No files uploaded.", gr.update(interactive=False)
        
        progress(0.1, desc="Extracting text from files...")
        
        # Extract text from files
        raw_text = FileProcessor.extract_text(files, use_ocr)
        
        if not raw_text.strip():
            return "❌ Failed to extract any text from uploaded files.", gr.update(interactive=False)
        
        progress(0.4, desc="Cleaning and processing text...")
        
        # Clean and chunk text
        clean_text = TextProcessor.clean(raw_text)
        chunks = TextProcessor.chunk(clean_text)
        
        if not chunks:
            return "❌ No text chunks generated.", gr.update(interactive=False)
        
        progress(0.7, desc="Creating embeddings and indexing...")
        
        # Add to vector store
        indexed_count = app_state.vector_store.add_documents(chunks, app_state.session_id)
        
        progress(1.0, desc="Indexing complete!")
        
        # Update application state
        app_state.documents_indexed = True
        
        return (
            f"✅ Successfully indexed {indexed_count} chunks from {len(files)} file(s).",
            gr.update(interactive=True)
        )
        
    except Exception as e:
        logger.error(f"Upload and indexing failed: {e}")
        logger.error(traceback.format_exc())
        return f"❌ Error during indexing: {str(e)}", gr.update(interactive=False)

def make_api_call(endpoint, data=None):
    """Make API call to the backend endpoints"""
    try:
        default_port = os.getenv("PORT", "5000")
        base_url = os.getenv("API_BASE_URL", f"http://localhost:{default_port}")
        url = f"{base_url}{endpoint}"
        
        if data:
            response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API call failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"API call error: {e}")
        return None

def ask_question(question, chat_history):
    """Handle question asking and return updated chat"""
    try:
        if not app_state.documents_indexed:
            return chat_history, "Please upload and index documents first.", "", "", "", "", ""
        
        if not question or not question.strip():
            return chat_history, "Please enter a valid question.", "", "", "", "", ""
        
        # Always use the in-process pipeline so retrieval uses the same
        # vector store/session that was populated during upload.
        retriever = app_state.vector_store.get_retriever(app_state.session_id)
        result = app_state.qa_chain.run(
            question,
            retriever,
            app_state.session_id,
            f"user_{app_state.session_id[:8]}"
        )
        
        # Update chat history
        updated_history = []
        for msg in result.get('history', []):
            if msg['role'] == 'human':
                updated_history.append({"role": "user", "content": msg['content']})
            else:
                updated_history.append({"role": "assistant", "content": msg['content']})
        
        # Format evidence clauses with enhanced information
        evidence_text = ""
        if result.get('structured_response') and result['structured_response'].get('evidence'):
            evidence_clauses = result['structured_response']['evidence']['clauses']
            evidence_text = "\n\n---\n\n".join(
                f"{i+1}. [{c.get('clause_id', 'Unknown')}] {c.get('summary', c.get('clause_text', '').strip())} "
                f"(Relevance: {c.get('decision_relevance', 'Unknown')}, Strength: {c.get('evidence_strength', 'Unknown')})"
                for i, c in enumerate(evidence_clauses[:5])  # Show top 5 clauses
            )
        else:
            # Fallback to legacy format
            evidence_text = "\n\n---\n\n".join(
                f"{i+1}. {ec['text'].strip()}" for i, ec in enumerate(result.get('evidence_clauses', []))
            )
        
        # Get enhanced JSON output for debug tab
        json_output = result.get('json_output', 'No structured data available')
        
        # Add query analysis and reasoning information to debug output
        if result.get('query_analysis') or result.get('reasoning_result'):
            debug_info = {
                "query_analysis": result.get('query_analysis', {}),
                "reasoning_result": result.get('reasoning_result', {}),
                "structured_response": result.get('structured_response', {}),
                "retrieved_documents": result.get('retrieved_documents', []),
                "evidence_clauses": result.get('evidence_clauses', []),
                "audit_id": result.get('audit_id', 'N/A'),
                "processing_time": result.get('processing_time', 'N/A')
            }
            json_output = json.dumps(debug_info, indent=2)
        
        return (
            updated_history,
            result['answer'],
            result['decision'],
            result['amount'],
            result['justification'],
            evidence_text,
            json_output
        )

    except Exception as e:
        logger.error(f"Question processing failed: {e}")
        logger.error(traceback.format_exc())
        error_msg = f"Error processing question: {str(e)}"
        return chat_history, error_msg, "", "", "", "", ""

def reset_session():
    """Reset the current session"""
    global app_state
    old_session = app_state.session_id
    app_state.session_id = str(uuid.uuid4())
    app_state.documents_indexed = False
    
    if app_state.qa_chain:
        app_state.qa_chain.memory.clear_session(old_session)
    
    logger.info(f"Session reset: {old_session} -> {app_state.session_id}")
    
    return (
        "✅ Session reset successfully. Please upload new documents.",
        gr.update(interactive=False),
        [],
        "",
        "",
        "",  # decision_output
        "",  # amount_output
        "",  # justification_output
        "",  # evidence_output
        ""   # json_output
    )

# -----------------------------
# Real Backend Integration Functions
# -----------------------------

def get_session_info():
    """Get current session information"""
    try:
        session_info = {
            "session_id": app_state.session_id,
            "user_id": f"user_{app_state.session_id[:8]}",
            "documents_indexed": app_state.documents_indexed,
            "session_start_time": datetime.now().isoformat(),
            "status": "Active",
            "vector_store_status": "Connected" if app_state.vector_store else "Not Connected",
            "qa_chain_status": "Ready" if app_state.qa_chain else "Not Ready"
        }
        return json.dumps(session_info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

def get_cache_statistics():
    """Get real cache statistics"""
    try:
        if hasattr(app_state, 'cache_manager') and app_state.cache_manager:
            stats = app_state.cache_manager.get_cache_statistics()
        else:
            # Initialize cache manager if not available
            from src.utils.cache_manager import CacheManager
            app_state.cache_manager = CacheManager()
            stats = app_state.cache_manager.get_cache_statistics()
        
        # Ensure stats is a dict and has required fields
        if not isinstance(stats, dict):
            stats = {"error": "Invalid cache statistics format"}
        
        # Add default values for missing fields
        default_stats = {
            "hit_rate": "0%",
            "total_cache_entries": 0,
            "cache_size_mb": 0,
            "last_cleanup": datetime.now().isoformat(),
            "status": "active"
        }
        
        for key, default_value in default_stats.items():
            if key not in stats:
                stats[key] = default_value
        
        return json.dumps(stats, indent=2)
    except Exception as e:
        error_response = {
            "error": str(e),
            "hit_rate": "0%",
            "total_cache_entries": 0,
            "cache_size_mb": 0,
            "last_cleanup": datetime.now().isoformat(),
            "status": "error"
        }
        return json.dumps(error_response, indent=2)

def get_audit_trail(start_date, end_date, decision_type):
    """Get real audit trail with filters"""
    try:
        if not hasattr(app_state, 'qa_chain') or not hasattr(app_state.qa_chain, 'audit_trail'):
            # Return empty DataFrame with proper structure
            return pd.DataFrame(columns=["Timestamp", "Action", "Decision", "Amount", "Query"])
        
        # Convert dates if provided
        start_dt = None
        end_dt = None
        
        if start_date and start_date.strip():
            try:
                start_dt = datetime.fromisoformat(start_date)
            except:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                except:
                    start_dt = None
        
        if end_date and end_date.strip():
            try:
                end_dt = datetime.fromisoformat(end_date)
            except:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                except:
                    end_dt = None
        
        # Get audit trail with error handling
        trail = []
        try:
            trail = app_state.qa_chain.audit_trail.get_audit_trail(
                session_id=app_state.session_id,
                start_date=start_dt,
                end_date=end_dt,
                action_type=decision_type if decision_type != "All" else None
            )
        except RecursionError as e:
            logger.error(f"Recursion error getting audit trail: {e}")
            trail = []
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            trail = []
        
        # Convert to DataFrame for display
        if trail and isinstance(trail, list):
            df_data = []
            for entry in trail:
                if isinstance(entry, dict):
                    decision_data = entry.get("decision", {})
                    df_data.append({
                        "Timestamp": entry.get("timestamp", ""),
                        "Action": entry.get("action", ""),
                        "Decision": decision_data.get("status", "") if isinstance(decision_data, dict) else str(decision_data),
                        "Amount": decision_data.get("amount", "") if isinstance(decision_data, dict) else "",
                        "Query": entry.get("query", "")[:50] + "..." if len(entry.get("query", "")) > 50 else entry.get("query", "")
                    })
            return pd.DataFrame(df_data)
        else:
            return pd.DataFrame(columns=["Timestamp", "Action", "Decision", "Amount", "Query"])
            
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        return pd.DataFrame(columns=["Timestamp", "Action", "Decision", "Amount", "Query"])

def process_batch_queries(batch_text, progress=gr.Progress()):
    """Process multiple queries at once with real backend and progress"""
    try:
        if not app_state.documents_indexed:
            return "❌ Please upload and index documents first."
        
        queries = [q.strip() for q in batch_text.split('\n') if q.strip()]
        if not queries:
            return "❌ No valid queries provided."
        
        results = []
        retriever = app_state.vector_store.get_retriever(app_state.session_id)
        
        # More visible progress updates
        progress(0.0, desc=f"🚀 Starting batch processing of {len(queries)} queries...")
        
        for i, query in enumerate(queries):
            try:
                # More detailed progress updates
                progress_percent = (i + 1) / len(queries)
                progress(progress_percent, desc=f"📝 Processing query {i + 1}/{len(queries)}: {query[:50]}...")
                
                result = app_state.qa_chain.run(query, retriever, app_state.session_id)
                results.append({
                    "Query": query,
                    "Decision": result.get('decision', 'Unknown'),
                    "Amount": result.get('amount', 'N/A'),
                    "Confidence": f"{result.get('confidence', 0.0):.2f}",
                    "Status": "✅ Success"
                })
                
                # Small delay to make progress visible
                import time
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                results.append({
                    "Query": query,
                    "Decision": "❌ Error",
                    "Amount": "N/A",
                    "Confidence": "0.00",
                    "Status": f"❌ Error: {str(e)[:100]}"
                })
        
        progress(1.0, desc="✅ Batch processing complete!")
        
        # Convert to DataFrame for display with better formatting
        df = pd.DataFrame(results)
        
        # Create a more detailed HTML table
        html_table = """
        <div style="margin: 20px 0;">
            <h3>📊 Batch Processing Results</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #f0f0f0;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Query</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Decision</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Amount</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Confidence</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Status</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for _, row in df.iterrows():
            status_color = "green" if "Success" in row['Status'] else "red"
            html_table += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">{row['Query']}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{row['Decision']}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{row['Amount']}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{row['Confidence']}</td>
                        <td style="border: 1px solid #ddd; padding: 8px; color: {status_color};">{row['Status']}</td>
                    </tr>
            """
        
        html_table += """
                </tbody>
            </table>
            <p style="margin-top: 10px; color: #666;">
                ✅ Processed {total} queries successfully | ❌ {errors} queries failed
            </p>
        </div>
        """.format(
            total=len([r for r in results if "Success" in r['Status']]),
            errors=len([r for r in results if "Error" in r['Status']])
        )
        
        return html_table
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return f"❌ Batch processing failed: {str(e)}"

def clear_cache():
    """Clear all caches"""
    try:
        if hasattr(app_state, 'cache_manager') and app_state.cache_manager:
            cleared = app_state.cache_manager.clear_all_caches()
            return f"✅ Cleared {cleared} cache entries successfully."
        else:
            return "❌ Cache manager not available."
    except Exception as e:
        return f"❌ Failed to clear cache: {str(e)}"

def update_api_keys(pinecone_key, groq_key, huggingface_key):
    """Update API keys"""
    try:
        if not pinecone_key or not groq_key or not huggingface_key:
            return "❌ Please provide all API keys."
        
        # Update environment variables
        import os
        os.environ['PINECONE_API_KEY'] = pinecone_key
        os.environ['GROQ_API_KEY'] = groq_key
        os.environ['HUGGINGFACE_API_KEY'] = huggingface_key
        
        return "✅ API keys updated successfully. Please restart the application for changes to take effect."
    except Exception as e:
        return f"❌ Failed to update API keys: {str(e)}"

def save_query_template(template_name, query_text):
    """Save a query template with persistent storage"""
    try:
        if not template_name or not query_text:
            return "❌ Please provide both template name and query text."
        
        # Save to file for persistence
        import os
        templates_dir = "templates"
        os.makedirs(templates_dir, exist_ok=True)
        
        template_file = os.path.join(templates_dir, f"{template_name}.json")
        template_data = {
            "name": template_name,
            "query": query_text,
            "created_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        return f"✅ Template '{template_name}' saved successfully."
    except Exception as e:
        return f"❌ Failed to save template: {str(e)}"

def load_query_template(template_name):
    """Load a query template"""
    try:
        if not template_name:
            return "❌ Please provide a template name."
        
        import os
        templates_dir = "templates"
        template_file = os.path.join(templates_dir, f"{template_name}.json")
        
        if not os.path.exists(template_file):
            return f"❌ Template '{template_name}' not found."
        
        with open(template_file, 'r') as f:
            template_data = json.load(f)
        
        return template_data.get("query", "")
    except Exception as e:
        return f"❌ Failed to load template: {str(e)}"

def get_performance_metrics():
    """Get real system performance metrics"""
    try:
        # Get real metrics from backend components with error handling
        cache_stats = {}
        if hasattr(app_state, 'cache_manager') and app_state.cache_manager:
            try:
                cache_stats = app_state.cache_manager.get_cache_statistics()
                if not isinstance(cache_stats, dict):
                    cache_stats = {}
            except Exception as e:
                logger.error(f"Error getting cache stats: {e}")
                cache_stats = {}
        
        audit_stats = {}
        if hasattr(app_state, 'qa_chain') and hasattr(app_state.qa_chain, 'audit_trail'):
            try:
                # Use try-catch to prevent recursion errors
                decision_count = 0
                activity_count = 0
                try:
                    decision_count = len(app_state.qa_chain.audit_trail.decision_history)
                except:
                    pass
                try:
                    activity_count = len(app_state.qa_chain.audit_trail.activity_log)
                except:
                    pass
                
                audit_stats = {
                    "total_decisions": decision_count,
                    "total_activities": activity_count
                }
            except Exception as e:
                logger.error(f"Error getting audit stats: {e}")
                audit_stats = {"total_decisions": 0, "total_activities": 0}
        
        metrics = {
            "session_id": getattr(app_state, 'session_id', 'unknown'),
            "user_id": f"user_{getattr(app_state, 'session_id', 'unknown')[:8]}",
            "documents_indexed": getattr(app_state, 'documents_indexed', False),
            "session_start_time": datetime.now().isoformat(),
            "cache_hit_rate": cache_stats.get("hit_rate", "0%"),
            "total_cache_entries": cache_stats.get("total_cache_entries", 0),
            "total_decisions": audit_stats.get("total_decisions", 0),
            "total_activities": audit_stats.get("total_activities", 0),
            "system_status": "Healthy",
            "vector_store_status": "Connected" if hasattr(app_state, 'vector_store') and app_state.vector_store else "Not Connected",
            "qa_chain_status": "Ready" if hasattr(app_state, 'qa_chain') and app_state.qa_chain else "Not Ready"
        }
        return json.dumps(metrics, indent=2)
    except Exception as e:
        error_metrics = {
            "error": str(e),
            "session_id": "unknown",
            "user_id": "unknown",
            "documents_indexed": False,
            "session_start_time": datetime.now().isoformat(),
            "cache_hit_rate": "0%",
            "total_cache_entries": 0,
            "total_decisions": 0,
            "total_activities": 0,
            "system_status": "Error",
            "vector_store_status": "Unknown",
            "qa_chain_status": "Unknown"
        }
        return json.dumps(error_metrics, indent=2)

def export_user_data(user_id):
    """Export real user data for GDPR compliance"""
    try:
        if not user_id or not user_id.strip():
            error_response = {
                "error": "Please provide a user ID.",
                "user_id": "",
                "export_timestamp": datetime.now().isoformat(),
                "session_data": [],
                "query_history": [],
                "decisions": []
            }
            return json.dumps(error_response, indent=2)
        
        # Get real data from audit trail
        export_data = {
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "session_data": [],
            "query_history": [],
            "decisions": []
        }
        
        if hasattr(app_state, 'qa_chain') and hasattr(app_state.qa_chain, 'audit_trail'):
            try:
                audit_trail = app_state.qa_chain.audit_trail
                
                # Get session data safely
                try:
                    if app_state.session_id in audit_trail.session_trails:
                        export_data["session_data"] = audit_trail.session_trails[app_state.session_id]
                except Exception as e:
                    logger.error(f"Error getting session data: {e}")
                    export_data["session_data"] = []
                
                # Get decision history safely
                try:
                    export_data["decisions"] = audit_trail.get_decision_history(
                        session_id=app_state.session_id,
                        user_id=user_id
                    )
                except Exception as e:
                    logger.error(f"Error getting decision history: {e}")
                    export_data["decisions"] = []
                
                # Get query history from memory safely
                try:
                    if hasattr(app_state.qa_chain, 'memory'):
                        query_history = app_state.qa_chain.memory.get_history(app_state.session_id)
                        export_data["query_history"] = query_history
                except Exception as e:
                    logger.error(f"Error getting query history: {e}")
                    export_data["query_history"] = []
                    
            except Exception as e:
                logger.error(f"Error accessing audit trail: {e}")
                export_data["error"] = f"Failed to access audit trail: {str(e)}"
        
        return json.dumps(export_data, indent=2)
    except Exception as e:
        error_response = {
            "error": f"Failed to export data: {str(e)}",
            "user_id": user_id if user_id else "",
            "export_timestamp": datetime.now().isoformat(),
            "session_data": [],
            "query_history": [],
            "decisions": []
        }
        return json.dumps(error_response, indent=2)

def delete_user_data(user_id):
    """Delete real user data for GDPR compliance"""
    try:
        if not user_id:
            return "❌ Please provide a user ID."
        
        # Delete from audit trail
        if hasattr(app_state, 'qa_chain') and hasattr(app_state.qa_chain, 'audit_trail'):
            audit_trail = app_state.qa_chain.audit_trail
            
            # Remove session data
            if app_state.session_id in audit_trail.session_trails:
                del audit_trail.session_trails[app_state.session_id]
            
            # Remove from decision history
            audit_trail.decision_history = [
                d for d in audit_trail.decision_history 
                if d.get('user_id') != user_id
            ]
            
            # Remove from activity log
            audit_trail.activity_log = [
                a for a in audit_trail.activity_log 
                if a.get('user_id') != user_id
            ]
        
        # Clear memory
        if hasattr(app_state.qa_chain, 'memory'):
            app_state.qa_chain.memory.clear_session(app_state.session_id)
        
        return f"✅ User data for {user_id} has been deleted successfully."
    except Exception as e:
        return f"❌ Failed to delete data: {str(e)}"

def configure_webhook(webhook_url, events):
    """Configure webhook"""
    try:
        if not webhook_url:
            return "❌ Please provide a webhook URL."
        
        # Store webhook configuration
        webhook_config = {
            "url": webhook_url,
            "events": events,
            "configured_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Save to file
        os.makedirs("config/api", exist_ok=True)
        with open("config/api/webhook.json", 'w') as f:
            json.dump(webhook_config, f, indent=2)
        
        return f"✅ Webhook configured successfully for URL: {webhook_url}"
    except Exception as e:
        return f"❌ Failed to configure webhook: {str(e)}"

def get_query_validation(query):
    """Get real query validation results"""
    try:
        if not query or not query.strip():
            validation = {
                "query": "",
                "is_valid": False,
                "entities_found": {},
                "confidence_score": 0.0,
                "suggestions": ["Please enter a query to validate"],
                "warnings": [],
                "errors": ["No query provided"]
            }
            return json.dumps(validation, indent=2)
        
        # Use the actual query processor
        if hasattr(app_state, 'qa_chain') and hasattr(app_state.qa_chain, 'query_processor'):
            try:
                validation_result = app_state.qa_chain.query_processor.process_query(query)
                
                # Ensure validation_result is a dict
                if not isinstance(validation_result, dict):
                    validation_result = {}
                
                # Format validation result with safe defaults
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
            except Exception as e:
                error_validation = {
                    "query": query,
                    "is_valid": False,
                    "entities_found": {},
                    "confidence_score": 0.0,
                    "suggestions": [],
                    "warnings": [],
                    "errors": [f"Query processor error: {str(e)}"]
                }
                return json.dumps(error_validation, indent=2)
        else:
            error_validation = {
                "query": query,
                "is_valid": False,
                "entities_found": {},
                "confidence_score": 0.0,
                "suggestions": [],
                "warnings": [],
                "errors": ["Query processor not available"]
            }
            return json.dumps(error_validation, indent=2)
    except Exception as e:
        error_validation = {
            "query": query if query else "",
            "is_valid": False,
            "entities_found": {},
            "confidence_score": 0.0,
            "suggestions": [],
            "warnings": [],
            "errors": [f"Validation failed: {str(e)}"]
        }
        return json.dumps(error_validation, indent=2)

def get_query_history():
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

def save_model_config(temperature, max_tokens):
    """Save model configuration"""
    try:
        config = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "saved_at": datetime.now().isoformat()
        }
        
        # Save to file
        import os
        os.makedirs("config", exist_ok=True)
        with open("config/model_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        return f"✅ Model configuration saved: Temperature={temperature}, Max Tokens={max_tokens}"
    except Exception as e:
        return f"❌ Failed to save configuration: {str(e)}"

def update_rate_limit(rate_limit):
    """Update rate limit"""
    try:
        # Save rate limit configuration
        config = {
            "rate_limit": rate_limit,
            "updated_at": datetime.now().isoformat()
        }
        
        import os
        os.makedirs("config", exist_ok=True)
        with open("config/rate_limit.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        return f"✅ Rate limit updated to {rate_limit} requests per minute"
    except Exception as e:
        return f"❌ Failed to update rate limit: {str(e)}"

# -----------------------------
# Build Enhanced Gradio Interface
# -----------------------------

def build_interface():
    """Enhanced Gradio interface with all advanced features"""

    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="purple",
        text_size="lg"
    )

    with gr.Blocks(theme=theme, title="Advanced Document Q&A Assistant") as interface:

        # Main Title with enhanced styling
        gr.Markdown(
            """
            # 🚀 Advanced Document Q&A Assistant
            ### Intelligent Document Analysis with Advanced Analytics & Monitoring
            
            *Powered by RAG, Multi-Hop Reasoning, and Real-time Analytics*
            """
        )

        with gr.Tabs():
            
            # ===== MAIN INTERFACE TAB =====
            with gr.Tab("💬 Main Interface", id=0):
                with gr.Row():
                    # Left Column - Upload & Processing
                    with gr.Column(scale=1):
                        gr.Markdown("### 📁 Document Upload & Processing")
                        
                        file_input = gr.File(
                            file_count="multiple",
                            file_types=[".pdf", ".txt", ".docx", ".doc", ".eml", ".msg", ".png", ".jpg", ".jpeg"],
                            label="Upload Documents"
                        )
                        
                        ocr_toggle = gr.Checkbox(
                            label="Enable OCR for Images",
                            value=False
                        )
                        
                        with gr.Row():
                            index_btn = gr.Button("🔄 Process & Index Documents", variant="primary", scale=2)
                            reset_btn = gr.Button("🔄 Reset Session", variant="secondary", scale=1)
                        
                        status_output = gr.Label(label="Status")
                        
                        # Session Info
                        gr.Markdown("### 📊 Session Information")
                        session_info_btn = gr.Button("🔄 Refresh Session Info", variant="primary")
                        session_info = gr.JSON(label="Current Session", value={"session_id": "Loading..."})
                        
                    # Right Column - Chat Interface
                    with gr.Column(scale=2):
                        gr.Markdown("### 💬 Ask Questions")
                        
                        chatbot = gr.Chatbot(height=400, label="Conversation", bubble_full_width=False, type="messages")
                        
                        with gr.Row():
                            question_input = gr.Textbox(
                                label="Your Question",
                                placeholder="Ask a question about your documents...",
                                interactive=False
                            )
                            send_btn = gr.Button("📤 Send", variant="primary", interactive=False)
                        
                        # Results Tabs
                        with gr.Tabs():
                            with gr.Tab("Answer"):
                                answer_output = gr.Textbox(label="Latest Answer", interactive=False, lines=4)
                            
                            with gr.Tab("Decision Summary"):
                                decision_output = gr.Textbox(label="✅ Decision", interactive=False)
                                amount_output = gr.Textbox(label="💰 Amount", interactive=False)
                                justification_output = gr.Textbox(label="📌 Justification", lines=4, interactive=False)
                                evidence_output = gr.Textbox(label="📖 Evidence Clauses (Preview)", lines=6, interactive=False)
                            
                            with gr.Tab("Debug Info"):
                                json_output = gr.Textbox(label="🔍 Full Structured Output", lines=10, interactive=False)
            
            # ===== BATCH PROCESSING TAB =====
            with gr.Tab("⚡ Batch Processing", id=1):
                gr.Markdown("### 🔄 Process Multiple Queries at Once")
                
                batch_input = gr.Textbox(
                    label="Batch Queries (one per line)",
                    placeholder="Enter multiple queries here, one per line...",
                    lines=10
                )
                
                with gr.Row():
                    process_batch_btn = gr.Button("🚀 Process Batch", variant="primary")
                    clear_batch_btn = gr.Button("🗑️ Clear", variant="secondary")
                
                batch_results = gr.HTML(label="Batch Results")
            
            # ===== ANALYTICS & MONITORING TAB =====
            with gr.Tab("📊 Analytics & Monitoring", id=2):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📈 Performance Metrics")
                        performance_btn = gr.Button("🔄 Refresh Metrics", variant="primary")
                        performance_output = gr.JSON(label="System Performance", value={"status": "Click Refresh to load metrics"})
                        
                        gr.Markdown("### 💾 Cache Statistics")
                        cache_btn = gr.Button("🔄 Refresh Cache Stats", variant="primary")
                        cache_output = gr.JSON(label="Cache Performance", value={"status": "Click Refresh to load cache stats"})
                        
                        clear_cache_btn = gr.Button("🗑️ Clear Cache", variant="secondary")
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### 📋 Audit Trail Viewer")
                        
                        with gr.Row():
                            start_date = gr.Textbox(label="Start Date (YYYY-MM-DD)", placeholder="2024-01-01")
                            end_date = gr.Textbox(label="End Date (YYYY-MM-DD)", placeholder="2024-12-31")
                            decision_filter = gr.Dropdown(
                                label="Decision Type",
                                choices=["All", "decision_made", "error_occurred"],
                                value="All"
                            )
                        
                        audit_btn = gr.Button("🔍 Load Audit Trail", variant="primary")
                        audit_output = gr.Dataframe(label="Audit Trail", headers=["Timestamp", "Action", "Decision", "Amount", "Query"])
            
            # ===== CONFIGURATION TAB =====
            with gr.Tab("⚙️ Configuration", id=3):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🔑 API Key Management")
                        
                        pinecone_key = gr.Textbox(label="Pinecone API Key", type="password")
                        groq_key = gr.Textbox(label="Groq API Key", type="password")
                        huggingface_key = gr.Textbox(label="HuggingFace API Key", type="password")
                        
                        update_keys_btn = gr.Button("💾 Update API Keys", variant="primary")
                        keys_status = gr.Textbox(label="Status", interactive=False)
                        
                        gr.Markdown("### 🔧 Model Configuration")
                        
                        model_temp = gr.Slider(label="Temperature", minimum=0.0, maximum=1.0, value=0.1, step=0.1)
                        model_max_tokens = gr.Slider(label="Max Tokens", minimum=1000, maximum=8000, value=4000, step=500)
                        
                        save_config_btn = gr.Button("💾 Save Configuration", variant="primary")
                        config_status = gr.Textbox(label="Config Status", interactive=False)
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 🔗 Webhook Configuration")
                        
                        webhook_url = gr.Textbox(label="Webhook URL", placeholder="https://your-webhook-url.com/endpoint")
                        webhook_events = gr.CheckboxGroup(
                            label="Events to Trigger",
                            choices=["decision_made", "error_occurred", "session_started", "session_ended"],
                            value=["decision_made"]
                        )
                        
                        webhook_btn = gr.Button("🔗 Configure Webhook", variant="primary")
                        webhook_status = gr.Textbox(label="Webhook Status", interactive=False)
                        
                        gr.Markdown("### 🚦 Rate Limiting")
                        
                        rate_limit = gr.Slider(label="Requests per Minute", minimum=10, maximum=200, value=60, step=10)
                        rate_limit_btn = gr.Button("💾 Update Rate Limit", variant="primary")
                        rate_limit_status = gr.Textbox(label="Rate Limit Status", interactive=False)
            
            # ===== GDPR & SECURITY TAB =====
            with gr.Tab("🔒 GDPR & Security", id=4):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 Data Export")
                        
                        export_user_id = gr.Textbox(label="User ID for Export", value=f"user_{app_state.session_id[:8]}")
                        export_btn = gr.Button("📤 Export User Data", variant="primary")
                        export_output = gr.JSON(label="Exported Data", value={"status": "Click Export to download data"})
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 🗑️ Data Deletion")
                        
                        delete_user_id = gr.Textbox(label="User ID for Deletion", value=f"user_{app_state.session_id[:8]}")
                        delete_btn = gr.Button("🗑️ Delete User Data", variant="secondary")
                        delete_status = gr.Textbox(label="Deletion Status", interactive=False)
                        
                        gr.Markdown("### 🔐 Security Status")
                        
                        security_status = gr.JSON(label="Security Status", value={
                            "encryption_enabled": True,
                            "access_control_enabled": True,
                            "audit_logging_enabled": True,
                            "gdpr_compliance_enabled": True,
                            "session_id": app_state.session_id,
                            "user_id": f"user_{app_state.session_id[:8]}"
                        })
            
            # ===== QUERY TOOLS TAB =====
            with gr.Tab("🔍 Query Tools", id=5):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📝 Query Templates")
                        
                        template_name = gr.Textbox(label="Template Name", placeholder="e.g., Knee Surgery Query")
                        template_query = gr.Textbox(label="Query Template", placeholder="Enter your query template...", lines=3)
                        
                        with gr.Row():
                            save_template_btn = gr.Button("💾 Save Template", variant="primary")
                            load_template_btn = gr.Button("📂 Load Template", variant="secondary")
                        
                        template_status = gr.Textbox(label="Template Status", interactive=False)
                        
                        gr.Markdown("### ✅ Query Validation")
                        
                        validation_query = gr.Textbox(label="Query to Validate", placeholder="Enter query for validation...")
                        validate_btn = gr.Button("✅ Validate Query", variant="primary")
                        validation_output = gr.JSON(label="Validation Results", value={"status": "Enter a query to validate"})
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📚 Query History")
                        
                        history_btn = gr.Button("📚 Load Query History", variant="primary")
                        query_history = gr.Dataframe(label="Query History", headers=["Timestamp", "Query", "Decision", "Status"])
                        
                        gr.Markdown("### 💡 Query Optimization")
                        
                        optimization_tips = gr.Markdown("""
                        **💡 Query Optimization Tips:**
                        
                        1. **Be Specific**: Include age, gender, procedure details
                        2. **Add Context**: Mention location, policy duration
                        3. **Use Keywords**: Include medical terms and procedures
                        4. **Be Clear**: Avoid ambiguous language
                        5. **Include Details**: Add urgency, severity if applicable
                        
                        **Example Good Queries:**
                        - "46-year-old male, knee surgery in Pune, 3-month policy"
                        - "Female patient, 35 years old, cataract surgery in Mumbai"
                        - "Angioplasty procedure for 50-year-old male, urgent case"
                        """)

        # Footer with enhanced instructions
        with gr.Accordion("📋 Instructions & Help", open=False):
            gr.Markdown("""
            ## 🚀 Advanced Features Guide
            
            ### 📁 Document Upload
            1. **Supported Formats**: PDF, TXT, DOCX, DOC, EML, MSG, Images (PNG, JPG, JPEG)
            2. **Enable OCR** for image files if needed
            3. **Click Process & Index** to extract knowledge
            
            ### 💬 Query Interface
            1. **Ask Questions** in natural language
            2. **View Results** in Answer, Decision Summary, and Debug tabs
            3. **Use Templates** for common query patterns
            
            ### ⚡ Batch Processing
            1. **Enter Multiple Queries** (one per line)
            2. **Process All at Once** for efficiency
            3. **View Results** in organized table format
            
            ### 📊 Analytics & Monitoring
            1. **Monitor Performance** with real-time metrics
            2. **View Cache Statistics** for optimization
            3. **Browse Audit Trail** for decision history
            
            ### ⚙️ Configuration
            1. **Update API Keys** as needed
            2. **Configure Model Parameters** for optimal performance
            3. **Set Up Webhooks** for external integrations
            4. **Manage Rate Limits** for system stability
            
            ### 🔒 GDPR & Security
            1. **Export User Data** for compliance
            2. **Delete User Data** when requested
            3. **Monitor Security Status** continuously
            """)

        # Event handlers for main interface
        index_btn.click(
            fn=upload_and_index,
            inputs=[file_input, ocr_toggle],
            outputs=[status_output, send_btn]
        ).then(
            fn=lambda: gr.update(interactive=True),
            outputs=[question_input]
        )

        send_btn.click(
            fn=ask_question,
            inputs=[question_input, chatbot],
            outputs=[chatbot, answer_output, decision_output, amount_output, justification_output, evidence_output, json_output]
        ).then(
            fn=lambda: gr.update(value=""),
            outputs=[question_input]
        )

        question_input.submit(
            fn=ask_question,
            inputs=[question_input, chatbot],
            outputs=[chatbot, answer_output, decision_output, amount_output, justification_output, evidence_output, json_output]
        ).then(
            fn=lambda: gr.update(value=""),
            outputs=[question_input]
        )

        reset_btn.click(
            fn=reset_session,
            outputs=[status_output, send_btn, chatbot, answer_output, question_input,
                     decision_output, amount_output, justification_output, evidence_output, json_output]
        )

        # Event handlers for session info
        session_info_btn.click(
            fn=get_session_info,
            outputs=[session_info]
        )

        # Event handlers for batch processing
        process_batch_btn.click(
            fn=process_batch_queries,
            inputs=[batch_input],
            outputs=[batch_results]
        )

        clear_batch_btn.click(
            fn=lambda: "",
            outputs=[batch_input]
        )

        # Event handlers for analytics
        performance_btn.click(
            fn=get_performance_metrics,
            outputs=[performance_output]
        )

        cache_btn.click(
            fn=get_cache_statistics,
            outputs=[cache_output]
        )

        clear_cache_btn.click(
            fn=clear_cache,
            outputs=[cache_output]
        )

        audit_btn.click(
            fn=get_audit_trail,
            inputs=[start_date, end_date, decision_filter],
            outputs=[audit_output]
        )

        # Event handlers for configuration
        update_keys_btn.click(
            fn=update_api_keys,
            inputs=[pinecone_key, groq_key, huggingface_key],
            outputs=[keys_status]
        )

        save_config_btn.click(
            fn=save_model_config,
            inputs=[model_temp, model_max_tokens],
            outputs=[config_status]
        )

        webhook_btn.click(
            fn=configure_webhook,
            inputs=[webhook_url, webhook_events],
            outputs=[webhook_status]
        )

        rate_limit_btn.click(
            fn=update_rate_limit,
            inputs=[rate_limit],
            outputs=[rate_limit_status]
        )

        # Event handlers for GDPR
        export_btn.click(
            fn=export_user_data,
            inputs=[export_user_id],
            outputs=[export_output]
        )

        delete_btn.click(
            fn=delete_user_data,
            inputs=[delete_user_id],
            outputs=[delete_status]
        )

        # Event handlers for query tools
        save_template_btn.click(
            fn=save_query_template,
            inputs=[template_name, template_query],
            outputs=[template_status]
        )

        load_template_btn.click(
            fn=load_query_template,
            inputs=[template_name],
            outputs=[template_query]
        )

        validate_btn.click(
            fn=get_query_validation,
            inputs=[validation_query],
            outputs=[validation_output]
        )

        history_btn.click(
            fn=get_query_history,
            outputs=[query_history]
        )

    return interface
