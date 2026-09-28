import hashlib
import json
from typing import Any, Dict, List, Union
from datetime import datetime


class EvidenceHashService:
    """
    Dedicated cryptographic hashing service for IBVAP 2.0 evidence packages.
    Ensures 100% deterministic, canonical serialization prior to SHA-256 computation.
    """

    def _normalize_value(self, val: Any) -> Any:
        """Recursively normalizes values for canonical serialization."""
        if isinstance(val, dict):
            # Exclude ephemeral / temporary keys
            cleaned = {}
            for k, v in val.items():
                if k.startswith("_") or k in ("temp_id", "$$hashKey", "ui_expanded"):
                    continue
                cleaned[str(k)] = self._normalize_value(v)
            # Return dict sorted by keys
            return {k: cleaned[k] for k in sorted(cleaned.keys())}

        elif isinstance(val, list):
            return [self._normalize_value(item) for item in val]

        elif isinstance(val, float):
            # Normalize float precision to 4 decimal places to prevent IEEE 754 platform variances
            return round(val, 4)

        elif isinstance(val, datetime):
            # Normalize datetime to UTC ISO string with trailing Z
            if val.tzinfo is None:
                return val.isoformat() + "Z"
            return val.isoformat()

        elif isinstance(val, (int, bool, str)) or val is None:
            return val

        else:
            return str(val)

    def canonicalize(self, manifest_data: Dict[str, Any]) -> bytes:
        """
        Converts a manifest dictionary into a deterministic, canonical UTF-8 byte stream.
        Applies RFC 8785 JSON Canonicalization Scheme principles:
        - Sorted keys
        - Normalized whitespace / separators (no whitespace after comma or colon)
        - Strict UTF-8 encoding
        """
        normalized = self._normalize_value(manifest_data)
        canonical_json_str = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return canonical_json_str.encode("utf-8")

    def calculate_sha256(self, canonical_bytes_or_dict: Union[bytes, str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes the SHA-256 cryptographic digest of canonical evidence data.
        Returns algorithm name, hex digest, and canonical size in bytes.
        """
        if isinstance(canonical_bytes_or_dict, dict):
            raw_bytes = self.canonicalize(canonical_bytes_or_dict)
        elif isinstance(canonical_bytes_or_dict, str):
            raw_bytes = canonical_bytes_or_dict.encode("utf-8")
        else:
            raw_bytes = canonical_bytes_or_dict

        digest = hashlib.sha256(raw_bytes).hexdigest()
        return {
            "algorithm": "SHA-256",
            "hash": digest,
            "size_bytes": len(raw_bytes)
        }


# Global singleton hash service
evidence_hash_service = EvidenceHashService()
