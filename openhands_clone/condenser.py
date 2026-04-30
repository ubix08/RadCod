"""
OpenHands-Clone Condenser - Phase 2
===============================
Context condensation for agent memory management.

Phase 2: Condenser for condensing long conversations.
"""

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# Condenser Settings
# =============================================================================

@dataclass
class CondenserSettings:
    """Settings for context condensation."""
    
    max_tokens: int = 12000  # Maximum tokens before condensing
    min_tokens: int = 2000  # Minimum tokens after condensing
    ratio: float = 0.8  # Target ratio after condensing
    
    @classmethod
    def default(cls) -> "CondenserSettings":
        """Default settings."""
        return cls()
    
    @classmethod
    def aggressive(cls) -> "CondenserSettings":
        """Aggressive condensing - keep minimal context."""
        return cls(
            max_tokens=8000,
            min_tokens=1000,
            ratio=0.6,
        )


# =============================================================================
# Condenser
# =============================================================================

class Condenser:
    """Condense conversation history to save tokens."""
    
    def __init__(self, settings: CondenserSettings | None = None):
        self.settings = settings or CondenserSettings.default()
        self._history: list[dict] = []
        self._token_count: int = 0
    
    def add(self, message: dict) -> None:
        """Add a message to history."""
        self._history.append(message)
        # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
        self._token_count += len(str(message)) // 4
    
    def should_condense(self) -> bool:
        """Check if condensing is needed."""
        return self._token_count > self.settings.max_tokens
    
    def condense(self) -> list[dict]:
        """
        Condense history to target size.
        
        Returns condensed history.
        """
        if not self.should_condense():
            return self._history
        
        # Calculate target size
        target_tokens = int(self.settings.max_tokens * self.settings.ratio)
        
        # Keep system messages and recent messages
        condensed = []
        system_messages = []
        other_messages = []
        
        for msg in self._history:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)
        
        # Keep first system message and recent messages
        condensed.extend(system_messages[:1])  # Keep only first system message
        
        # Estimate tokens for system messages
        estimated = sum(len(str(m)) // 4 for m in condensed)
        
        # Add recent messages until target
        for msg in reversed(other_messages):
            msg_tokens = len(str(msg)) // 4
            if estimated + msg_tokens > target_tokens:
                break
            condensed.insert(1, msg)  # After system message
            estimated += msg_tokens
        
        self._history = condensed
        self._token_count = estimated
        
        return condensed
    
    def get_history(self) -> list[dict]:
        """Get current history."""
        return self._history.copy()
    
    def clear(self) -> None:
        """Clear history."""
        self._history.clear()
        self._token_count = 0
    
    def get_token_count(self) -> int:
        """Get approximate token count."""
        return self._token_count
    
    def __len__(self) -> int:
        return len(self._history)


# =============================================================================
# Summarizing Condenser
# =============================================================================

class SummarizingCondenser(Condenser):
    """Condenser that generates summaries."""
    
    def __init__(self, settings: CondenserSettings | None = None, summarize_fn: Any = None):
        super().__init__(settings)
        self._summarize_fn = summarize_fn
    
    def condense_with_summary(self) -> tuple[list[dict], str]:
        """
        Condense and generate summary.
        
        Returns (condensed_history, summary).
        """
        if not self.should_condense():
            return self._history, ""
        
        # Generate summary if function provided
        summary = ""
        if self._summarize_fn:
            # Summarize older messages
            messages_to_summarize = self._history[:-5] if len(self._history) > 5 else self._history
            summary = self._summarize_fn(messages_to_summarize)
        
        # Condense
        condensed = self.condense()
        
        return condensed, summary
    
    def set_summarize_fn(self, fn: Any) -> None:
        """Set summary generation function."""
        self._summarize_fn = fn