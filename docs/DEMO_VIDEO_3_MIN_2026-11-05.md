# VEYTAC: three-minute home demo

## The promise

“The most valuable part of skilled work is often the decision nobody wrote down. VEYTAC watches a permitted demonstration, asks the expert why a choice was made, and keeps the answer tied to the moment in the video. A human reviews the resulting knowledge before it becomes a lesson or training candidate.”

The live application is a prototype. Describe reviewed lessons and robot data as gated outputs, not guaranteed outputs from this recording. A phone recording does not contain robot actions.

## Props and setup

- Your iPhone on a stable stand, landscape if filming for a pitch. Keep the whole table in frame; use the rear camera at normal zoom.
- A mug with a handle, a small box, and two visibly different packing materials: a soft cloth and one sheet of paper. Put both materials in view.
- A laptop showing the VEYTAC session in the same local network, if you want the camera and interface in one shot. Hide notifications and private screens.
- Use the iPhone speaker at a safe volume. Make a 30-second rehearsal and confirm the opening question is audible and your spoken answer appears in the transcript. Use a real recording for the submitted video; do not dub in invented AI replies.

## Ready-to-film script and shots

| Time | Picture and action | Spoken script |
| --- | --- | --- |
| 0:00–0:20 | Tight shot of an ordinary instruction: “Pack the mug.” Cut to two materials and the mug handle. | “An instruction can tell you *what* to do. It rarely captures what an expert notices before deciding *how*. That missing judgment is what apprentices and future machines need.” |
| 0:20–0:35 | Show VEYTAC camera preview, then Start and the permissions. Check **Show model calls**. | “VEYTAC starts with permission and a live view of the work. The expert stays hands free.” |
| 0:35–1:05 | Let the real opening question play. Answer it on camera. | VEYTAC: “What kind of work are you going to do today?” You: “I’m packing this fragile mug so the handle survives shipping.” Pause until the transcript registers the answer. |
| 1:05–1:40 | Hold the mug and two materials clearly in frame. Wrap the handle in cloth; put paper in the box. Point to the handle. Keep the live overlay and model calls visible in an interface cutaway. | “This is the mug. I choose the soft cloth around the handle because that narrow joint is the weak point. The paper fills space; it is not my primary protection.” If VEYTAC asks a grounded follow-up, answer it naturally. If it asks for a closer view, show the handle. |
| 1:40–2:05 | Stop the recording. Open Library and play the actual clip. Pause where you explained the handle. | “The video remains inspectable. The answer is attached to the moment it explains. The tracked marks are visual observations, not measured force, depth, or robot actions.” |
| 2:05–2:30 | Show the model-call panel and its status/model/latency. In Library, show **Download video** and **Download session data ZIP**. | “For this hackathon, the calls are visible as they happen: which model ran, when it finished, and the available usage estimate. The owner can replay or export the private evidence.” |
| 2:30–2:50 | Show the review or dataset quality gate. Do not present blocked exports as complete. | “The system keeps proposed knowledge separate from approved knowledge. A reviewer decides what is safe to reuse. A phone video is observation data; robot policy training still requires aligned robot state and actions.” |
| 2:50–3:00 | Return to a clean view of the mug and VEYTAC mark. | “We are building the bridge from experienced human judgment to teachable, reviewable knowledge. First for people. Eventually, where the evidence supports it, for machines.” |

## Rehearsal and edit notes

1. Restart the backend after code changes. Run doctor and confirm `mode=live`; this uses the user's own paid-call configuration and budget gate. Do not run an extra provider rehearsal without that authorization.
2. Keep the real question and answer audio. Use captions for clarity, but label any screen recording or replay as replay.
3. If a model follow-up is slow or absent, continue the demonstration and show the real transcript. The opening question and expert explanation still make the core story; do not invent a question in editing.
4. Before final export, verify the Library video plays, the ZIP contains `manifest.json`, and the video has sound. Record in a quiet room with the full mug/box in frame.
