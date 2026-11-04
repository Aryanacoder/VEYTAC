"""Voice package: live speech relay + event normalization (TRD 7.4)."""

from .events import normalize_event
from .relay import MockVoiceRelay, VoiceError, VoiceRelay, build_handshake

__all__ = ["normalize_event", "MockVoiceRelay", "VoiceError", "VoiceRelay", "build_handshake"]
