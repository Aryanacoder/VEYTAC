/* Capture layer (TRD 3): screen OR camera source, 2s chunk cadence.
   Chunks are stored locally for the demo slice; server upload lands in S4b.
   Real timestamps preserved; gaps marked, never interpolated. */

export type SourceKind = "screen" | "camera";
export type CameraOrientation = "portrait" | "landscape";

export interface ChunkMeta {
  sequence_no: number;
  started_at_ms: number; // performance.now() epoch of this capture clock
  mime: string;
  bytes: Blob;
  gap_before_ms: number | null; // >tolerance means a discontinuity
}

const CHUNK_MS = 2000;
const GAP_TOLERANCE_MS = 600;

export class CaptureController {
  stream: MediaStream | null = null;
  recorder: MediaRecorder | null = null;
  source: SourceKind | null = null;
  private seq = 0;
  private lastStop = 0;
  private stopping = false;
  private borrowedVideoTrack: MediaStreamTrack | null = null;
  onChunk: (c: ChunkMeta) => void = () => {};
  onGap: (gapMs: number) => void = () => {};
  onUnexpectedStop: (reason: string) => void = () => {};
  onStopped: () => void = () => {};

  get chunkCount(): number { return this.seq; }

  static support(): { ok: boolean; reason: string } {
    const md = navigator.mediaDevices;
    if (!md || typeof md.getUserMedia !== "function") {
      return {
        ok: false,
        reason:
          "Camera/mic unavailable: this page is not a secure context. " +
          "Open it via http://localhost on this PC, or trusted LAN HTTPS " +
          "on your phone/tablet (see docs/HOSTING.md).",
      };
    }
    if (typeof MediaRecorder === "undefined" || !CaptureController.recordingMime()) {
      return { ok: false, reason: "This browser cannot record camera video. Use a current Safari, Chrome, or Edge." };
    }
    return { ok: true, reason: "" };
  }

  static screenSupport(): { ok: boolean; reason: string } {
    if (!navigator.mediaDevices?.getDisplayMedia) {
      return { ok: false, reason: "Screen sharing is unavailable in this browser. Use a desktop browser that supports screen capture." };
    }
    return CaptureController.support();
  }

  static recordingMime(): string | null {
    if (typeof MediaRecorder === "undefined") return null;
    return ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm", "video/mp4"]
      .find((mime) => MediaRecorder.isTypeSupported(mime)) ?? null;
  }

  static cameraFormatConstraints(orientation: CameraOrientation): MediaTrackConstraints {
    return orientation === "portrait"
      ? { width: { ideal: 720 }, height: { ideal: 1280 }, aspectRatio: { ideal: 9 / 16 } }
      : { width: { ideal: 1280 }, height: { ideal: 720 }, aspectRatio: { ideal: 16 / 9 } };
  }

  static cameraVideoConstraints(facing: "environment" | "user", orientation: CameraOrientation): MediaTrackConstraints {
    return { facingMode: { ideal: facing }, ...CaptureController.cameraFormatConstraints(orientation) };
  }

  async start(
    source: SourceKind,
    preview: HTMLVideoElement,
    facing: "environment" | "user" = "environment",
    previewStream?: MediaStream | null,
    orientation: CameraOrientation = "landscape",
    selectedScreenStream?: MediaStream | null,
  ): Promise<void> {
    const check = source === "screen" ? CaptureController.screenSupport() : CaptureController.support();
    if (!check.ok) throw new Error(check.reason);
    this.stop();
    this.stopping = false;
    this.source = source;
    const usableVideo = previewStream?.getVideoTracks().find((track) => track.readyState === "live");
    if (source === "camera" && usableVideo) {
      const mic = await navigator.mediaDevices.getUserMedia({ audio: {
        echoCancellation: true, noiseSuppression: true,
      } });
      this.borrowedVideoTrack = usableVideo;
      mic.getVideoTracks().forEach((track) => { if (track !== usableVideo) track.stop(); });
      this.stream = new MediaStream([usableVideo, ...mic.getAudioTracks()]);
      preview.srcObject = previewStream ?? new MediaStream([usableVideo]);
    } else if (source === "screen") {
      const display = selectedScreenStream ?? await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
      const videoTrack = display.getVideoTracks()[0];
      if (!videoTrack || videoTrack.readyState !== "live") throw new Error("Screen sharing ended before recording began.");
      const mic = await navigator.mediaDevices.getUserMedia({ audio: {
        echoCancellation: true, noiseSuppression: true,
      }, video: false });
      display.getAudioTracks().forEach((track) => track.stop());
      this.borrowedVideoTrack = null;
      this.stream = new MediaStream([videoTrack, ...mic.getAudioTracks()]);
      preview.srcObject = this.stream;
    } else {
      this.borrowedVideoTrack = null;
      this.stream = await navigator.mediaDevices.getUserMedia({ video: CaptureController.cameraVideoConstraints(facing, orientation), audio: {
        echoCancellation: true, noiseSuppression: true,
      } });
      preview.srcObject = this.stream;
    }
    const playback = preview.play().catch(() => {});
    if (!preview.videoWidth) {
      await Promise.race([
        playback,
        new Promise<void>((resolve) => window.setTimeout(resolve, 5000)),
      ]);
    }
    if (!preview.videoWidth) throw new Error("Camera opened but no video frames arrived. Check camera permission and try again.");
    const mime = CaptureController.recordingMime();
    if (!mime) throw new Error("No supported camera recording format found.");
    this.seq = 0;
    this.lastStop = performance.now();
    this.recorder = new MediaRecorder(this.stream, {
      mimeType: mime,
      videoBitsPerSecond: 1_500_000,
    });
    this.recorder.ondataavailable = (ev: BlobEvent) => {
      if (!ev.data || ev.data.size === 0) return;
      const now = performance.now();
      const sinceLast = now - this.lastStop;
      const gap = sinceLast - CHUNK_MS > GAP_TOLERANCE_MS ? sinceLast - CHUNK_MS : null;
      if (gap !== null) this.onGap(gap);
      this.onChunk({
        sequence_no: this.seq++,
        started_at_ms: now,
        mime,
        bytes: ev.data,
        gap_before_ms: gap,
      });
      this.lastStop = now;
    };
    this.recorder.onstop = () => {
      this.onStopped();
      if (!this.stopping) this.onUnexpectedStop("Recording stopped unexpectedly. Camera preview remains available.");
    };
    this.recorder.onerror = () => this.onUnexpectedStop("The browser recorder failed. Camera preview remains available.");
    // Local recording of the full stream (owner requirement 9): keep every
    // timeslice blob so the complete stream is saved, not only samples.
    this.recorder.start(CHUNK_MS);
  }

  snapshot(preview: HTMLVideoElement): Promise<{ at_ms: number; jpeg: Blob; frame_w: number; frame_h: number } | null> {
    if (!preview.videoWidth) return Promise.resolve(null);
    const canvas = document.createElement("canvas");
    canvas.width = Math.min(preview.videoWidth, 1280);
    canvas.height = Math.round((canvas.width * preview.videoHeight) / preview.videoWidth);
    canvas.getContext("2d")?.drawImage(preview, 0, 0, canvas.width, canvas.height);
    const at_ms = performance.now();
    return new Promise((resolve) => {
      canvas.toBlob((b) => resolve(b ? { at_ms, jpeg: b, frame_w: canvas.width, frame_h: canvas.height } : null), "image/jpeg", 0.8);
    });
  }

  stop(keepCameraPreview = false): MediaStream | null {
    this.stopping = true;
    try {
      if (this.recorder?.state !== "inactive") this.recorder?.stop();
    } catch {
      /* already stopped */
    }
    const video = this.source === "camera" && (keepCameraPreview || this.borrowedVideoTrack)
      ? this.stream?.getVideoTracks().filter((t) => t.readyState === "live") ?? []
      : [];
    this.stream?.getTracks().forEach((track) => { if (!video.includes(track)) track.stop(); });
    const preview = video.length ? new MediaStream(video) : null;
    this.recorder = null;
    this.stream = null;
    this.borrowedVideoTrack = null;
    this.source = null;
    return preview;
  }
}
