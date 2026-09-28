import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable, List, Optional
from backend.config import settings
from backend.database.connection import SessionLocal
from backend.database.models import ConnectivityStateModel
from backend.models.sync import ConnectionState, ConnectivityStatusResponse

logger = logging.getLogger(__name__)


class ConnectivityService:
    """
    Lightweight, non-blocking connectivity monitor and connection-state manager.
    Tracks state transitions (ONLINE, DEGRADED, OFFLINE, RECONNECTING, SYNCING),
    supports operator simulation overrides, and triggers synchronization on recovery.
    """

    def __init__(self):
        self._current_state = ConnectionState.ONLINE
        self._is_simulated = False
        self._reason = "System initialized in normal connected mode."
        self._last_checked = datetime.now(timezone.utc)
        self._callbacks: List[Callable[[ConnectionState, ConnectionState], None]] = []
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._init_db_state()

    def _init_db_state(self):
        """Initializes or restores the last recorded state from the database."""
        db = SessionLocal()
        try:
            latest = db.query(ConnectivityStateModel).order_by(ConnectivityStateModel.id.desc()).first()
            if latest:
                try:
                    self._current_state = ConnectionState(latest.state)
                    self._is_simulated = latest.is_simulated
                    self._reason = latest.reason
                    self._last_checked = latest.timestamp
                except ValueError:
                    self._current_state = ConnectionState.ONLINE
            else:
                initial_state = ConnectivityStateModel(
                    state="ONLINE",
                    is_simulated=False,
                    reason="Initial online state",
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(initial_state)
                db.commit()
        except Exception as e:
            logger.warning(f"Could not load initial connectivity state: {e}")
        finally:
            db.close()

    def register_callback(self, cb: Callable[[ConnectionState, ConnectionState], None]):
        """Registers a listener for connectivity state transitions."""
        if cb not in self._callbacks:
            self._callbacks.append(cb)

    @property
    def current_state(self) -> ConnectionState:
        return self._current_state

    @property
    def is_online(self) -> bool:
        return self._current_state in (ConnectionState.ONLINE, ConnectionState.RECONNECTING, ConnectionState.SYNCING)

    @property
    def is_offline(self) -> bool:
        return self._current_state in (ConnectionState.OFFLINE, ConnectionState.DEGRADED)

    def set_state(self, new_state: ConnectionState, reason: str = "", is_simulated: bool = False) -> ConnectionState:
        """Transitions connectivity state and notifies registered listeners."""
        old_state = self._current_state
        if old_state == new_state and self._is_simulated == is_simulated:
            return new_state

        self._current_state = new_state
        self._is_simulated = is_simulated
        self._reason = reason or f"Transitioned to {new_state}"
        self._last_checked = datetime.now(timezone.utc)

        # Persist state transition to database
        db = SessionLocal()
        try:
            state_record = ConnectivityStateModel(
                state=new_state.value,
                is_simulated=is_simulated,
                reason=self._reason,
                timestamp=self._last_checked
            )
            db.add(state_record)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to persist connectivity state: {e}")
        finally:
            db.close()

        logger.info(f"[CONNECTIVITY] State transition: {old_state} -> {new_state} (Simulated: {is_simulated}, Reason: {self._reason})")

        # Notify callbacks
        for cb in self._callbacks:
            try:
                cb(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in connectivity state callback: {e}")

        return new_state

    def simulate_offline(self, reason: str = "Operator simulated network loss") -> ConnectivityStatusResponse:
        """Manually overrides connection state to OFFLINE for demonstration / testing."""
        self.set_state(ConnectionState.OFFLINE, reason=reason, is_simulated=True)
        return self.get_status()

    def restore_connection(self, reason: str = "Network connectivity restored") -> ConnectivityStatusResponse:
        """Restores connectivity state to ONLINE and initiates synchronization."""
        self.set_state(ConnectionState.ONLINE, reason=reason, is_simulated=False)
        return self.get_status()

    def get_status(self) -> ConnectivityStatusResponse:
        """Returns structured connectivity status."""
        return ConnectivityStatusResponse(
            edge_id=settings.EDGE_ID,
            state=self._current_state,
            is_simulated=self._is_simulated,
            reason=self._reason,
            checked_at=self._last_checked.isoformat(),
            heartbeat_interval_seconds=settings.CONNECTIVITY_CHECK_INTERVAL,
            central_server_url="http://central-command.ibvap.internal/api"
        )


connectivity_service = ConnectivityService()
