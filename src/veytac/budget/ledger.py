"""Budget reservation protocol (TRD 13.2). Integer microdollars, reserve-before-dispatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


def usd_to_micro(amount_usd: str) -> int:
    return int(Decimal(amount_usd) * 1_000_000)


def _book(payload: dict) -> dict:
    book = payload.setdefault("budget", {})
    book.setdefault("cap_micro", usd_to_micro(str(payload.get("budget_cap_usd", "3.00"))))
    book.setdefault("reserved", {})
    book.setdefault("spent_micro", 0)
    book.setdefault("unknown_micro", 0)
    book.setdefault("log", [])
    return book


def reserve_call(payload: dict, call_id: str, estimate_micro: int) -> bool:
    """Reserve-before-dispatch against the session's own book (TRD 13.2)."""
    book = _book(payload)
    committed = sum(book["reserved"].values()) + book["spent_micro"] + book["unknown_micro"]
    if estimate_micro <= 0 or committed + estimate_micro > book["cap_micro"]:
        book["log"].append(f"DENIED {call_id} need={estimate_micro}")
        return False
    book["reserved"][call_id] = estimate_micro
    book["log"].append(f"RESERVED {call_id} {estimate_micro}")
    return True


def reconcile_call(payload: dict, call_id: str, actual_micro: int | None) -> None:
    book = _book(payload)
    reserved = book["reserved"].pop(call_id, 0)
    if actual_micro is None:
        book["unknown_micro"] += reserved  # timed-out calls may still be billed
        book["log"].append(f"UNKNOWN {call_id} held={reserved}")
    else:
        book["spent_micro"] += max(actual_micro, 0)
        book["log"].append(f"RECONCILED {call_id} actual={actual_micro}")


@dataclass
class BudgetLedger:
    cap_micro: int
    reserved_micro: int = 0
    spent_micro: int = 0
    unknown_micro: int = 0
    log: list[str] = field(default_factory=list)

    @property
    def available_micro(self) -> int:
        return self.cap_micro - self.reserved_micro - self.spent_micro - self.unknown_micro

    def reserve(self, call_id: str, estimate_micro: int) -> bool:
        if estimate_micro <= 0:
            raise ValueError("estimate must be positive")
        if estimate_micro > self.available_micro:
            self.log.append(f"DENIED {call_id} need={estimate_micro}")
            return False
        self.reserved_micro += estimate_micro
        self.log.append(f"RESERVED {call_id} {estimate_micro}")
        return True

    def reconcile(self, call_id: str, reserved_micro: int, actual_micro: int | None) -> None:
        self.reserved_micro -= reserved_micro
        if actual_micro is None:
            self.unknown_micro += reserved_micro  # conservatively charged
            self.log.append(f"UNKNOWN {call_id} held={reserved_micro}")
        else:
            self.spent_micro += actual_micro
            released = reserved_micro - actual_micro
            if released < 0:
                self.spent_micro += -released
                released = 0
            self.log.append(f"RECONCILED {call_id} actual={actual_micro}")
