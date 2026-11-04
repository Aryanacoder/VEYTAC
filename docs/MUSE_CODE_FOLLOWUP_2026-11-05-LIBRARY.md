# Muse Code follow-up: private library and live call receipts

Codex completed the owner-scoped recording list, one-click finalization of contiguous orphaned chunks, video and private-backup import/export, and opt-in model-call metadata panel. Backend restarted and `/api/v1/health` reports `execution_mode=live`. Verification: 74 Python unit tests, 8 Playwright tests, frontend build, and scoped Ruff check passed. No paid provider request was made in this work.

Next checks for Muse Code:

1. On the owner's iPhone Safari using the same HTTPS origin and browser cookie as the latest sessions, open Library. Confirm both latest recordings are listed by task/date. Tap **Finish video** on each, play, download video, and round-trip a private backup ZIP. Report the actual chunk count and whether playback seeks. Do not modify or expose the owner cookie.
2. Perform one authorized, bounded live session with **Show model calls** checked. Compare UI receipts to backend `model_call` rows for observation, question, SAM, and voice. Confirm model names, completion/error state, latency, and usage; no prompts, frames, audio, keys, or provider error bodies in receipts. Record the actual provider cost separately because the UI value is an estimate.
3. Investigate account-backed access across devices. Cookie-scoped access intentionally does not synchronize recordings between iPhone and laptop; private ZIP export/import is the current manual transfer path.
4. Add a media validation gate for imported MP4/WebM: the current endpoint checks container magic, size, and private permission, and attempts a stream-copy remux. It does not guarantee that every uploaded video is decodable.

Keep decisions and object labels from imported backups unreviewed; do not inherit processing/training consent. Do not turn phone observation data into robot action trajectories.
