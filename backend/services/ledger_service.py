import abc
import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.database.connection import SessionLocal
from backend.database.models import LedgerAnchorModel
from backend.services.evidence_hash_service import evidence_hash_service


class EvidenceLedger(abc.ABC):
    """Abstract interface for blockchain / immutable ledger adapters."""

    @abc.abstractmethod
    def anchor_hash(
        self,
        incident_id: str,
        evidence_id: str,
        evidence_hash: str,
        version: str = "1.0",
        hash_algorithm: str = "SHA-256",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Anchors a cryptographic evidence hash onto the ledger."""
        pass

    @abc.abstractmethod
    def get_anchor(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an anchor transaction by evidence package ID."""
        pass

    @abc.abstractmethod
    def verify_anchor(self, evidence_id: str, evidence_hash: str) -> Dict[str, Any]:
        """Checks whether the given hash matches the immutable ledger record."""
        pass

    @abc.abstractmethod
    def get_block_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the chronological ledger block chain history."""
        pass


class PrivateLedgerAdapter(EvidenceLedger):
    """
    Lightweight, cryptographic private ledger implementation for IBVAP 2.0.
    Builds an immutable, chained block structure storing transaction receipts,
    previous block hashes, and SHA-256 Merkle roots.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._is_available = True  # Can be toggled for offline/failure handling tests
        self._blocks: List[Dict[str, Any]] = []
        self._tx_counter = 0
        self._init_genesis_block()

    def _init_genesis_block(self):
        """Initializes Block #0 if not already present."""
        if not self._blocks:
            genesis_time = "2026-09-20T00:00:00Z"
            genesis_payload = {
                "block_number": 0,
                "previous_block_hash": "0" * 64,
                "transactions": [],
                "merkle_root": hashlib.sha256(b"IBVAP_GENESIS_ROOT").hexdigest(),
                "timestamp": genesis_time,
            }
            canonical_bytes = evidence_hash_service.canonicalize(genesis_payload)
            genesis_hash = hashlib.sha256(canonical_bytes).hexdigest()
            genesis_payload["block_hash"] = genesis_hash
            self._blocks.append(genesis_payload)

    def set_availability(self, available: bool):
        """Allows testing ledger failure & retry workflows."""
        with self._lock:
            self._is_available = available

    def is_available(self) -> bool:
        return self._is_available

    def _calculate_merkle_root(self, hashes: List[str]) -> str:
        """Calculates a binary Merkle root hash from transaction hashes."""
        if not hashes:
            return hashlib.sha256(b"EMPTY_BLOCK").hexdigest()
        if len(hashes) == 1:
            return hashes[0]

        current_level = hashes
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                h1 = current_level[i]
                h2 = current_level[i + 1] if i + 1 < len(current_level) else h1
                combined = hashlib.sha256((h1 + h2).encode("utf-8")).hexdigest()
                next_level.append(combined)
            current_level = next_level
        return current_level[0]

    def anchor_hash(
        self,
        incident_id: str,
        evidence_id: str,
        evidence_hash: str,
        version: str = "1.0",
        hash_algorithm: str = "SHA-256",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates an immutable ledger transaction and seals it into a new block.
        Persists both to the database and in-memory blockchain.
        """
        with self._lock:
            if not self._is_available:
                raise RuntimeError("Private Ledger is currently unavailable (Offline / Connection timeout)")

            db = SessionLocal()
            try:
                # Check for existing anchor (idempotency)
                existing = db.query(LedgerAnchorModel).filter(
                    LedgerAnchorModel.evidence_id == evidence_id,
                    LedgerAnchorModel.version == version
                ).first()

                if existing:
                    return {
                        "transaction_id": existing.transaction_id,
                        "evidence_id": existing.evidence_id,
                        "incident_id": existing.incident_id,
                        "version": existing.version,
                        "block_number": existing.block_number,
                        "block_hash": existing.block_hash,
                        "previous_block_hash": existing.previous_block_hash,
                        "anchored_hash": existing.anchored_hash,
                        "ledger_type": existing.ledger_type,
                        "timestamp": existing.timestamp.isoformat(),
                        "status": existing.status,
                    }

                # Count total transactions for deterministic ID
                total_tx = db.query(LedgerAnchorModel).count()
                tx_id = f"TX-{total_tx + 1:04d}"

                prev_block = self._blocks[-1]
                prev_block_hash = prev_block["block_hash"]
                block_number = len(self._blocks)

                tx_data = {
                    "transaction_id": tx_id,
                    "evidence_id": evidence_id,
                    "incident_id": incident_id,
                    "version": version,
                    "evidence_hash": evidence_hash,
                    "hash_algorithm": hash_algorithm,
                    "metadata": metadata or {},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                merkle_root = self._calculate_merkle_root([evidence_hash])
                block_timestamp = datetime.now(timezone.utc).isoformat()

                block_payload = {
                    "block_number": block_number,
                    "previous_block_hash": prev_block_hash,
                    "transactions": [tx_data],
                    "merkle_root": merkle_root,
                    "timestamp": block_timestamp,
                }
                block_bytes = evidence_hash_service.canonicalize(block_payload)
                block_hash = hashlib.sha256(block_bytes).hexdigest()
                block_payload["block_hash"] = block_hash

                self._blocks.append(block_payload)

                # Persist to database
                anchor_model = LedgerAnchorModel(
                    transaction_id=tx_id,
                    evidence_id=evidence_id,
                    incident_id=incident_id,
                    version=version,
                    block_number=block_number,
                    block_hash=block_hash,
                    previous_block_hash=prev_block_hash,
                    anchored_hash=evidence_hash,
                    ledger_type="PRIVATE_IMMUTABLE_LEDGER",
                    timestamp=datetime.now(timezone.utc),
                    status="CONFIRMED"
                )
                db.add(anchor_model)
                db.commit()
                db.refresh(anchor_model)

                return {
                    "transaction_id": tx_id,
                    "evidence_id": evidence_id,
                    "incident_id": incident_id,
                    "version": version,
                    "block_number": block_number,
                    "block_hash": block_hash,
                    "previous_block_hash": prev_block_hash,
                    "anchored_hash": evidence_hash,
                    "ledger_type": "PRIVATE_IMMUTABLE_LEDGER",
                    "timestamp": anchor_model.timestamp.isoformat(),
                    "status": "CONFIRMED",
                }
            finally:
                db.close()

    def get_anchor(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves anchor details by evidence ID."""
        db = SessionLocal()
        try:
            anchor = db.query(LedgerAnchorModel).filter(
                LedgerAnchorModel.evidence_id == evidence_id
            ).order_by(LedgerAnchorModel.id.desc()).first()

            if not anchor:
                return None

            return {
                "transaction_id": anchor.transaction_id,
                "evidence_id": anchor.evidence_id,
                "incident_id": anchor.incident_id,
                "version": anchor.version,
                "block_number": anchor.block_number,
                "block_hash": anchor.block_hash,
                "previous_block_hash": anchor.previous_block_hash,
                "anchored_hash": anchor.anchored_hash,
                "ledger_type": anchor.ledger_type,
                "timestamp": anchor.timestamp.isoformat(),
                "status": anchor.status,
            }
        finally:
            db.close()

    def verify_anchor(self, evidence_id: str, evidence_hash: str) -> Dict[str, Any]:
        """Compares calculated hash with anchored immutable ledger hash."""
        anchor = self.get_anchor(evidence_id)
        if not anchor:
            return {
                "status": "NOT_FOUND",
                "is_authentic": False,
                "anchored_hash": "",
                "calculated_hash": evidence_hash,
                "transaction_id": "",
                "reason": f"No ledger anchor record found for evidence ID {evidence_id}",
            }

        anchored_hash = anchor["anchored_hash"]
        is_match = (anchored_hash == evidence_hash)

        return {
            "status": "AUTHENTIC" if is_match else "TAMPERED",
            "is_authentic": is_match,
            "anchored_hash": anchored_hash,
            "calculated_hash": evidence_hash,
            "transaction_id": anchor["transaction_id"],
            "block_number": anchor["block_number"],
            "block_hash": anchor["block_hash"],
            "anchor_timestamp": anchor["timestamp"],
            "reason": "Hash matches immutable ledger record" if is_match else "Hash mismatch: off-chain evidence package was modified after anchoring",
        }

    def get_block_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns verified blocks in the chain."""
        with self._lock:
            return list(reversed(self._blocks))[:limit]


# Global singleton ledger service instance
ledger_service = PrivateLedgerAdapter()
