"""
OpenHands-Clone Security - Phase 2
================================
Security analysis and action confirmation.

Phase 2: Security integration matching SDK patterns.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# =============================================================================
# Security Levels
# =============================================================================

class SecurityLevel(Enum):
    """Security levels for actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(Enum):
    """Status of action after security review."""
    APPROVED = "approved"
    DENIED = "denied"
    NEEDS_CONFIRMATION = "needs_confirmation"


# =============================================================================
# Security Policy
# =============================================================================

@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    
    name: str = "default"
    allow_destructive: bool = False
    allow_network: bool = True
    allow_file_write: bool = True
    allow_execute: bool = True
    confirmation_threshold: SecurityLevel = SecurityLevel.MEDIUM
    
    @classmethod
    def default(cls) -> "SecurityPolicy":
        """Default policy."""
        return cls(name="default")
    
    @classmethod
    def strict(cls) -> "SecurityPolicy":
        """Strict policy - requires confirmation for most actions."""
        return cls(
            name="strict",
            allow_destructive=False,
            allow_network=True,
            allow_file_write=True,
            allow_execute=False,
            confirmation_threshold=SecurityLevel.LOW,
        )
    
    @classmethod
    def permissive(cls) -> "SecurityPolicy":
        """Permissive policy - minimal restrictions."""
        return cls(
            name="permissive",
            allow_destructive=True,
            allow_network=True,
            allow_file_write=True,
            allow_execute=True,
            confirmation_threshold=SecurityLevel.CRITICAL,
        )


# =============================================================================
# Action Classifier
# =============================================================================

class ActionClassifier:
    """Classify actions by security risk."""
    
    # Patterns for different action types
    DESTRUCTIVE_PATTERNS = [
        "rm -rf",
        "delete",
        "drop table",
        "truncate",
        "remove file",
    ]
    
    NETWORK_PATTERNS = [
        "curl",
        "wget", 
        "fetch",
        "request",
        "http",
    ]
    
    FILE_WRITE_PATTERNS = [
        "write",
        "create",
        "edit",
        "modify",
        "update",
    ]
    
    EXECUTE_PATTERNS = [
        "exec",
        "run",
        "command",
        "bash",
    ]
    
    @classmethod
    def classify(cls, action: str) -> SecurityLevel:
        """Classify action security level."""
        action_lower = action.lower()
        
        # Check destructive
        for pattern in cls.DESTRUCTIVE_PATTERNS:
            if pattern in action_lower:
                return SecurityLevel.CRITICAL
        
        # Check network
        for pattern in cls.NETWORK_PATTERNS:
            if pattern in action_lower:
                return SecurityLevel.MEDIUM
        
        # Check file write
        for pattern in cls.FILE_WRITE_PATTERNS:
            if pattern in action_lower:
                return SecurityLevel.LOW
        
        # Check execute
        for pattern in cls.EXECUTE_PATTERNS:
            if pattern in action_lower:
                return SecurityLevel.MEDIUM
        
        return SecurityLevel.LOW
    
    @classmethod
    def requires_confirmation(cls, action: str, policy: SecurityPolicy) -> bool:
        """Check if action requires confirmation."""
        level = cls.classify(action)
        threshold = policy.confirmation_threshold
        
        # Compare security levels
        level_order = {
            SecurityLevel.LOW: 0,
            SecurityLevel.MEDIUM: 1,
            SecurityLevel.HIGH: 2,
            SecurityLevel.CRITICAL: 3,
        }
        
        return level_order[level] >= level_order[threshold]


# =============================================================================
# Security Analyzer
# =============================================================================

class SecurityAnalyzer:
    """Analyze actions for security risks."""
    
    def __init__(self, policy: SecurityPolicy | None = None):
        self.policy = policy or SecurityPolicy.default()
        self._allowed_actions: set[str] = set()
        self._denied_actions: set[str] = set()
    
    def analyze(self, action: str) -> ActionStatus:
        """Analyze an action."""
        # Check if explicitly denied
        if action in self._denied_actions:
            return ActionStatus.DENIED
        
        # Check if allowed without confirmation
        if action in self._allowed_actions:
            return ActionStatus.APPROVED
        
        # Check if confirmation needed
        if ActionClassifier.requires_confirmation(action, self.policy):
            return ActionStatus.NEEDS_CONFIRMATION
        
        return ActionStatus.APPROVED
    
    def approve(self, action: str) -> None:
        """Approve an action permanently."""
        self._allowed_actions.add(action)
    
    def deny(self, action: str) -> None:
        """Deny an action permanently."""
        self._denied_actions.add(action)
    
    def get_risk_level(self, action: str) -> SecurityLevel:
        """Get risk level for action."""
        return ActionClassifier.classify(action)


# =============================================================================
# Confirmation Handler
# =============================================================================

class ConfirmationHandler:
    """Handle action confirmations."""
    
    def __init__(self, analyzer: SecurityAnalyzer):
        self.analyzer = analyzer
    
    def should_confirm(self, action: str) -> bool:
        """Check if confirmation is needed."""
        return self.analyzer.analyze(action) == ActionStatus.NEEDS_CONFIRMATION
    
    def confirm(self, action: str) -> None:
        """Confirm an action after user approval."""
        self.analyzer.approve(action)
    
    def deny(self, action: str) -> None:
        """Deny an action."""
        self.analyzer.deny(action)