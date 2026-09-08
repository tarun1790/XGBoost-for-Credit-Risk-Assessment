import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.models import AuditLog
from backend.app.core.security import compute_audit_hash
from backend.app.core.rate_limiter import get_client_ip

class AuditService:
    """
    Enterprise Cryptographically Chained (SHA-256) Audit Trail Service.
    Guarantees tamper-evident immutable logging across all system actions.
    """

    @staticmethod
    async def create_log(
        db: AsyncSession,
        action: str,
        details: str,
        user_id: Optional[uuid.UUID] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Appends an audit log linked via cryptographic hash chain to the preceding entry.
        """
        # 1. Fetch previous record hash (tail of the chain)
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1)
        res = await db.execute(stmt)
        last_log = res.scalars().first()
        previous_hash = last_log.record_hash if (last_log and last_log.record_hash) else ("0" * 64)

        # 2. Extract network metadata
        ip_addr = "127.0.0.1"
        user_agent = "SYSTEM"
        if request:
            ip_addr = get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "UNKNOWN")[:255]

        # 3. Create entry attributes
        log_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # 4. Compute SHA-256 block hash
        record_hash = compute_audit_hash(
            log_id=str(log_id),
            user_id=str(user_id) if user_id else None,
            action=action,
            details=details,
            timestamp_iso=now_iso,
            ip_address=ip_addr,
            previous_hash=previous_hash
        )

        audit_entry = AuditLog(
            id=log_id,
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_addr,
            user_agent=user_agent,
            previous_hash=previous_hash,
            record_hash=record_hash,
            timestamp=now
        )

        db.add(audit_entry)
        return audit_entry

    @staticmethod
    async def verify_chain_integrity(db: AsyncSession) -> Dict[str, Any]:
        """
        Traverses all records in the audit chain in chronological order.
        Recomputes SHA-256 hashes and verifies unbroken cryptographic linkage.
        """
        stmt = select(AuditLog).order_by(AuditLog.timestamp.asc())
        res = await db.execute(stmt)
        logs = res.scalars().all()

        if not logs:
            return {
                "is_valid": True,
                "status": "EMPTY_CHAIN",
                "total_records": 0,
                "tampered_records": []
            }

        expected_prev_hash = "0" * 64
        tampered_records = []

        for idx, log in enumerate(logs):
            # If log has no hash (legacy unmigrated), link from previous
            if not log.record_hash:
                continue

            # Check previous hash link
            if log.previous_hash and log.previous_hash != expected_prev_hash and idx > 0:
                tampered_records.append({
                    "record_id": str(log.id),
                    "action": log.action,
                    "reason": "Previous hash pointer mismatch (broken link)"
                })

            # Recompute record hash
            recomputed = compute_audit_hash(
                log_id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                action=log.action,
                details=log.details,
                timestamp_iso=log.timestamp.isoformat() if hasattr(log.timestamp, "isoformat") else str(log.timestamp),
                ip_address=log.ip_address,
                previous_hash=log.previous_hash
            )

            if log.record_hash != recomputed:
                tampered_records.append({
                    "record_id": str(log.id),
                    "action": log.action,
                    "reason": "Payload hash mismatch (content tampered)"
                })

            expected_prev_hash = log.record_hash

        is_valid = len(tampered_records) == 0
        return {
            "is_valid": is_valid,
            "status": "CHAIN_INTEGRITY_VERIFIED" if is_valid else "TAMPERING_DETECTED",
            "total_records": len(logs),
            "tampered_count": len(tampered_records),
            "tampered_records": tampered_records
        }

audit_service = AuditService()
