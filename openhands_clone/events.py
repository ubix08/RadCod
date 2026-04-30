"""
OpenHands-Clone Events - Phase 2
================================
Event system for tracking agent actions and observations.

Phase 2: Event system matching SDK patterns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# =============================================================================
# Event Types
# =============================================================================

class EventType(Enum):
    """Types of events in the system."""
    MESSAGE = "message"
    OBSERVATION = "observation"
    ACTION = "action"
    THINKING = "thinking"
    ERROR = "error"
    SYSTEM = "system"


# =============================================================================
# Event Base
# =============================================================================

@dataclass
class Event:
    """Base event class."""
    
    event_type: EventType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.event_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


# =============================================================================
# Event Builders
# =============================================================================

def message_event(content: str, **metadata) -> Event:
    """Create a message event."""
    return Event(
        event_type=EventType.MESSAGE,
        content=content,
        metadata=metadata,
    )


def observation_event(content: str, **metadata) -> Event:
    """Create an observation event."""
    return Event(
        event_type=EventType.OBSERVATION,
        content=content,
        metadata=metadata,
    )


def action_event(action: str, **metadata) -> Event:
    """Create an action event."""
    return Event(
        event_type=EventType.ACTION,
        content=action,
        metadata=metadata,
    )


def thinking_event(content: str, **metadata) -> Event:
    """Create a thinking event."""
    return Event(
        event_type=EventType.THINKING,
        content=content,
        metadata=metadata,
    )


def error_event(content: str, **metadata) -> Event:
    """Create an error event."""
    return Event(
        event_type=EventType.ERROR,
        content=content,
        metadata=metadata,
    )


# =============================================================================
# Event History
# =============================================================================

class EventHistory:
    """Track event history."""
    
    def __init__(self, max_size: int = 1000):
        self._events: list[Event] = []
        self._max_size = max_size
    
    def add(self, event: Event) -> None:
        """Add an event."""
        self._events.append(event)
        if len(self._events) > self._max_size:
            self._events.pop(0)
    
    def get_all(self) -> list[Event]:
        """Get all events."""
        return self._events.copy()
    
    def get_by_type(self, event_type: EventType) -> list[Event]:
        """Get events by type."""
        return [e for e in self._events if e.event_type == event_type]
    
    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()
    
    def __len__(self) -> int:
        return len(self._events)
    
    def __iter__(self):
        return iter(self._events)