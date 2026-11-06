"""Server-side session management and CSRF tokens for administrator sessions."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
from typing import Dict, Optional
import uuid


@dataclass
class AdminSession:
    """Represents an active server-side administrator session."""

    session_id: str
    admin_id: uuid.UUID
    csrf_token: str
    created_at: datetime
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


class SessionStore:
    """Thread-safe in-memory session repository."""

    def __init__(self) -> None:
        self._sessions: Dict[str, AdminSession] = {}

    def create_session(
        self,
        admin_id: uuid.UUID,
        ttl_seconds: int = 86400 * 7,
    ) -> AdminSession:
        """Create and store a new secure server-side session."""
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        session = AdminSession(
            session_id=session_id,
            admin_id=admin_id,
            csrf_token=csrf_token,
            created_at=now,
            expires_at=expires_at,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: Optional[str]) -> Optional[AdminSession]:
        """Retrieve a session if present and not expired."""
        if not session_id:
            return None

        session = self._sessions.get(session_id)
        if session is None:
            return None

        if session.is_expired:
            self._sessions.pop(session_id, None)
            return None

        return session

    def invalidate_session(self, session_id: Optional[str]) -> None:
        """Remove a session from storage."""
        if session_id:
            self._sessions.pop(session_id, None)

    def invalidate_admin_sessions(self, admin_id: uuid.UUID) -> None:
        """Invalidate all active sessions for a specific administrator."""
        to_delete = [
            sid for sid, s in self._sessions.items()
            if s.admin_id == admin_id
        ]
        for sid in to_delete:
            self._sessions.pop(sid, None)

    def clear(self) -> None:
        """Clear all sessions (useful for tests)."""
        self._sessions.clear()


# Global in-memory session store instance
session_store = SessionStore()

