import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from src.api.setup_api import logger
from src.core.qa_chain import QAChain
from src.utils.cache_manager import CacheManager
from src.utils.security_manager import SecurityManager

# -----------------------------
# API Endpoints System
# -----------------------------
class APIEndpoints:
    """RESTful API endpoints for the document Q&A system"""
    
    def __init__(self, qa_chain: QAChain, cache_manager: CacheManager, security_manager: SecurityManager):
        self.qa_chain = qa_chain
        self.cache_manager = cache_manager
        self.security_manager = security_manager
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        
        # API configuration
        self.api_config = {
            "version": "1.0.0",
            "rate_limit_enabled": True,
            "max_requests_per_minute": 60,
            "webhook_enabled": True,
            "batch_processing_enabled": True
        }
        
        # Webhook endpoints - load from file
        self.webhook_endpoints = {}
        self._load_webhook_config()
        
        # Rate limiting
        self.request_counts = {}
        
        # Register routes
        self._register_routes()
        
        logger.info("API Endpoints initialized")
    
    def _load_webhook_config(self):
        """Load webhook configuration from file"""
        try:
            webhook_file = "config/api/webhook.json"
            if not os.path.exists(webhook_file):
                # Backward compatibility with older layout.
                webhook_file = "config/webhook.json"
            if os.path.exists(webhook_file):
                with open(webhook_file, 'r') as f:
                    webhook_config = json.load(f)
                
                # Create a webhook endpoint from the configuration
                webhook_id = "gradio_webhook"
                self.webhook_endpoints[webhook_id] = {
                    "url": webhook_config.get("url", ""),
                    "events": webhook_config.get("events", []),
                    "active": webhook_config.get("status") == "active",
                    "created_at": webhook_config.get("configured_at", datetime.now().isoformat())
                }
                
                logger.info(f"Loaded webhook configuration: {webhook_config.get('url', 'No URL')}")
            else:
                logger.info("No webhook configuration file found")
        except Exception as e:
            logger.error(f"Failed to load webhook configuration: {e}")
    
    def _reload_webhook_config(self):
        """Reload webhook configuration from file"""
        self._load_webhook_config()
    
    def _register_routes(self):
        """Register all API routes"""
        
        # Health check
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": self.api_config["version"]
            })
        
        # Query endpoint
        @self.app.route('/api/v1/query', methods=['POST'])
        def process_query():
            return self._handle_query_request()
        
        # Batch query endpoint
        @self.app.route('/api/v1/batch-query', methods=['POST'])
        def process_batch_query():
            return self._handle_batch_query_request()
        
        # Document processing endpoint
        @self.app.route('/api/v1/documents', methods=['POST'])
        def process_documents():
            return self._handle_document_processing()
        
        # Audit trail endpoint
        @self.app.route('/api/v1/audit-trail', methods=['GET'])
        def get_audit_trail():
            return self._handle_audit_trail_request()
        
        # Cache statistics endpoint
        @self.app.route('/api/v1/cache/stats', methods=['GET'])
        def get_cache_stats():
            return self._handle_cache_stats_request()
        
        # Security statistics endpoint
        @self.app.route('/api/v1/security/stats', methods=['GET'])
        def get_security_stats():
            return self._handle_security_stats_request()
        
        # GDPR compliance endpoints
        @self.app.route('/api/v1/gdpr/export/<user_id>', methods=['GET'])
        def export_user_data(user_id):
            return self._handle_gdpr_export(user_id)
        
        @self.app.route('/api/v1/gdpr/delete/<user_id>', methods=['DELETE'])
        def delete_user_data(user_id):
            return self._handle_gdpr_deletion(user_id)
        
        # Webhook management endpoints
        @self.app.route('/api/v1/webhooks', methods=['POST'])
        def register_webhook():
            return self._handle_webhook_registration()
        
        @self.app.route('/api/v1/webhooks/<webhook_id>', methods=['DELETE'])
        def unregister_webhook(webhook_id):
            return self._handle_webhook_unregistration(webhook_id)
        
        # Session management endpoints
        @self.app.route('/api/v1/session', methods=['POST'])
        def create_session():
            return self._handle_session_creation()
        
        @self.app.route('/api/v1/session/<session_token>', methods=['DELETE'])
        def invalidate_session(session_token):
            return self._handle_session_invalidation(session_token)
    
    def _handle_query_request(self) -> Response:
        """Handle single query request"""
        try:
            # Check rate limiting
            if not self._check_rate_limit(request):
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            # Validate request
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({"error": "Missing query parameter"}), 400
            
            # Extract parameters
            query = data['query']
            session_id = data.get('session_id', 'default_session')
            user_id = data.get('user_id', 'default_user')
            
            # Check security permissions
            session_token = data.get('session_token')
            if session_token and not self.security_manager.check_permission(session_token, "query"):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            # Reload webhook config before processing
            self._reload_webhook_config()
            
            # Get retriever for the session
            retriever = None
            try:
                # Get vector_store from app_state (not qa_chain)
                from src.utils.app_state import app_state
                if hasattr(app_state, 'vector_store') and app_state.vector_store:
                    retriever = app_state.vector_store.get_retriever(session_id)
                else:
                    logger.warning("Vector store not available in app_state")
            except Exception as e:
                logger.error(f"Failed to get retriever: {e}")
                # Continue without retriever - qa_chain will handle it
            
            # Process query
            result = self.qa_chain.run(query, retriever, session_id, user_id)
            
            # Log data access
            self.security_manager.log_data_access(user_id, "query", "process", {
                "query": query,
                "session_id": session_id
            })
            
            # Trigger webhooks with proper event types
            webhook_data = {
                "query": query,
                "session_id": session_id,
                "user_id": user_id,
                "result": result.get("answer", ""),
                "decision": result.get("decision", {}),
                "processing_time": result.get("processing_time", 0),
                "audit_id": result.get("audit_id", "")
            }
            
            # Trigger different webhook events based on result
            if "decision" in result and result["decision"]:
                self._trigger_webhooks("decision_made", webhook_data)
            else:
                self._trigger_webhooks("query_processed", webhook_data)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Query request failed: {e}")
            # Trigger error webhook
            self._trigger_webhooks("error_occurred", {
                "error": str(e),
                "query": data.get('query', '') if 'data' in locals() else '',
                "session_id": data.get('session_id', '') if 'data' in locals() else '',
                "user_id": data.get('user_id', '') if 'data' in locals() else ''
            })
            return jsonify({"error": str(e)}), 500
    
    def _handle_batch_query_request(self) -> Response:
        """Handle batch query request"""
        try:
            # Check rate limiting
            if not self._check_rate_limit(request):
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            # Validate request
            data = request.get_json()
            if not data or 'queries' not in data:
                return jsonify({"error": "Missing queries parameter"}), 400
            
            queries = data['queries']
            if not isinstance(queries, list) or len(queries) > 10:  # Limit batch size
                return jsonify({"error": "Invalid queries format or too many queries"}), 400
            
            # Check security permissions
            session_token = data.get('session_token')
            if session_token and not self.security_manager.check_permission(session_token, "batch_query"):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            # Process batch queries
            results = []
            for i, query_data in enumerate(queries):
                if isinstance(query_data, dict):
                    query = query_data.get('query', '')
                    session_id = query_data.get('session_id', f'batch_session_{i}')
                    user_id = query_data.get('user_id', 'default_user')
                else:
                    query = str(query_data)
                    session_id = f'batch_session_{i}'
                    user_id = 'default_user'
                
                try:
                    result = self.qa_chain.run(query, None, session_id, user_id)
                    results.append({
                        "query": query,
                        "result": result,
                        "status": "success"
                    })
                except Exception as e:
                    results.append({
                        "query": query,
                        "error": str(e),
                        "status": "error"
                    })
            
            # Log batch data access
            user_id = data.get('user_id', 'default_user')
            self.security_manager.log_data_access(user_id, "batch_query", "process", {
                "query_count": len(queries),
                "success_count": len([r for r in results if r["status"] == "success"])
            })
            
            # Trigger webhooks
            self._trigger_webhooks("batch_query_processed", {"results": results})
            
            return jsonify({
                "batch_id": f"batch_{datetime.now().timestamp()}",
                "total_queries": len(queries),
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Batch query request failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_document_processing(self) -> Response:
        """Handle document processing request"""
        try:
            # Check rate limiting
            if not self._check_rate_limit(request):
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            # Validate request
            data = request.get_json()
            if not data or 'documents' not in data:
                return jsonify({"error": "Missing documents parameter"}), 400
            
            # Check security permissions
            session_token = data.get('session_token')
            if session_token and not self.security_manager.check_permission(session_token, "document_upload"):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            documents = data['documents']
            results = []
            
            for doc in documents:
                try:
                    # Process document (placeholder for actual document processing)
                    doc_id = doc.get('id', f"doc_{datetime.now().timestamp()}")
                    doc_type = doc.get('type', 'unknown')
                    
                    results.append({
                        "document_id": doc_id,
                        "type": doc_type,
                        "status": "processed",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    results.append({
                        "document_id": doc.get('id', 'unknown'),
                        "status": "error",
                        "error": str(e)
                    })
            
            # Log document processing
            user_id = data.get('user_id', 'default_user')
            self.security_manager.log_data_access(user_id, "document", "upload", {
                "document_count": len(documents),
                "success_count": len([r for r in results if r["status"] == "processed"])
            })
            
            # Trigger webhooks
            self._trigger_webhooks("documents_processed", {"results": results})
            
            return jsonify({
                "processing_id": f"proc_{datetime.now().timestamp()}",
                "total_documents": len(documents),
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Document processing request failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_audit_trail_request(self) -> Response:
        """Handle audit trail request"""
        try:
            # Check security permissions
            session_token = request.args.get('session_token')
            if session_token and not self.security_manager.check_permission(session_token, "audit_read"):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            # Get query parameters
            session_id = request.args.get('session_id')
            user_id = request.args.get('user_id')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            action_type = request.args.get('action_type')
            
            # Get audit trail
            audit_trail = self.qa_chain.get_audit_trail(
                session_id=session_id,
                user_id=user_id,
                start_date=datetime.fromisoformat(start_date) if start_date else None,
                end_date=datetime.fromisoformat(end_date) if end_date else None,
                action_type=action_type
            )
            
            return jsonify({
                "audit_trail": audit_trail,
                "total_entries": len(audit_trail),
                "filters": {
                    "session_id": session_id,
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "action_type": action_type
                }
            })
            
        except Exception as e:
            logger.error(f"Audit trail request failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_cache_stats_request(self) -> Response:
        """Handle cache statistics request"""
        try:
            # Check security permissions
            session_token = request.args.get('session_token')
            if session_token and not self.security_manager.check_permission(session_token, "cache_read"):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            stats = self.cache_manager.get_cache_statistics()
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Cache stats request failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_security_stats_request(self) -> Response:
        """Handle security statistics request"""
        try:
            # Check security permissions
            session_token = request.args.get('session_token')
            if session_token and not self.security_manager.check_permission(session_token, "security_read"):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            stats = self.security_manager.get_security_statistics()
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Security stats request failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_gdpr_export(self, user_id: str) -> Response:
        """Handle GDPR data export request"""
        try:
            # Check security permissions
            session_token = request.args.get('session_token')
            if session_token and not self.security_manager.check_permission(session_token, "gdpr_export"):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            export_data = self.security_manager.export_user_data(user_id)
            return jsonify(export_data)
            
        except Exception as e:
            logger.error(f"GDPR export request failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_gdpr_deletion(self, user_id: str) -> Response:
        """Handle GDPR data deletion request"""
        try:
            # Check security permissions
            session_token = request.args.get('session_token')
            if session_token and not self.security_manager.check_permission(session_token, "gdpr_delete"):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            success = self.security_manager.delete_user_data(user_id)
            
            if success:
                return jsonify({"status": "success", "message": f"Data deleted for user {user_id}"})
            else:
                return jsonify({"error": "Failed to delete user data"}), 500
            
        except Exception as e:
            logger.error(f"GDPR deletion request failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_webhook_registration(self) -> Response:
        """Handle webhook registration"""
        try:
            data = request.get_json()
            if not data or 'url' not in data:
                return jsonify({"error": "Missing URL parameter"}), 400
            
            webhook_id = f"webhook_{datetime.now().timestamp()}"
            webhook_config = {
                "url": data['url'],
                "events": data.get('events', ['query_processed']),
                "secret": data.get('secret'),
                "active": True,
                "created_at": datetime.now().isoformat()
            }
            
            self.webhook_endpoints[webhook_id] = webhook_config
            
            return jsonify({
                "webhook_id": webhook_id,
                "status": "registered",
                "config": webhook_config
            })
            
        except Exception as e:
            logger.error(f"Webhook registration failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_webhook_unregistration(self, webhook_id: str) -> Response:
        """Handle webhook unregistration"""
        try:
            if webhook_id in self.webhook_endpoints:
                del self.webhook_endpoints[webhook_id]
                return jsonify({"status": "unregistered", "webhook_id": webhook_id})
            else:
                return jsonify({"error": "Webhook not found"}), 404
            
        except Exception as e:
            logger.error(f"Webhook unregistration failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_session_creation(self) -> Response:
        """Handle session creation"""
        try:
            data = request.get_json()
            user_id = data.get('user_id', 'default_user')
            permissions = data.get('permissions', ['read', 'query'])
            
            session_token = self.security_manager.create_user_session(user_id, permissions)
            
            if session_token:
                return jsonify({
                    "session_token": session_token,
                    "user_id": user_id,
                    "permissions": permissions,
                    "expires_in": self.security_manager.security_config["session_timeout"]
                })
            else:
                return jsonify({"error": "Failed to create session"}), 500
            
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _handle_session_invalidation(self, session_token: str) -> Response:
        """Handle session invalidation"""
        try:
            success = self.security_manager.invalidate_session(session_token)
            
            if success:
                return jsonify({"status": "invalidated", "session_token": session_token})
            else:
                return jsonify({"error": "Session not found or already invalidated"}), 404
            
        except Exception as e:
            logger.error(f"Session invalidation failed: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _check_rate_limit(self, request) -> bool:
        """Check rate limiting"""
        try:
            if not self.api_config["rate_limit_enabled"]:
                return True
            
            client_ip = request.remote_addr
            current_time = datetime.now()
            
            # Clean old entries
            self.request_counts = {
                ip: times for ip, times in self.request_counts.items()
                if (current_time - times[-1]).total_seconds() < 60
            }
            
            # Check rate limit
            if client_ip in self.request_counts:
                recent_requests = [
                    time for time in self.request_counts[client_ip]
                    if (current_time - time).total_seconds() < 60
                ]
                
                if len(recent_requests) >= self.api_config["max_requests_per_minute"]:
                    return False
                
                self.request_counts[client_ip] = recent_requests
            
            # Add current request
            if client_ip not in self.request_counts:
                self.request_counts[client_ip] = []
            
            self.request_counts[client_ip].append(current_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow request if rate limiting fails
    
    def _trigger_webhooks(self, event_type: str, data: Dict[str, Any]):
        """Trigger webhooks for events"""
        try:
            if not self.api_config["webhook_enabled"]:
                return
            
            import requests
            
            for webhook_id, webhook_config in self.webhook_endpoints.items():
                if not webhook_config.get("active", False):
                    continue
                
                if event_type not in webhook_config.get("events", []):
                    continue
                
                try:
                    payload = {
                        "event_type": event_type,
                        "webhook_id": webhook_id,
                        "timestamp": datetime.now().isoformat(),
                        "data": data
                    }
                    
                    # Add secret if configured
                    if webhook_config.get("secret"):
                        payload["signature"] = self._generate_webhook_signature(
                            payload, webhook_config["secret"]
                        )
                    
                    # Send webhook
                    response = requests.post(
                        webhook_config["url"],
                        json=payload,
                        timeout=10
                    )
                    
                    if response.status_code != 200:
                        logger.warning(f"Webhook {webhook_id} failed: {response.status_code}")
                    
                except Exception as e:
                    logger.error(f"Failed to trigger webhook {webhook_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Webhook triggering failed: {e}")
    
    def _generate_webhook_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate webhook signature for security"""
        try:
            import hmac
            import hashlib
            
            # Create signature from payload
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"Failed to generate webhook signature: {e}")
            return ""
    
    def run(self, host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
        """Run the API server"""
        try:
            logger.info(f"Starting API server on {host}:{port}")
            # Suppress Flask development server warnings
            import logging
            logging.getLogger('werkzeug').setLevel(logging.ERROR)
            
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            raise 