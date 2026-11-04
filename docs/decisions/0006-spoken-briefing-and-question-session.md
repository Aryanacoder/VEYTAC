# Decision 0006 — spoken task briefing and ongoing questions (2026-11-04)

The owner reported that the live app stayed silent, did not ask what work was
about to happen, and missed iPad/pen movements. This changes the interaction
contract from decision 0004's 30-second question window.

1. After the owner separately approves capture, external processing, and
   spoken questions, Start opens one bounded 10-minute question-ready session.
   Mute and Stop revoke the backend gate; the model cannot open or renew it.
   This is a user-approved change to the PRD/TRD **default** 30-second window.
   The consent text says to Start only where hearing a question is safe. The
   server's five-question cap and cooldown still apply. A physical-work
   release must re-evaluate safe-interruption evidence, rather than assuming
   video stillness proves safety.
2. VEYTAC immediately asks a scripted spoken task-brief question, then saves
   the expert's voice answer as session task context. The script is product
   UI, not a claim of model-generated insight. Later live Meta question
   proposals receive the task brief and preferred language. English and
   Japanese are wired through session metadata, browser TTS/ASR locale, and
   the Meta question prompt. Mandarin is labeled experimental; no universal
   language capability is claimed without device/provider evidence.
3. Starting recognition no longer cancels speech synthesis. The WebSocket
   client waits for the backend's provider `hello`, not merely the local socket
   open. The microphone AudioWorklet is connected to a zero-volume output so
   browsers process it without playing the mic. Errors are visible and browser
   speech is a fallback when the relay fails. Original-language final text
   is stored; interim text is not committed. Recognition starts only after the
   spoken prompt ends, so the app does not transcribe its own question as the
   expert's answer. Mute and Stop invalidate pending speech callbacks. A
   browser speech startup/finish watchdog returns to listening and shows a
   visible warning if speech events do not complete.
4. The bundled on-device object model has a limited class list and may not
   label an iPad, pen, or industrial tool. Event-driven frames remain, with a
   bounded 8-second context refresh so the Meta vision model can inspect
   changes that the generic detector misses. The server budget reservation and
   session cap still guard each paid call. A provider 402/502 pauses further
   frame attempts in that session rather than repeatedly charging/rejecting.

Requirement focus: FR-01, FR-02, FR-05, FR-06, FR-10, FR-11, FR-12, FR-24,
FR-28; NFR-08. Offline browser and API tests demonstrate flow, not successful
Meta speech, Japanese generation, industrial object recognition, or safe
physical-work interruption. Those remain real-session gates.
