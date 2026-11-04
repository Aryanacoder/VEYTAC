import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import { api, DatasetQuality, ObjectLabelPayload, OwnedRecording, PostprocessRun, RecordingInfo, RobotDatasetStatus, SavedSamMask, SavedTrackSample } from "../api/client";
import { drawOverlay, drawSamBoxes, Track } from "../perceive/overlay";

interface Props {
  ids: string[];
  refresh: number;
  onImport(id: string): void;
  onBack(): void;
  review?: ReactNode;
}

export function Library({ ids, refresh, onImport, onBack, review }: Props) {
  const [tab, setTab] = useState<"videos" | "robots" | "ai">("videos");
  const [selected, setSelected] = useState(ids[0] ?? "");
  const [owned, setOwned] = useState<OwnedRecording[]>([]);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importAllowed, setImportAllowed] = useState(false);
  const [importing, setImporting] = useState(false);
  const [info, setInfo] = useState<RecordingInfo | null>(null);
  const [samples, setSamples] = useState<SavedTrackSample[]>([]);
  const [labels, setLabels] = useState<ObjectLabelPayload[]>([]);
  const [dataset, setDataset] = useState<RobotDatasetStatus | null>(null);
  const [quality, setQuality] = useState<DatasetQuality | null>(null);
  const [masks, setMasks] = useState<SavedSamMask[]>([]);
  const [postprocess, setPostprocess] = useState<PostprocessRun | null>(null);
  const [rightsOrigin, setRightsOrigin] = useState("");
  const [rightsConfirmed, setRightsConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [mediaRatio, setMediaRatio] = useState(16 / 9);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => { if (ids[0]) setSelected(ids[0]); }, [ids[0]]);

  useEffect(() => {
    let active = true;
    void api.ownedRecordings().then(({ recordings }) => {
      if (!active) return;
      const available = Array.isArray(recordings) ? recordings : [];
      setOwned(available);
      setSelected((current) => available.some((entry) => entry.id === current)
        ? current : available[0]?.id ?? current);
    }).catch(() => {});
    return () => { active = false; };
  }, [refresh]);

  useEffect(() => {
    if (!selected) return;
    let active = true;
    setLoading(true);
    setError(null);
    setPostprocess(null);
    Promise.allSettled([
      api.recordingInfo(selected), api.getTracking(selected),
      api.getObjectLabels(selected), api.robotDataset(selected),
      api.datasetQuality(selected), api.getMasks(selected),
    ]).then(([recording, tracks, objectLabels, robot, report, savedMasks]) => {
      if (!active) return;
      setInfo(recording.status === "fulfilled" ? recording.value : null);
      setSamples(tracks.status === "fulfilled" && Array.isArray(tracks.value.samples) ? tracks.value.samples : []);
      setLabels(objectLabels.status === "fulfilled" && Array.isArray(objectLabels.value.labels) ? objectLabels.value.labels : []);
      setDataset(robot.status === "fulfilled" ? robot.value : null);
      setQuality(report.status === "fulfilled" && report.value?.gates && report.value?.evidence ? report.value : null);
      setMasks(savedMasks.status === "fulfilled" && Array.isArray(savedMasks.value?.masks) ? savedMasks.value.masks : []);
      if (recording.status === "rejected") {
        const reason = recording.reason instanceof Error ? recording.reason.message : "";
        setError(reason.includes("403")
          ? "This recording belongs to another browser or predates private library access. New recordings appear here automatically."
          : "Recording is not ready or its chunks are missing.");
      }
      setLoading(false);
    });
    return () => { active = false; };
  }, [selected, refresh]);

  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    const draw = () => {
      const width = video.clientWidth;
      const height = video.clientHeight;
      if (!width || !height) return;
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width; canvas.height = height;
      }
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const atMs = video.currentTime * 1000;
      let lo = 0; let hi = samples.length;
      while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (samples[mid].at_ms <= atMs) lo = mid + 1;
        else hi = mid;
      }
      const sample = samples[lo - 1];
      const visible = sample && atMs - sample.at_ms <= 1200;
      const tracks: Track[] = visible ? sample.tracks.map((track) => ({
        ...track, trail: [], updatedMs: sample.at_ms,
      })) : [];
      drawOverlay(ctx, width, height, tracks, {
        srcW: visible ? sample.frame_w : video.videoWidth,
        srcH: visible ? sample.frame_h : video.videoHeight,
        dots: visible ? sample.hand_points : [], showTrails: false,
      });
      let mask: SavedSamMask | undefined;
      for (const item of masks) {
        if (item.recording_elapsed_ms > atMs) break;
        mask = item;
      }
      if (mask && atMs - mask.recording_elapsed_ms >= 1600) mask = undefined;
      if (mask?.box) drawSamBoxes(ctx, width, height, [{
        id: mask.object_id, label: `${mask.label} · SAM ${mask.execution_mode}`,
        kind: "object", x1: mask.box.x1, y1: mask.box.y1,
        x2: mask.box.x2, y2: mask.box.y2,
        frameW: mask.frame_w, frameH: mask.frame_h,
        maskSvg: mask.decoded ? mask.svg : null,
        maskH: mask.mask_size?.[0], maskW: mask.mask_size?.[1],
      }], { w: mask.frame_w, h: mask.frame_h });
      const suggested = labels.find((label) => label.box && label.localized_at_ms !== undefined &&
        atMs >= label.localized_at_ms && atMs - label.localized_at_ms < 4000);
      if (suggested?.box && video.videoWidth && video.videoHeight) {
        const box = suggested.box;
        drawSamBoxes(ctx, width, height, [{ id: 0, label: `${suggested.label} · suggested`, kind: "object",
          x1: box.x * video.videoWidth, y1: box.y * video.videoHeight,
          x2: (box.x + box.w) * video.videoWidth, y2: (box.y + box.h) * video.videoHeight,
          frameW: video.videoWidth, frameH: video.videoHeight,
          maskSvg: suggested.mask_svg, maskH: suggested.mask_size?.[0],
          maskW: suggested.mask_size?.[1] }],
        { w: video.videoWidth, h: video.videoHeight });
      }
      const cue = labels.find((label) => label.point && atMs >= (label.point_at_ms ?? label.at_ms) &&
        atMs - (label.point_at_ms ?? label.at_ms) < 4000);
      if (cue?.point && video.videoWidth && video.videoHeight) {
        const scale = Math.min(width / video.videoWidth, height / video.videoHeight);
        const x = (width - video.videoWidth * scale) / 2 + cue.point.x * video.videoWidth * scale;
        const y = (height - video.videoHeight * scale) / 2 + cue.point.y * video.videoHeight * scale;
        ctx.strokeStyle = "#ff7687"; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(x, y, 20, 0, 2 * Math.PI); ctx.stroke();
        ctx.fillStyle = "#ff7687"; ctx.font = "13px system-ui";
        ctx.fillText(`${cue.label} · expert pointed`, x + 25, y - 8);
      }
    };
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(draw);
    observer?.observe(video);
    video.addEventListener("timeupdate", draw);
    video.addEventListener("seeked", draw);
    video.addEventListener("loadedmetadata", draw);
    draw();
    return () => {
      observer?.disconnect();
      video.removeEventListener("timeupdate", draw);
      video.removeEventListener("seeked", draw);
      video.removeEventListener("loadedmetadata", draw);
    };
  }, [selected, info, samples, labels, masks, tab]);

  async function grantTrainingUse() {
    if (!selected) return;
    try {
      await api.consent(selected, "training", true);
      setDataset(await api.robotDataset(selected));
      setQuality(await api.datasetQuality(selected));
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }

  async function declareRights() {
    if (!selected || !rightsConfirmed || rightsOrigin.trim().length < 3) return;
    try {
      await api.declareSourceRights(selected, rightsOrigin.trim(), "session owner declaration");
      setQuality(await api.datasetQuality(selected));
      setRightsConfirmed(false);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }

  async function assembleReviewQueue() {
    if (!selected) return;
    try {
      const result = await api.runPostprocess(selected);
      setPostprocess(result.postprocess);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }

  async function finishVideo() {
    if (!selected || !info?.stream_id || !info.chunk_count) return;
    try {
      setLoading(true);
      await api.completeRecording(selected, info.stream_id, info.chunk_count);
      setInfo(await api.recordingInfo(selected));
      setOwned((await api.ownedRecordings()).recordings);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? `Could not finish video: ${e.message}` : "Could not finish video.");
    } finally { setLoading(false); }
  }

  async function importSelectedVideo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!importFile || !importAllowed) return;
    try {
      setImporting(true);
      const { recording } = await api.importVideo(importFile);
      onImport(recording.id);
      setSelected(recording.id);
      setOwned((await api.ownedRecordings()).recordings);
      setTab("videos");
      setImportFile(null);
      setImportAllowed(false);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setImporting(false); }
  }

  const recordings = owned.length ? owned : ids.map((id) => ({
    id, created_at: null, title: "Work recording", source_type: "unknown",
    chunk_count: 0, size_bytes: 0, complete: false, duration_ms: null,
  }));

  const rightsForm = quality && !quality.source_rights.declared && <div className="dataset-permission">
    <p>Inspect and redact this recording before training. Declare that you own its content or have permission for private model training, including material visible on screen or camera.</p>
    <input aria-label="Source origin" value={rightsOrigin} onChange={(event) => setRightsOrigin(event.target.value)} placeholder="Source origin or owner" />
    <label><input type="checkbox" checked={rightsConfirmed} onChange={(event) => setRightsConfirmed(event.target.checked)} /> I own this content or have permission to use it for private model training.</label>
    <button disabled={!rightsConfirmed || rightsOrigin.trim().length < 3} onClick={() => void declareRights()}>Record source rights</button>
  </div>;

  return <section className="library-shell" aria-label="VEYTAC library">
    <div className="library-top"><button type="button" onClick={onBack}>← Camera</button><div><h1>Captured work</h1><p>Private recordings and attributed research data.</p></div></div>
    <nav className="library-tabs" aria-label="Library sections">
      <button className={tab === "videos" ? "active" : ""} onClick={() => setTab("videos")}>Video library</button>
      <button className={tab === "robots" ? "active" : ""} onClick={() => setTab("robots")}>Robot dataset</button>
      <button className={tab === "ai" ? "active" : ""} onClick={() => setTab("ai")}>AI dataset</button>
    </nav>
    <div className="library-layout">
      <aside className="library-sessions" aria-label="Your recordings">
        <h2>Your recordings <span>{recordings.length}</span></h2>
        {recordings.length === 0 && <p>No recording here yet. Start a session or import a video below.</p>}
        {recordings.map((entry) => <button key={entry.id} className={selected === entry.id ? "selected" : ""} onClick={() => setSelected(entry.id)}>
          <span>{entry.title}</span><small>{entry.created_at ? new Date(entry.created_at).toLocaleString() : "Saved recording"} · {entry.source_type} · {entry.complete ? "Ready" : entry.chunk_count ? "Finish video" : "No video yet"}</small>
        </button>)}
        <form className="library-import" onSubmit={(event) => void importSelectedVideo(event)}>
          <label htmlFor="import-video">Import video or VEYTAC backup</label>
          <input id="import-video" type="file" accept=".mp4,.webm,.zip,video/mp4,video/webm,application/zip" onChange={(event) => setImportFile(event.target.files?.[0] ?? null)} />
          <label className="import-consent"><input type="checkbox" checked={importAllowed} onChange={(event) => setImportAllowed(event.target.checked)} /> I have permission to store this file privately.</label>
          <button type="submit" disabled={!importFile || !importAllowed || importing}>{importing ? "Importing…" : "Import file"}</button>
        </form>
      </aside>
      <div className="library-detail">
        {loading && <p className="library-state">Loading this session…</p>}
        {error && <p className="library-error" role="alert">{error}</p>}
        {!selected && <p className="library-state">Select a recording to review it.</p>}
        {selected && tab === "videos" && <>
          <div className="library-detail-heading"><div><h2>Recorded demonstration</h2><p>{info ? `${info.chunk_count} chunks · ${(info.size_bytes / 1024 / 1024).toFixed(1)} MB · ${info.complete ? "upload complete" : "completion unverified"}${info.replay_duration_ms ? ` · ${(info.replay_duration_ms / 1000).toFixed(1)} s` : ""}` : "Waiting for recorded media"}</p></div></div>
          {info && <div className="replay-frame" style={{ aspectRatio: mediaRatio, width: mediaRatio < 1 ? "min(100%, 420px)" : "100%" }}><video key={selected} ref={videoRef} controls playsInline preload="metadata" src={`/api/v1/sessions/${selected}/recording`} onLoadedMetadata={(event) => {
            const video = event.currentTarget;
            if (video.videoWidth && video.videoHeight) setMediaRatio(video.videoWidth / video.videoHeight);
          }} /><canvas ref={canvasRef} aria-hidden="true" /></div>}
          {info && <div className="recording-actions">
            {!info.complete && <button type="button" disabled={loading} onClick={() => void finishVideo()}>{loading ? "Finishing…" : "Finish video"}</button>}
            <a href={`/api/v1/sessions/${selected}/recording`} download={`veytac-recording.${info.mime?.startsWith("video/mp4") ? "mp4" : "webm"}`}>Download video</a>
            <a href={`/api/v1/sessions/${selected}/backup/download`} download="veytac-session-backup.zip">Download session data ZIP</a>
          </div>}
          {info && !info.complete && <p className="library-state">The video chunks are saved. Tap Finish video to make playback seekable and confirm the recording.</p>}
          {info && samples.length === 0 && <p className="library-state">This recording has no saved tracking samples. Video playback is available without an overlay.</p>}
          {info && samples.length > 0 && <p className="library-evidence">{samples.length} on-device tracking samples. Boxes and hand points are image observations; they are not measured depth or robot motion.</p>}
          {masks.length > 0 && <p className="library-evidence">{masks.length} time aligned SAM mask candidates. Shaded outlines appear at sampled moments; they need review.</p>}
          <div className="library-labels"><h3>Expert object labels <span>{labels.length}</span></h3>
            {labels.length === 0 ? <p>No object label was spoken in this session.</p> : labels.map((label) => <button key={label.id} onClick={() => { if (videoRef.current) videoRef.current.currentTime = label.at_ms / 1000; }}><strong>{label.label}</strong><span>{(label.at_ms / 1000).toFixed(1)} s · {label.localization.replace(/_/g, " ")} · unreviewed</span></button>)}
          </div>
          {review}
        </>}
        {selected && tab === "robots" && <>
          <div className="library-detail-heading"><div><h2>Observation dataset</h2><p>Evidence for perception research, with robot-policy gaps shown explicitly.</p></div></div>
          <div className="dataset-facts"><div><span>Video</span><strong>{dataset ? `${(dataset.video_bytes / 1024 / 1024).toFixed(1)} MB` : "—"}</strong></div><div><span>Track samples</span><strong>{dataset?.tracking_samples ?? "—"}</strong></div><div><span>Expert labels</span><strong>{dataset?.expert_labels ?? "—"}</strong></div></div>
          <div className="dataset-gate"><strong>Action-policy training: blocked</strong><p>A phone video has no measured robot states, actions, calibration, or action alignment. The export preserves those fields as missing; it does not invent them.</p><small>Missing: {dataset?.missing_for_action_policy?.join(" · ") ?? "robot state · action · calibration · alignment"}</small></div>
          {quality && <div className="dataset-gate"><strong>Target: {quality.target_robot_format}</strong><p>Current ZIP format: {quality.gates.visual_ai.format}</p><p>Visual AI: {quality.gates.visual_ai.status}. {quality.gates.visual_ai.reasons.join("; ") || "Local evidence checks passed; model-specific validation remains."}</p><small>{quality.evidence.timed_chunks}/{quality.evidence.chunk_count} chunks timed · {quality.evidence.live_observations} live observations · {quality.evidence.decoded_sam_masks} decoded masks</small></div>}
          {dataset?.training_permission ? <p className="library-evidence">Private training use permitted for this session. No public release or training job has started.</p> : <div className="dataset-permission"><p>Recording consent does not grant dataset training use. Approve this session separately to download its private observation package.</p><button onClick={() => void grantTrainingUse()}>Allow private training dataset use</button></div>}
          {rightsForm}
          {dataset?.training_permission && dataset.recording_complete && quality?.source_rights.declared && <a className="dataset-download" href={`/api/v1/sessions/${selected}/robot-dataset/download`} download>Download observation dataset ZIP</a>}
          {dataset && !dataset.recording_complete && <p className="library-state">The recording must finish uploading before its dataset can be exported.</p>}
        </>}
        {selected && tab === "ai" && <>
          <div className="library-detail-heading"><div><h2>Reviewed AI data</h2><p>Private, source linked decisions for a future specialist model.</p></div></div>
          {quality ? <>
            <div className="dataset-facts"><div><span>Source</span><strong>{quality.source_type}</strong></div><div><span>Expert turns</span><strong>{quality.evidence.dialogue_turns}</strong></div><div><span>Approved records</span><strong>{quality.evidence.approved_latest_decisions}</strong></div></div>
            <div className="dataset-gate"><strong>Reviewed examples: {quality.gates.reviewed_sft.status}</strong><p>{quality.gates.reviewed_sft.reasons.join("; ") || "Candidate examples only. Validate a session separated train and validation split and target model before training."}</p><small>{quality.gates.reviewed_sft.format}</small></div>
            <div className="dataset-gate"><strong>Code agent harness: {quality.gates.code_agent_harness.status}</strong><p>{quality.gates.code_agent_harness.reasons.join("; ")}</p></div>
            <div className="dataset-facts">{quality.postprocess_stages.map((stage) => <div key={stage.role}><span>{stage.role.replace(/_/g, " ")}</span><strong>{stage.status}</strong></div>)}</div>
            <div className="dataset-permission"><p>Assemble local evidence and unanswered items into a review queue. This makes no model calls.</p><button onClick={() => void assembleReviewQueue()}>Assemble review queue</button></div>
            {postprocess && <div className="dataset-gate"><strong>{postprocess.review_queue.length} items need review</strong><p>{postprocess.review_queue.slice(0, 8).map((item) => `${item.kind}: ${item.reason}`).join("; ") || "No open items in this session."}</p><small>{postprocess.approved_grounded_record_ids.length} grounded approved records · {postprocess.execution_mode} · {postprocess.model_calls} model calls</small></div>}
            {!quality.evidence.training_permission && <div className="dataset-permission"><p>Approve private training use separately from recording consent.</p><button onClick={() => void grantTrainingUse()}>Allow private training dataset use</button></div>}
            {rightsForm}
            {quality.gates.reviewed_sft.status === "CANDIDATE" && <a className="dataset-download" href={`/api/v1/sessions/${selected}/ai-dataset/download`} download>Download reviewed JSONL</a>}
          </> : <p className="library-state">Quality report unavailable for this session.</p>}
        </>}
      </div>
    </div>
  </section>;
}
