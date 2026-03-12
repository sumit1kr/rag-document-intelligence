import json
import logging
import hashlib
import secrets
import base64
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.api.setup_api import logger

# -----------------------------
# Security & Compliance System
# -----------------------------
class SecurityManager:
    """Comprehensive security and compliance management system"""
    
    def __init__(self):
        # Security configuration
        self.security_config = {
            "encryption_enabled": True,
            "access_control_enabled": True,
            "audit_logging_enabled": True,
            "gdpr_compliance_enabled": True,
            "session_timeout": 3600,  # 1 hour
            "max_login_attempts": 5,
            "password_min_length": 8,
            "data_retention_days": 365
        }
        
        # Encryption key management
        self.encryption_key = self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Access control
        self.user_sessions = {}
        self.user_permissions = {}
        self.login_attempts = {}
        
        # Audit logging
        self.security_audit_log = []
        
        # GDPR compliance
        self.data_subjects = {}
        self.data_processing_records = {}
        self.consent_records = {}
        
        logger.info("Security Manager initialized")
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            if not self.security_config["encryption_enabled"]:
                return data
            
            # Convert string to bytes and encrypt
            data_bytes = data.encode('utf-8')
            encrypted_data = self.cipher_suite.encrypt(data_bytes)
            
            # Return base64 encoded encrypted data
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            if not self.security_config["encryption_enabled"]:
                return encrypted_data
            
            # Decode base64 and decrypt
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return encrypted_data
    
    def hash_password(self, password: str) -> str:
        """Hash password using secure hashing"""
        try:
            # Generate salt and hash password
            salt = secrets.token_hex(16)
            password_hash = hashlib.pbkdf2_hmac(
                'sha256', 
                password.encode('utf-8'), 
                salt.encode('utf-8'), 
                100000
            )
            
            return f"{salt}:{password_hash.hex()}"
            
        except Exception as e:
            logger.error(f"Failed to hash password: {e}")
            return ""
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            if not stored_hash or ':' not in stored_hash:
                return False
            
            salt, hash_value = stored_hash.split(':', 1)
            password_hash = hashlib.pbkdf2_hmac(
                'sha256', 
                password.encode('utf-8'), 
                salt.encode('utf-8'), 
                100000
            )
            
            return password_hash.hex() == hash_value
            
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False
    
    def create_user_session(self, user_id: str, permissions: List[str] = None) -> str:
        """Create a new user session with access control"""
        try:
            if not self.security_config["access_control_enabled"]:
                return "default_session"
            
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            
            # Create session with permissions
            session_data = {
                "user_id": user_id,
                "permissions": permissions or ["read", "query"],
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "is_active": True
            }
            
            self.user_sessions[session_token] = session_data
            
            # Log session creation
            self._log_security_event("session_created", user_id, {
                "session_token": session_token,
                "permissions": permissions
            })
            
            logger.info(f"Created session for user: {user_id}")
            return session_token
            
        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
            return None
    
    def validate_session(self, session_token: str) -> Dict[str, Any]:
        """Validate user session and return session data"""
        try:
            if not self.security_config["access_control_enabled"]:
                return {"user_id": "default_user", "permissions": ["read", "query"], "is_valid": True}
            
            session_data = self.user_sessions.get(session_token)
            
            if not session_data:
                return {"is_valid": False, "error": "Session not found"}
            
            # Check if session is active
            if not session_data.get("is_active", False):
                return {"is_valid": False, "error": "Session inactive"}
            
            # Check session timeout
            last_activity = session_data["last_activity"]
            timeout_seconds = self.security_config["session_timeout"]
            
            if (datetime.now() - last_activity).total_seconds() > timeout_seconds:
                self._invalidate_session(session_token)
                return {"is_valid": False, "error": "Session expired"}
            
            # Update last activity
            session_data["last_activity"] = datetime.now()
            
            return {
                "is_valid": True,
                "user_id": session_data["user_id"],
                "permissions": session_data["permissions"],
                "session_data": session_data
            }
            
        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return {"is_valid": False, "error": str(e)}
    
    def check_permission(self, session_token: str, required_permission: str) -> bool:
        """Check if user has required permission"""
        try:
            if not self.security_config["access_control_enabled"]:
                return True
            
            session_validation = self.validate_session(session_token)
            
            if not session_validation["is_valid"]:
                return False
            
            user_permissions = session_validation.get("permissions", [])
            
            # Check if user has required permission
            has_permission = required_permission in user_permissions or "admin" in user_permissions
            
            # Log permission check
            self._log_security_event("permission_check", session_validation["user_id"], {
                "required_permission": required_permission,
                "user_permissions": user_permissions,
                "granted": has_permission
            })
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Failed to check permission: {e}")
            return False
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate user session"""
        try:
            if not self.security_config["access_control_enabled"]:
                return True
            
            return self._invalidate_session(session_token)
            
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False
    
    def _invalidate_session(self, session_token: str) -> bool:
        """Internal method to invalidate session"""
        try:
            if session_token in self.user_sessions:
                user_id = self.user_sessions[session_token]["user_id"]
                del self.user_sessions[session_token]
                
                # Log session invalidation
                self._log_security_event("session_invalidated", user_id, {
                    "session_token": session_token
                })
                
                logger.info(f"Invalidated session for user: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False
    
    def sanitize_data_for_export(self, data: Any) -> Any:
        """Sanitize data for export by removing sensitive information"""
        try:
            if isinstance(data, dict):
                sanitized = {}
                sensitive_fields = ["password", "api_key", "token", "secret", "key"]
                
                for key, value in data.items():
                    if any(sensitive in key.lower() for sensitive in sensitive_fields):
                        sanitized[key] = "[REDACTED]"
                    else:
                        sanitized[key] = self.sanitize_data_for_export(value)
                
                return sanitized
            elif isinstance(data, list):
                return [self.sanitize_data_for_export(item) for item in data]
            else:
                return data
                
        except Exception as e:
            logger.error(f"Failed to sanitize data: {e}")
            return data
    
    def log_data_access(self, user_id: str, data_type: str, action: str, details: Dict[str, Any] = None):
        """Log data access for GDPR compliance"""
        try:
            if not self.security_config["audit_logging_enabled"]:
                return
            
            access_log = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "data_type": data_type,
                "action": action,
                "details": details or {},
                "session_id": details.get("session_id") if details else None
            }
            
            self.security_audit_log.append(access_log)
            
            # Log to GDPR compliance records
            if self.security_config["gdpr_compliance_enabled"]:
                self._log_gdpr_data_access(user_id, data_type, action, details)
            
        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
    
    def _log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any] = None):
        """Log security events"""
        try:
            security_event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "details": details or {},
                "ip_address": details.get("ip_address") if details else None
            }
            
            self.security_audit_log.append(security_event)
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _log_gdpr_data_access(self, user_id: str, data_type: str, action: str, details: Dict[str, Any] = None):
        """Log GDPR-compliant data access"""
        try:
            gdpr_record = {
                "timestamp": datetime.now().isoformat(),
                "data_subject_id": user_id,
                "data_type": data_type,
                "processing_purpose": details.get("purpose", "query_processing"),
                "legal_basis": details.get("legal_basis", "legitimate_interest"),
                "action": action,
                "data_retention_period": self.security_config["data_retention_days"],
                "consent_given": details.get("consent_given", True)
            }
            
            if user_id not in self.data_processing_records:
                self.data_processing_records[user_id] = []
            
            self.data_processing_records[user_id].append(gdpr_record)
            
        except Exception as e:
            logger.error(f"Failed to log GDPR data access: {e}")
    
    def get_data_subject_rights(self, user_id: str) -> Dict[str, Any]:
        """Get GDPR data subject rights information"""
        try:
            if not self.security_config["gdpr_compliance_enabled"]:
                return {"gdpr_enabled": False}
            
            user_records = self.data_processing_records.get(user_id, [])
            
            return {
                "gdpr_enabled": True,
                "data_subject_id": user_id,
                "processing_records_count": len(user_records),
                "rights": {
                    "right_to_access": True,
                    "right_to_rectification": True,
                    "right_to_erasure": True,
                    "right_to_portability": True,
                    "right_to_restriction": True,
                    "right_to_object": True
                },
                "data_retention_days": self.security_config["data_retention_days"],
                "last_processing": user_records[-1]["timestamp"] if user_records else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get data subject rights: {e}")
            return {"error": str(e)}
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data for GDPR right to portability"""
        try:
            if not self.security_config["gdpr_compliance_enabled"]:
                return {"gdpr_enabled": False}
            
            user_records = self.data_processing_records.get(user_id, [])
            
            # Sanitize data before export
            sanitized_records = self.sanitize_data_for_export(user_records)
            
            return {
                "gdpr_enabled": True,
                "data_subject_id": user_id,
                "export_timestamp": datetime.now().isoformat(),
                "processing_records": sanitized_records,
                "data_retention_policy": {
                    "retention_days": self.security_config["data_retention_days"],
                    "auto_deletion_enabled": True
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to export user data: {e}")
            return {"error": str(e)}
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete user data for GDPR right to erasure"""
        try:
            if not self.security_config["gdpr_compliance_enabled"]:
                return True
            
            # Remove from data processing records
            if user_id in self.data_processing_records:
                del self.data_processing_records[user_id]
            
            # Remove from consent records
            if user_id in self.consent_records:
                del self.consent_records[user_id]
            
            # Remove from data subjects
            if user_id in self.data_subjects:
                del self.data_subjects[user_id]
            
            # Log deletion
            self._log_security_event("data_deletion", user_id, {
                "deletion_type": "gdpr_erasure",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Deleted GDPR data for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False
    
    def get_security_audit_log(self, 
                              start_date: datetime = None,
                              end_date: datetime = None,
                              event_type: str = None,
                              user_id: str = None) -> List[Dict[str, Any]]:
        """Get filtered security audit log"""
        try:
            filtered_log = []
            
            for entry in self.security_audit_log:
                # Apply filters
                if event_type and entry.get("event_type") != event_type:
                    continue
                
                if user_id and entry.get("user_id") != user_id:
                    continue
                
                # Date filtering
                if start_date or end_date:
                    entry_timestamp = datetime.fromisoformat(entry["timestamp"])
                    
                    if start_date and entry_timestamp < start_date:
                        continue
                    
                    if end_date and entry_timestamp > end_date:
                        continue
                
                filtered_log.append(entry)
            
            return filtered_log
            
        except Exception as e:
            logger.error(f"Failed to get security audit log: {e}")
            return []
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security statistics and compliance metrics"""
        try:
            # Calculate statistics
            total_events = len(self.security_audit_log)
            active_sessions = sum(1 for session in self.user_sessions.values() if session.get("is_active", False))
            
            # Event type breakdown
            event_types = {}
            for entry in self.security_audit_log:
                event_type = entry.get("event_type", "unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # GDPR compliance metrics
            gdpr_metrics = {
                "data_subjects_count": len(self.data_subjects),
                "processing_records_count": sum(len(records) for records in self.data_processing_records.values()),
                "consent_records_count": len(self.consent_records)
            }
            
            return {
                "total_security_events": total_events,
                "active_sessions": active_sessions,
                "event_type_breakdown": event_types,
                "gdpr_compliance": gdpr_metrics,
                "security_config": {
                    "encryption_enabled": self.security_config["encryption_enabled"],
                    "access_control_enabled": self.security_config["access_control_enabled"],
                    "audit_logging_enabled": self.security_config["audit_logging_enabled"],
                    "gdpr_compliance_enabled": self.security_config["gdpr_compliance_enabled"]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get security statistics: {e}")
            return {"error": str(e)}
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key"""
        try:
            # Generate a random key
            key = Fernet.generate_key()
            return key
            
        except Exception as e:
            logger.error(f"Failed to generate encryption key: {e}")
            # Fallback to a default key (not recommended for production)
            return b'default_key_for_development_only_' 