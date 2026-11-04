import { useEffect, useRef, useState } from "react";
import { api, DecisionPayload, LessonPayload, ModelCallReceipt, ObjectLabelPayload, ObservationPayload, QuestionPayload, SavedTrackSample } from "./api/client";
import { CameraOrientation, CaptureController, SourceKind } from "./capture/recorder";
import { asrSupported, listen, Listener, primeSpeechOutput, speak, stopSpeaking } from "./dialogue/speech";
import { primeVoiceAudio, RelayVoice } from "./dialogue/streaming";
import { candidateNearHand, spokenObjectLabel } from "./dialogue/labels";
import { Library } from "./library/Library";
import { createTracker, Tracker } from "./perceive/detector";
import { FrameDesc, TrackEvent, deriveEvents, heldLabels } from "./perceive/events";
import { drawOverlay, drawSamBoxes, updateTracks, SamBox, Track } from "./perceive/overlay";
import { SamMaskPayload } from "./api/client";
import "./styles.css";

interface Turn {
  who: "ai" | "expert";
  text: string;
  at: string;
}

type SessionLanguage = "en" | "ja" | "zh";
const voiceLocale: Record<SessionLanguage, string> = { en: "en-US", ja: "ja-JP", zh: "zh-CN" };
const openingQuestion: Record<SessionLanguage, string> = {
  en: "What kind of work are you going to do today?",
  ja: "今日はどのような作業をしますか？",
  zh: "你今天要做什么工作？",
};
const briefAck: Record<SessionLanguage, string> = {
  en: "Got it. I am here with you. Show me the work, and I will ask when a choice needs context.",
  ja: "わかりました。一緒に作業を見ています。判断の理由が必要なときに質問します。",
  zh: "明白了。我会陪着你观察工作，遇到需要了解判断依据的地方就会提问。",
};
const answerAck: Record<SessionLanguage, string> = {
  en: "Thanks, that helps. I am still watching.",
  ja: "ありがとうございます。よく分かりました。引き続き見ています。",
  zh: "谢谢，这很有帮助。我会继续观察。",
};
const QUESTION_WINDOW_SECONDS = 600;

export default function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const capRef = useRef<CaptureController | null>(null);
  const streamRef = useRef<string | null>(null);
  const snapTimer = useRef<number | null>(null);
  const elapsedTimer = useRef<number | null>(null);
  const captureLimitTimer = useRef<number | null>(null);
  const captureWarningTimer = useRef<number | null>(null);
  const previewRef = useRef<MediaStream | null>(null);
  const previewPromiseRef = useRef<Promise<MediaStream | null> | null>(null);
  const recordingStartPerf = useRef(0);
  const chunkUploads = useRef<Promise<boolean>[]>([]);
  const trackingUploads = useRef<Promise<boolean>[]>([]);
  const trackingBuffer = useRef<SavedTrackSample[]>([]);
  const labelOverrideRef = useRef<Map<string, string>>(new Map());
  const pendingLabelRef = useRef<ObjectLabelPayload | null>(null);
  const lastViewPrompt = useRef(0);

  const [libraryOpen, setLibraryOpen] = useState(false);
  const [libraryIds, setLibraryIds] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem("veytac-private-sessions") ?? "[]") as string[]; }
    catch { return []; }
  });
  const [libraryRefresh, setLibraryRefresh] = useState(0);
  const [pendingLabel, setPendingLabel] = useState<ObjectLabelPayload | null>(null);

  const [showReview, setShowReview] = useState(false);
  const [showConsent, setShowConsent] = useState(false);
  const [captureConsent, setCaptureConsent] = useState(false);
  const [processingConsent, setProcessingConsent] = useState(false);
  const [questionConsent, setQuestionConsent] = useState(false);
  const [showModelCalls, setShowModelCalls] = useState(false);
  const [modelCalls, setModelCalls] = useState<ModelCallReceipt[]>([]);
  const [language, setLanguage] = useState<SessionLanguage>(() => {
    const preferred = navigator.language.toLowerCase();
    return preferred.startsWith("ja") ? "ja" : preferred.startsWith("zh") ? "zh" : "en";
  });
  const [taskBrief, setTaskBrief] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const sessionRef = useRef<string | null>(null);
  const [reviewSessionId, setReviewSessionId] = useState<string | null>(null);
  const [mode, setMode] = useState<string>("mock");
  const [capturing, setCapturing] = useState(false);
  const [previewReady, setPreviewReady] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [source, setSource] = useState<SourceKind>("camera");
  const [cameraFacing, setCameraFacing] = useState<"environment" | "user">("environment");
  const [cameraOrientation, setCameraOrientation] = useState<CameraOrientation>(
    () => window.innerHeight >= window.innerWidth ? "portrait" : "landscape",
  );
  const [captureResolution, setCaptureResolution] = useState("");
  const [muted, setMuted] = useState(false);
  const mutedRef = useRef(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [questionsOpen, setQuestionsOpen] = useState(false);
  const [support, setSupport] = useState<{ ok: boolean; reason: string } | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [observations, setObservations] = useState<ObservationPayload[]>([]);
  const observationsRef = useRef<ObservationPayload[]>([]);
  const [question, setQuestion] = useState<QuestionPayload | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [decisions, setDecisions] = useState<DecisionPayload[]>([]);
  const [episodeId, setEpisodeId] = useState<string | null>(null);
  const [lessons, setLessons] = useState<LessonPayload[]>([]);
  const [approvedScope, setApprovedScope] = useState("");
  const [reviewerId, setReviewerId] = useState("");
  const [listening, setListening] = useState(false);
  const [voiceNote, setVoiceNote] = useState<string | null>(null);
  const [trackNote, setTrackNote] = useState<string | null>(null);
  const [voiceMode, setVoiceMode] = useState<string | null>(null);
  const relayRef = useRef<RelayVoice | null>(null);
  const voiceMicRef = useRef<MediaStream | null>(null);
  const trackRef = useRef<Tracker | null>(null);
  const prevDesc = useRef<FrameDesc | null>(null);
  const overlayRef = useRef<HTMLCanvasElement | null>(null);
  const tracksRef = useRef<Track[]>([]);
  const samRef = useRef<SamBox[]>([]);
  const samFrameAtRef = useRef(0);
  const dotsRef = useRef<{ x: number; y: number }[][]>([]);
  const lastEventCheck = useRef(0);
  const prevEventDesc = useRef<FrameDesc | null>(null);
  function paintOverlay() {
    const canvas = overlayRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const w = video.clientWidth || 640;
    const h = video.clientHeight || 360;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const displayedTracks = tracksRef.current.map((track) => ({
      ...track, label: labelOverrideRef.current.get(track.key) ?? track.label,
    }));
    drawOverlay(ctx, w, h, displayedTracks, { reducedMotion: reduced, srcW: video.videoWidth || w, srcH: video.videoHeight || h, dots: dotsRef.current });
    if (samRef.current.length > 0 && Date.now() - samFrameAtRef.current < 2000 && video.videoWidth > 0) {
      drawSamBoxes(ctx, w, h, samRef.current, { w: video.videoWidth, h: video.videoHeight });
    }
    const pointed = pendingLabelRef.current;
    if (pointed?.box && pointed.localized_at_ms !== undefined &&
        performance.now() - recordingStartPerf.current - pointed.localized_at_ms < 5000 &&
        video.videoWidth && video.videoHeight) {
      const box = pointed.box;
      drawSamBoxes(ctx, w, h, [{ id: 0, label: `${pointed.label} · suggested`, kind: "object",
        x1: box.x * video.videoWidth, y1: box.y * video.videoHeight,
        x2: (box.x + box.w) * video.videoWidth, y2: (box.y + box.h) * video.videoHeight,
        frameW: video.videoWidth, frameH: video.videoHeight,
        maskSvg: pointed.mask_svg, maskH: pointed.mask_size?.[0], maskW: pointed.mask_size?.[1] }],
      { w: video.videoWidth, h: video.videoHeight });
    }
    if (pointed?.point && video.videoWidth && video.videoHeight) {
      const scale = Math.min(w / video.videoWidth, h / video.videoHeight);
      const px = (w - video.videoWidth * scale) / 2 + pointed.point.x * video.videoWidth * scale;
      const py = (h - video.videoHeight * scale) / 2 + pointed.point.y * video.videoHeight * scale;
      ctx.strokeStyle = "#ff7687";
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(px, py, 20, 0, Math.PI * 2); ctx.stroke();
      ctx.fillStyle = "#ff7687";
      ctx.font = "13px system-ui, sans-serif";
      ctx.fillText(`${pointed.label} · expert pointed`, px + 25, py - 8);
    }
  }
  const listenRef = useRef<Listener | null>(null);
  const sendTimer = useRef<number | null>(null);
  const questionRetryTimer = useRef<number | null>(null);
  const questionWindowTimer = useRef<number | null>(null);
  const lastAsk = useRef(0);
  const askingRef = useRef(false);
  const answerRef = useRef("");
  const finalTranscriptRef = useRef("");
  const speechTurnRef = useRef(0);
  const listenCycleRef = useRef(0);
  const questionRef = useRef<QuestionPayload | null>(null);
  const questionsOpenRef = useRef(false);
  answerRef.current = answerText;
  questionRef.current = question;
  questionsOpenRef.current = questionsOpen;

  function logInteraction(id: string, event: string) {
    void api.logDiagnostic(id, event).catch(() => {});
  }

  function rememberSession(id: string) {
    setLibraryIds((current) => {
      const next = [id, ...current.filter((known) => known !== id)].slice(0, 30);
      try { localStorage.setItem("veytac-private-sessions", JSON.stringify(next)); } catch { /* private mode */ }
      return next;
    });
  }

  function flushTracking(id: string) {
    const samples = trackingBuffer.current.splice(0, 12);
    if (!samples.length) return;
    const task = api.saveTracking(id, samples).then(() => true).catch((e: Error) => {
      setError(`tracking save: ${e.message}`);
      return false;
    });
    trackingUploads.current.push(task);
  }

  function handleSpokenLabel(id: string, utterance: string) {
    const label = spokenObjectLabel(utterance, language);
    if (!label) return;
    const candidate = candidateNearHand(tracksRef.current);
    const atMs = Math.max(0, Math.round(performance.now() - recordingStartPerf.current));
    void api.saveObjectLabel(id, {
      label, utterance, language, at_ms: atMs,
      localization: candidate ? "on_device_candidate" : "unlocalized",
      track_key: candidate?.key ?? null, point: null,
    }).then(async ({ label: saved }) => {
      pendingLabelRef.current = saved;
      setPendingLabel(saved);
      if (candidate) {
        labelOverrideRef.current.set(candidate.key, `${label} · expert said`);
        paintOverlay();
        setVoiceNote(`Expert called this ${label}. Highlight is a suggested match; tap the object to confirm its position.`);
      } else {
        let localized = false;
        const video = videoRef.current;
        const snap = video ? await capRef.current?.snapshot(video) : null;
        if (snap && video && sessionRef.current === id) {
          try {
            const jpeg_b64 = await new Promise<string>((resolve) => {
              const reader = new FileReader();
              reader.onload = () => resolve(String(reader.result));
              reader.readAsDataURL(snap.jpeg);
            });
            const result = await api.localizeObjectLabel(id, saved.id, {
              jpeg_b64, frame_w: snap.frame_w, frame_h: snap.frame_h,
              at_ms: Math.max(0, Math.round(snap.at_ms - recordingStartPerf.current)),
            });
            if (result.status === "candidate" && result.label.box && sessionRef.current === id) {
              pendingLabelRef.current = result.label;
              setPendingLabel(result.label);
              setVoiceNote(`Possible ${label} highlighted. This is an unreviewed visual match; tap the object to confirm.`);
              localized = true;
              paintOverlay();
            }
          } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
        }
        if (localized || sessionRef.current !== id) return;
        setVoiceNote(`Expert called this ${label}. Show it closer or from another side, or tap it in the video.`);
        if (!questionRef.current && questionsOpenRef.current && !mutedRef.current &&
            Date.now() - lastViewPrompt.current > 15000) {
          lastViewPrompt.current = Date.now();
          stopVoice();
          const prompt = language === "ja" ? `${label}を近づけて、別の角度から見せてください。`
            : language === "zh" ? `请把${label}拿近一点，再换个角度给我看。`
            : `Please hold the ${label} closer and show another side, or tap it on the video.`;
          if (!speak(prompt, voiceLocale[language], () => void startVoiceAnswer(id))) {
            void startVoiceAnswer(id);
          }
        }
      }
    }).catch((e: Error) => setError(`object label: ${e.message}`));
  }

  function handleAmbientSpeech(id: string, text: string) {
    const atMs = Math.max(0, Math.round(performance.now() - recordingStartPerf.current));
    void api.saveExpertNote(id, text, language, atMs)
      .catch((e: Error) => setError(`expert note: ${e.message}`));
    setTurns((items) => [...items, { who: "expert", text, at: new Date().toLocaleTimeString() }]);
    setAnswerText("");
    answerRef.current = "";
    finalTranscriptRef.current = "";
  }

  function pointPendingLabel(event: React.MouseEvent<HTMLVideoElement>) {
    const label = pendingLabelRef.current;
    const id = sessionRef.current;
    const video = event.currentTarget;
    if (!id || !label || !video.videoWidth || !video.videoHeight) return;
    const rect = video.getBoundingClientRect();
    const scale = Math.min(rect.width / video.videoWidth, rect.height / video.videoHeight);
    const shownW = video.videoWidth * scale;
    const shownH = video.videoHeight * scale;
    const x = (event.clientX - rect.left - (rect.width - shownW) / 2) / shownW;
    const y = (event.clientY - rect.top - (rect.height - shownH) / 2) / shownH;
    if (x < 0 || x > 1 || y < 0 || y > 1) return;
    void api.pointObjectLabel(id, label.id, { x, y,
      at_ms: Math.max(0, Math.round(performance.now() - recordingStartPerf.current)) }).then(({ label: pointed }) => {
      pendingLabelRef.current = pointed;
      setPendingLabel(pointed);
      setVoiceNote(`${pointed.label} marked by the expert. Position is a point cue, not a measured 3D pose.`);
      paintOverlay();
    }).catch((e: Error) => setError(`object point: ${e.message}`));
  }

  useEffect(() => {
    setSupport(CaptureController.support());
    api
      .health()
      .then((h) => setMode(h.execution_mode))
      .catch(() => setError("Backend unreachable — start the API (docs/HOSTING.md)."));
  }, []);

  useEffect(() => {
    let active = true;
    if (!navigator.mediaDevices?.getUserMedia) return;
    const pending = navigator.mediaDevices.getUserMedia({
      video: CaptureController.cameraVideoConstraints(cameraFacing, cameraOrientation), audio: false,
    }).then((stream) => {
      if (!active || !videoRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return null;
      }
      previewRef.current?.getTracks().forEach((track) => track.stop());
      previewRef.current = stream;
      videoRef.current.srcObject = stream;
      setPreviewReady(true);
      void videoRef.current.play().catch(() => { /* muted preview can retry on Start */ });
      return stream;
    }).catch(() => {
      if (active) setPreviewReady(false);
      return null;
    });
    previewPromiseRef.current = pending;
    return () => {
      active = false;
      previewRef.current?.getTracks().forEach((track) => track.stop());
      previewRef.current = null;
      setPreviewReady(false);
    };
  }, [cameraFacing]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const update = () => {
      setCameraOrientation(window.innerHeight >= window.innerWidth ? "portrait" : "landscape");
      if (video.videoWidth && video.videoHeight) setCaptureResolution(`${video.videoWidth}×${video.videoHeight}`);
      window.requestAnimationFrame(() => paintOverlay());
    };
    const observer = typeof ResizeObserver !== "undefined" ? new ResizeObserver(update) : null;
    observer?.observe(video);
    video.addEventListener("loadedmetadata", update);
    window.addEventListener("resize", update);
    window.addEventListener("orientationchange", update);
    update();
    return () => {
      observer?.disconnect();
      video.removeEventListener("loadedmetadata", update);
      window.removeEventListener("resize", update);
      window.removeEventListener("orientationchange", update);
    };
  }, []);

  useEffect(() => {
    const track = previewRef.current?.getVideoTracks()[0];
    if (!track || typeof track.applyConstraints !== "function") return;
    if (sessionRef.current) logInteraction(sessionRef.current,
      cameraOrientation === "portrait" ? "camera_portrait" : "camera_landscape");
    void track.applyConstraints(CaptureController.cameraFormatConstraints(cameraOrientation))
      .then(() => {
        const video = videoRef.current;
        if (video?.videoWidth && video.videoHeight) setCaptureResolution(`${video.videoWidth}×${video.videoHeight}`);
        paintOverlay();
      })
      .catch(() => {
        if (sessionRef.current) setTrackNote("Camera kept its supported frame ratio; overlay remains aligned.");
      });
  }, [cameraOrientation]);

  async function ensureSession() {
    if (sessionId) return sessionId;
    if (!captureConsent || !processingConsent || !questionConsent) throw new Error("Capture, processing, and spoken-question permissions are required for this session.");
    const { session } = await api.createSession("live-task-briefing", "LIVE_CAPTURE", language);
    await api.consent(session.id, "capture", true);
    await api.consent(session.id, "external_inference", true);
    setSessionId(session.id);
    sessionRef.current = session.id;
    return session.id as string;
  }

  function stopCapture(id: string | null) {
      if (snapTimer.current) window.clearInterval(snapTimer.current);
      if (elapsedTimer.current) window.clearInterval(elapsedTimer.current);
      if (captureLimitTimer.current) window.clearTimeout(captureLimitTimer.current);
      if (captureWarningTimer.current) window.clearTimeout(captureWarningTimer.current);
      if (questionWindowTimer.current) window.clearTimeout(questionWindowTimer.current);
      if (questionRetryTimer.current) window.clearTimeout(questionRetryTimer.current);
      questionRetryTimer.current = null;
      questionWindowTimer.current = null;
      if (id) void api.questionWindow(id, false).catch(() => {});
      if (id && questionRef.current && questionRef.current.id !== "task-brief") void api.deferQuestion(id, questionRef.current.id, "capture stopped").catch(() => {});
      setQuestionsOpen(false);
      setAnalyzing(false);
      stopVoice();
      trackRef.current?.close();
      trackRef.current = null;
      prevDesc.current = null;
      tracksRef.current = [];
      dotsRef.current = [];
      samRef.current = [];
      samFrameAtRef.current = 0;
      prevEventDesc.current = null;
      lastEventCheck.current = 0;
      { const c = overlayRef.current; c?.getContext("2d")?.clearRect(0, 0, c.width, c.height); }
      const cap = capRef.current;
      const stopped = new Promise<void>((resolve) => {
        if (!cap?.recorder || cap.recorder.state === "inactive") resolve();
        else cap.onStopped = resolve;
      });
      const preview = cap?.stop(true);
      if (id && cap && streamRef.current) {
        const streamId = streamRef.current;
        void (async () => {
          await stopped;
          flushTracking(id);
          const videoUploads = await Promise.all(chunkUploads.current);
          let videoComplete = false;
          if (cap.chunkCount > 0) {
            try {
              await api.completeRecording(id, streamId, cap.chunkCount);
              videoComplete = true;
            } catch {
              setError("Video could not be finalized. Open Library and tap Finish video to retry.");
            }
          } else {
            setError("No video chunks arrived. Check camera permission and try again.");
          }
          const trackingUploadsOk = await Promise.all(trackingUploads.current);
          if (videoComplete && trackingUploadsOk.some((ok) => !ok)) {
            setError("Video saved. Some tracking points could not be uploaded.");
          } else if (videoComplete && videoUploads.some((ok) => !ok)) {
            setError("Video saved after an upload retry. Check playback in Library.");
          }
          setLibraryRefresh((value) => value + 1);
        })();
      }
      if (preview && videoRef.current) {
        previewRef.current = preview;
        videoRef.current.srcObject = preview;
        void videoRef.current.play().catch(() => {});
        setPreviewReady(true);
      } else if (previewRef.current?.getVideoTracks().some((track) => track.readyState === "live") && videoRef.current) {
        videoRef.current.srcObject = previewRef.current;
        void videoRef.current.play().catch(() => {});
        setPreviewReady(true);
      } else if (!previewRef.current?.getVideoTracks().some((track) => track.readyState === "live")) {
        setPreviewReady(false);
      }
      capRef.current = null;
      setCapturing(false);
      setShowReview(true);
      setReviewSessionId(id);
      if (id) { rememberSession(id); setLibraryOpen(true); }
      void refreshDecisions(id);
      if (id) void api.listLessons(id).then((res) => setLessons(res.lessons ?? [])).catch(() => {});
      setQuestion(null);
      questionRef.current = null;
      setSessionId(null);
      sessionRef.current = null;
      setCaptureConsent(false);
      setProcessingConsent(false);
      setQuestionConsent(false);
  }

  async function toggleCapture(screenCapturePromise?: Promise<MediaStream>) {
    setError(null);
    if (capturing) {
      stopCapture(sessionId);
      return;
    }
    if (!captureConsent || !processingConsent || !questionConsent) {
      setShowConsent(true);
      return;
    }
    let startedSessionId: string | null = null;
    try {
      setMuted(false);
      mutedRef.current = false;
      setTurns([]);
      setObservations([]);
      setLessons([]);
      observationsRef.current = [];
      setTaskBrief("");
      chunkUploads.current = [];
      trackingUploads.current = [];
      trackingBuffer.current = [];
      labelOverrideRef.current.clear();
      pendingLabelRef.current = null;
      setPendingLabel(null);
      setQuestion(null);
      questionRef.current = null;
      setAnswerText("");
      answerRef.current = "";
      finalTranscriptRef.current = "";
      lastAsk.current = 0;
      const id = await ensureSession();
      startedSessionId = id;
      rememberSession(id);
      const { stream } = await api.registerStream(id, source, "e0", "clk_client", CaptureController.recordingMime()!);
      streamRef.current = stream.id;
      const cap = new CaptureController();
      cap.onChunk = (c) => {
        const task = api.uploadChunk(id, stream.id, c.sequence_no, "e0", c.bytes, c.started_at_ms,
          c.started_at_ms - recordingStartPerf.current, c.gap_before_ms)
          .then(() => true).catch((e: Error) => { setError(`upload: ${e.message}`); return false; });
        chunkUploads.current.push(task);
      };
      capRef.current = cap;
      const preview = source === "screen" ? null : previewRef.current ?? await previewPromiseRef.current;
      const selectedScreen = screenCapturePromise ? await screenCapturePromise : null;
      await cap.start(source, videoRef.current!, cameraFacing, preview, cameraOrientation, selectedScreen);
      recordingStartPerf.current = performance.now();
      setLibraryOpen(false);
      cap.onUnexpectedStop = (reason) => {
        if (sessionRef.current === id) { stopCapture(id); setError(reason); }
      };
      cap.stream?.getVideoTracks().forEach((track) => track.addEventListener("ended", () => {
        if (sessionRef.current === id) { stopCapture(id); setError(source === "screen"
          ? "Screen sharing ended. Recording stopped; the camera preview is available."
          : "Camera disconnected. Recording stopped; reconnect the camera to preview again."); }
      }, { once: true }));
      setCapturing(true);
      setPreviewReady(true);
      setElapsedSeconds(0);
      const startedAt = Date.now();
      elapsedTimer.current = window.setInterval(() => setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000)), 1000);
      captureWarningTimer.current = window.setTimeout(() => {
        setError("Recording will stop at the 15-minute safety limit. Camera preview will stay on.");
      }, 14 * 60 * 1000);
      captureLimitTimer.current = window.setTimeout(() => {
        stopCapture(id);
        setError("Recording stopped at the 15-minute safety limit. Camera preview remains on.");
      }, 15 * 60 * 1000);
      setShowReview(false);
      await openQuestionWindow(id);
      askOpening(id);
      prevDesc.current = null;
      // Load tracking concurrently: the frame loop below starts at once on
      // the timed fallback and upgrades to event-driven when ready.
      trackRef.current = null;
      setTrackNote("loading on-device tracker…");
      if (source === "camera") {
        void createTracker(videoRef.current!, (s) => { if (sessionRef.current === id) setTrackNote(s); }).then((t) => {
          if (sessionRef.current === id && capRef.current === cap) trackRef.current = t;
          else t.close();
        });
      } else {
        setTrackNote("Screen source · visual changes sampled for AI observation");
      }
      // Check locally once a second; request one initial model observation,
      // then send tracked changes and a bounded context refresh for small
      // tools that the generic on-device detector cannot classify.
      let lastFallback = 0;
      let lastModelFrameAt = 0;
      let lastTrackerFrameAt = 0;
      let initialModelFrameSent = false;
      let frameBusy = false;
      let providerBlocked = false;
      const keepObservation = (observation: ObservationPayload) => {
        setObservations((items) => { const next = [...items.slice(-5), observation]; observationsRef.current = next; return next; });
        if (observation.status === "failed") {
          const finding = Array.isArray(observation.findings) ? observation.findings[0] as { code?: string } : null;
          providerBlocked = true;
          setError(`Live observation paused (${finding?.code ?? "PROVIDER_INVALID"}). Recording and local tracking continue; restart after checking the provider.`);
        }
      };
      const analyzeFrame = async () => {
        if (frameBusy || sessionRef.current !== id) return;
        frameBusy = true;
        try {
        const tracker = trackRef.current;
        if (!tracker || !tracker.ready) {
          // Tracking unavailable: rare timed frame so the loop still works.
          if (providerBlocked) return;
          if (Date.now() - lastFallback < 8000) return;
          const snap = await cap.snapshot(videoRef.current!);
          if (!snap) return;
          lastFallback = Date.now();
          try {
            const dataUrl = await new Promise<string>((resolve) => {
              const reader = new FileReader();
              reader.onload = () => resolve(String(reader.result));
              reader.readAsDataURL(snap.jpeg);
            });
            setAnalyzing(true);
            if (sessionRef.current !== id) return;
            const { observation } = await api.postFrame(id, snap.at_ms, dataUrl, "timed-fallback", undefined,
              snap.at_ms - recordingStartPerf.current);
            initialModelFrameSent = true;
            lastModelFrameAt = Date.now();
            keepObservation(observation);
          } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
            if (e instanceof Error && /HTTP (402|502)/.test(e.message)) providerBlocked = true;
          } finally {
            setAnalyzing(false);
          }
          return;
        }
        let desc: FrameDesc | null = null;
        if (Date.now() - lastTrackerFrameAt < 500) return;
        lastTrackerFrameAt = Date.now();
        try {
          desc = await tracker.analyze(videoRef.current!);
        } catch (e) {
          setTrackNote(e instanceof Error ? e.message : "on-device tracker failed; using timed observations");
          trackRef.current?.close();
          trackRef.current = null;
          return;
        }
        if (!desc) return;
        tracksRef.current = updateTracks(tracksRef.current, desc, Date.now());
        dotsRef.current = desc.handPoints ?? [];
        paintOverlay();
        trackingBuffer.current.push({
          at_ms: Math.max(0, Math.round(performance.now() - recordingStartPerf.current)),
          frame_w: videoRef.current?.videoWidth || 1,
          frame_h: videoRef.current?.videoHeight || 1,
          tracks: tracksRef.current.filter((track) => Date.now() - track.updatedMs < 1000)
            .map((track) => ({ key: track.key, kind: track.kind,
              label: labelOverrideRef.current.get(track.key) ?? track.label, box: track.box })),
          hand_points: dotsRef.current,
        });
        if (trackingBuffer.current.length >= 4) flushTracking(id);
        const held = heldLabels(desc);
        setTrackNote(
          `seeing: ${desc.hands.length} hand(s)` +
            (held.length > 0 ? `, holding ${held.join(", ")}` : "") +
            ` · ${desc.objects.length} supported object(s)`,
        );
        prevDesc.current = desc;
        // Overlay/tracking run at full cadence; paid model frames fire at most
        // once per second, on tracked changes or motion bursts.
        let events: TrackEvent[] = [];
        const initialFrame = prevEventDesc.current === null;
        if (initialFrame || Date.now() - lastEventCheck.current >= 1000) {
          events = deriveEvents(prevEventDesc.current, desc);
          prevEventDesc.current = desc;
          lastEventCheck.current = Date.now();
        }
        const refreshDue = Date.now() - lastModelFrameAt >= 8000;
        if (providerBlocked) return;
        if (events.length === 0 && (!initialFrame || initialModelFrameSent) && !refreshDue) return;
        const snap = await cap.snapshot(videoRef.current!);
        if (!snap) return;
        try {
          const dataUrl = await new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(String(reader.result));
            reader.readAsDataURL(snap.jpeg);
          });
          const trigger = initialFrame && !initialModelFrameSent ? "initial-scene" : events.length === 0 ? "periodic-context" : events
            .map((e) => (e.label ? `${e.type}:${e.label}` : e.type))
            .join(",");
          const vw = snap.frame_w;
          const vh = snap.frame_h;
          const prompts = tracksRef.current.slice(0, 10).map((t, i) => ({
            id: i, label: t.label, x: t.box.x, y: t.box.y, w: t.box.w, h: t.box.h,
          }));
          setAnalyzing(true);
          if (sessionRef.current !== id) return;
          const res = await api.postFrame(id, snap.at_ms, dataUrl, trigger,
            vw > 0 && vh > 0 && prompts.length > 0 ? { w: vw, h: vh, prompts } : undefined,
            snap.at_ms - recordingStartPerf.current);
          initialModelFrameSent = true;
          lastModelFrameAt = Date.now();
          keepObservation(res.observation);
          samRef.current = (res.masks ?? []).map((m: SamMaskPayload) => ({
            id: m.object_id, label: m.label,
            kind: m.label === "person" || m.label === "hand" ? "human" : "object",
            x1: m.box.x1, y1: m.box.y1, x2: m.box.x2, y2: m.box.y2,
            frameW: m.frame_w, frameH: m.frame_h, confidence: m.confidence,
            maskSvg: m.decoded ? m.svg : null, maskW: m.mask?.w, maskH: m.mask?.h,
          }));
          samFrameAtRef.current = Date.now();
          paintOverlay();
          if (res.sam_error) setTrackNote((t) => t ? `${t} SAM: ${res.sam_error}` : `SAM: ${res.sam_error}`);
          else if (samRef.current.length > 0) setTrackNote((t) => t ? `${t} SAM: ${samRef.current.length} mask(s)` : `SAM: ${samRef.current.length} mask(s)`);
        } catch (e) {
          setError(e instanceof Error ? e.message : String(e));
          if (e instanceof Error && /HTTP (402|502)/.test(e.message)) providerBlocked = true;
        } finally {
          setAnalyzing(false);
        }
        } finally {
          frameBusy = false;
        }
      };
      void analyzeFrame();
      snapTimer.current = window.setInterval(() => void analyzeFrame(), 250);
    } catch (e) {
      if (elapsedTimer.current) window.clearInterval(elapsedTimer.current);
      if (captureLimitTimer.current) window.clearTimeout(captureLimitTimer.current);
      if (captureWarningTimer.current) window.clearTimeout(captureWarningTimer.current);
      if (snapTimer.current) window.clearInterval(snapTimer.current);
      if (questionWindowTimer.current) window.clearTimeout(questionWindowTimer.current);
      if (startedSessionId) void api.questionWindow(startedSessionId, false).catch(() => {});
      setQuestionsOpen(false);
      const preview = capRef.current?.stop(true);
      if (screenCapturePromise) void screenCapturePromise.then((shared) => shared.getTracks().forEach((track) => track.stop())).catch(() => {});
      if (preview && videoRef.current) {
        previewRef.current = preview;
        videoRef.current.srcObject = preview;
        setPreviewReady(true);
      } else if (previewRef.current?.getVideoTracks().some((track) => track.readyState === "live") && videoRef.current) {
        videoRef.current.srcObject = previewRef.current;
        void videoRef.current.play().catch(() => {});
        setPreviewReady(true);
      }
      capRef.current = null;
      setCapturing(false);
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  function beginSelectedCapture() {
    if (!captureConsent || !processingConsent || !questionConsent) {
      void toggleCapture();
      return;
    }
    if (source === "screen") {
      const check = CaptureController.screenSupport();
      if (!check.ok) { setError(check.reason); return; }
      try {
        // getDisplayMedia must start in the user's click, before API awaits.
        const display = navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
        void display.catch(() => {});
        void toggleCapture(display);
      } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
      return;
    }
    void toggleCapture();
  }

  async function openQuestionWindow(id: string) {
    await api.questionWindow(id, true, QUESTION_WINDOW_SECONDS);
    setQuestionsOpen(true);
    if (questionWindowTimer.current) window.clearTimeout(questionWindowTimer.current);
    questionWindowTimer.current = window.setTimeout(() => {
      setQuestionsOpen(false);
      questionWindowTimer.current = null;
      setVoiceNote("Question permission ended. Tap Start when it is safe to hear more questions.");
    }, QUESTION_WINDOW_SECONDS * 1000);
  }

  function askOpening(id: string) {
    setVoiceNote(null);
    const prompt: QuestionPayload = {
      id: "task-brief", gap_id: "task-brief", wording: openingQuestion[language], status: "delivered",
    };
    questionRef.current = prompt;
    setQuestion(prompt);
    setTurns((turns) => [...turns, { who: "ai", text: prompt.wording, at: new Date().toLocaleTimeString() }]);
    speakThenListen(id, prompt.wording);
  }

  function speakThenListen(id: string, wording: string) {
    stopListening();
    const turn = ++speechTurnRef.current;
    logInteraction(id, "tts_requested");
    const startAfterSpeech = (outcome: "ended" | "error" | "timeout" = "ended") => {
      if (speechTurnRef.current === turn && sessionRef.current === id && !mutedRef.current && questionRef.current) {
        logInteraction(id, outcome === "ended" ? "tts_ended" : outcome === "timeout" ? "tts_timeout" : "tts_error");
        if (outcome !== "ended") setVoiceNote("Phone audio did not finish. The question is on screen; starting voice input.");
        void startVoiceAnswer(id);
      }
    };
    if (!speak(wording, voiceLocale[language], startAfterSpeech, () => logInteraction(id, "tts_started"))) {
      startAfterSpeech("error");
    }
  }

  function acknowledgeAndListen(id: string, wording: string) {
    if (sessionRef.current !== id || mutedRef.current) return;
    const turn = ++speechTurnRef.current;
    setTurns((items) => [...items, { who: "ai", text: wording, at: new Date().toLocaleTimeString() }]);
    stopListening();
    const resume = () => {
      if (sessionRef.current === id && !mutedRef.current && speechTurnRef.current === turn && !questionRef.current) {
        void startVoiceAnswer(id);
      }
    };
    if (!speak(wording, voiceLocale[language], resume, () => logInteraction(id, "tts_started"))) resume();
  }

  async function refreshDecisions(id: string | null = sessionId) {
    if (!id) return;
    try {
      const { decisions } = await api.listDecisions(id);
      setDecisions(decisions);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function toggleMute() {
    if (!sessionId || !capturing) return;
    const next = !muted;
    try {
      await api.questionWindow(sessionId, !next, QUESTION_WINDOW_SECONDS);
      capRef.current?.stream?.getAudioTracks().forEach((track) => { track.enabled = !next; });
      if (next) {
        stopVoice();
        if (questionRef.current && questionRef.current.id !== "task-brief") {
          void api.deferQuestion(sessionId, questionRef.current.id, "expert muted").catch(() => {});
          questionRef.current = null;
          setQuestion(null);
          setAnswerText("");
          answerRef.current = "";
        }
        questionRef.current = null;
        setQuestion(null);
      }
      setMuted(next);
      mutedRef.current = next;
      setQuestionsOpen(!next);
      if (questionWindowTimer.current) window.clearTimeout(questionWindowTimer.current);
      questionWindowTimer.current = next ? null : window.setTimeout(() => {
        setQuestionsOpen(false);
        questionWindowTimer.current = null;
        setVoiceNote("Question permission ended. Tap Start when it is safe to hear more questions.");
      }, QUESTION_WINDOW_SECONDS * 1000);
      setVoiceNote(next ? "Muted. Recording continues without microphone audio or questions." : "Listening again. I’ll ask when an observation reveals a gap.");
      if (!next && !taskBrief) askOpening(sessionId);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  function stopListening() {
    listenCycleRef.current += 1;
    listenRef.current?.stop();
    listenRef.current = null;
    relayRef.current?.stop();
    relayRef.current = null;
    voiceMicRef.current?.getTracks().forEach((track) => track.stop());
    voiceMicRef.current = null;
    setListening(false);
    if (sendTimer.current) window.clearTimeout(sendTimer.current);
  }

  function stopVoice() {
    speechTurnRef.current += 1;
    stopListening();
    stopSpeaking();
  }

  function armAutoSend() {
    if (sendTimer.current) window.clearTimeout(sendTimer.current);
    sendTimer.current = window.setTimeout(() => void submitAnswer(), 1500);
  }

  async function startVoiceAnswer(id: string | null = sessionRef.current) {
    if (!id) return;
    stopListening();
    const listenCycle = listenCycleRef.current;
    finalTranscriptRef.current = "";
    // Relay first: server-side Meta live ASR over the session socket.
    let mic = capRef.current?.stream ?? null;
    const recordedMic = mic?.getAudioTracks()[0];
    if (!recordedMic) logInteraction(id, "mic_missing");
    if (recordedMic?.muted || recordedMic?.readyState === "ended") {
      logInteraction(id, "mic_muted");
      try {
        voiceMicRef.current = await navigator.mediaDevices.getUserMedia({ audio: {
          echoCancellation: true, noiseSuppression: true,
        }, video: false });
        mic = voiceMicRef.current;
      } catch {
        setVoiceNote("Microphone went silent after audio playback. Check the phone microphone permission.");
      }
    }
    if (sessionRef.current !== id || mutedRef.current || listenCycleRef.current !== listenCycle) {
      voiceMicRef.current?.getTracks().forEach((track) => track.stop());
      voiceMicRef.current = null;
      return;
    }
    if (mic && mic.getAudioTracks().some((track) => track.readyState === "live" && !track.muted)) {
      logInteraction(id, "asr_relay_connecting");
      const relay = new RelayVoice(id, {
        onPartial: (text) => { answerRef.current = text; setAnswerText(text); },
        onFinal: (text) => {
          if (!text.trim()) return;
          logInteraction(id, "asr_final");
          handleSpokenLabel(id, text);
          if (questionRef.current) {
            answerRef.current = text;
            setAnswerText(text);
            armAutoSend();
          } else {
            handleAmbientSpeech(id, text);
          }
        },
        onNote: (msg) => setVoiceNote(msg),
        onError: (msg) => { logInteraction(id, "asr_relay_failed"); setVoiceNote(`Voice relay: ${msg}`); },
        onAudioFrame: () => logInteraction(id, "asr_audio_started"),
        onClosed: () => {
          relayRef.current = null;
          if (sessionRef.current === id && !mutedRef.current) startListening();
        },
      });
      if (await relay.start(mic)) {
        if (sessionRef.current !== id || mutedRef.current || listenCycleRef.current !== listenCycle) {
          relay.stop();
          return;
        }
        relayRef.current = relay;
        logInteraction(id, "asr_relay_ready");
        setVoiceMode("relay");
        setListening(true);
        setVoiceNote(null);
        return;
      }
    }
    if (sessionRef.current !== id || mutedRef.current || listenCycleRef.current !== listenCycle) return;
    setVoiceMode("browser");
    startListening(); // browser speech fallback if the relay did not confirm readiness
  }

  function startListening() {
    if (!asrSupported()) {
      if (sessionRef.current) logInteraction(sessionRef.current, "asr_browser_failed");
      setVoiceNote("Voice input unavailable. Use Chrome/Edge or reconnect the voice relay.");
      return;
    }
    listenRef.current?.stop();
    const handle = listen(
      (interim) => {
        const next = `${finalTranscriptRef.current} ${interim}`.trim();
        answerRef.current = next;
        setAnswerText(next);
      },
      (final) => {
        const id = sessionRef.current;
        if (!id || !final.trim()) return;
        handleSpokenLabel(id, final);
        if (questionRef.current) {
          const next = `${finalTranscriptRef.current} ${final}`.trim();
          finalTranscriptRef.current = next;
          answerRef.current = next;
          setAnswerText(next);
          armAutoSend();
        } else {
          handleAmbientSpeech(id, final);
        }
      },
      (message) => {
        if (sessionRef.current) logInteraction(sessionRef.current, "asr_browser_failed");
        setVoiceNote(message);
      },
      voiceLocale[language],
    );
    if (handle) {
      if (sessionRef.current) logInteraction(sessionRef.current, "asr_browser_started");
      listenRef.current = handle;
      setListening(true);
      setVoiceNote(null);
    }
  }

  async function askNext() {
    if (!sessionId || !questionsOpen || askingRef.current || questionRef.current || muted || !taskBrief) return;
    const cooldownRemaining = 45000 - (Date.now() - lastAsk.current);
    if (cooldownRemaining > 0) {
      if (questionRetryTimer.current) window.clearTimeout(questionRetryTimer.current);
      questionRetryTimer.current = window.setTimeout(() => {
        questionRetryTimer.current = null;
        void askNext();
      }, cooldownRemaining + 250);
      return;
    }
    askingRef.current = true;
    setError(null);
    try {
      logInteraction(sessionId, "question_propose_requested");
      const prop = await api.proposeQuestion(sessionId);
      const q = prop.question;
      if (!q) {
        logInteraction(sessionId, "question_propose_empty");
        // Genuinely nothing grounded yet — say why instead of staying silent.
        setVoiceNote(prop.reason ? `No question yet: ${prop.reason}` : "No question yet.");
        return;
      }
      // The server's question window uses Unix wall-clock milliseconds.
      const res = await api.deliverQuestion(sessionId, q.id, Date.now());
      if (!res.delivered) {
        logInteraction(sessionId, "question_held");
        // The human gate held it (window/cooldown/cap) — show its reason.
        setVoiceNote(res.reason ? `Held: ${res.reason}` : "Held by question gate.");
        return;
      }
      const delivered = res.question ?? q;
      logInteraction(sessionId, "question_delivered");
      lastAsk.current = Date.now();
      questionRef.current = delivered;
      setQuestion(delivered);
      setVoiceNote(null);
      setTurns((t) => [...t, { who: "ai", text: delivered.wording, at: new Date().toLocaleTimeString() }]);
      speakThenListen(sessionId, delivered.wording);
    } catch (e) {
      logInteraction(sessionId, "question_error");
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      askingRef.current = false;
    }
  }

  // Auto-ask: every new observation while the window is open and free.
  useEffect(() => {
    if (questionsOpen && !muted && !question && taskBrief && observations.length > 0 && sessionId) {
      void askNext();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionsOpen, muted, question, taskBrief, observations[observations.length - 1]?.id, sessionId]);

  async function submitAnswer() {
    const activeQuestion = questionRef.current;
    const text = answerRef.current.trim();
    const id = sessionRef.current;
    if (!id || !activeQuestion || !text) return;
    stopVoice();
    try {
    if (activeQuestion.id === "task-brief") {
      await api.setTaskBrief(id, text);
      setTaskBrief(text);
      setTurns((turns) => [...turns, { who: "expert", text, at: new Date().toLocaleTimeString() }]);
      setAnswerText("");
      answerRef.current = "";
      finalTranscriptRef.current = "";
      setQuestion(null);
      questionRef.current = null;
      setVoiceNote("Watching for a decision worth asking about.");
      if (sessionRef.current === id && !mutedRef.current) acknowledgeAndListen(id, briefAck[language]);
      return;
    }
    await api.answerQuestion(id, activeQuestion.id, text, language);
    setTurns((t) => [...t, { who: "expert", text, at: new Date().toLocaleTimeString() }]);
    setAnswerText("");
    answerRef.current = "";
    finalTranscriptRef.current = "";
    const latestObservation = observationsRef.current[observationsRef.current.length - 1];
    const { decision } = await api.createDecision(id, {
      task_id: "live-task-briefing",
      observed_action_description: latestObservation?.description ?? "action under review",
      observation_id: latestObservation?.id,
      expert_original_statement: text,
      scope_description: "",
    });
    setDecisions((d) => [...d, decision]);
    setQuestion(null);
    questionRef.current = null;
    if (sessionRef.current === id && !mutedRef.current) acknowledgeAndListen(id, answerAck[language]);
    // A later observation can trigger another question only inside a newly
    // approved window. Do not queue a stale question after the window expires.
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setVoiceNote("Could not save the spoken answer. Tap Start to retry.");
    }
  }

  async function approve(recordId: string) {
    if (!approvedScope.trim() || !reviewerId.trim()) return;
    try {
      const { decision } = await api.reviewDecision(recordId, "approve", reviewerId.trim(), approvedScope.trim());
      setDecisions((d) => d.map((x) => (x.record_id === recordId ? decision : x)));
      setApprovedScope("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function finishEpisode() {
    if (!reviewSessionId) return;
    try {
      const { episode } = await api.assembleEpisode(reviewSessionId);
      setEpisodeId(episode.episode_id);
      const { lesson } = await api.buildLesson(episode.episode_id);
      setLessons((items) => [lesson, ...items]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    if (!capturing || !showModelCalls || !sessionId) {
      setModelCalls([]);
      return;
    }
    let active = true;
    const refresh = () => void api.modelCalls(sessionId).then(({ calls }) => {
      if (active) setModelCalls(calls);
    }).catch(() => {});
    refresh();
    const timer = window.setInterval(refresh, 1200);
    return () => { active = false; window.clearInterval(timer); };
  }, [capturing, showModelCalls, sessionId]);

  const latestObservation = observations[observations.length - 1];
  return (
    <main className={`live-app ${capturing ? "is-capturing" : ""} ${previewReady ? "has-preview" : ""} ${libraryOpen && !capturing ? "library-open" : ""}`}>
      <div className="live-stage">
        <video ref={videoRef} className="live-video" muted playsInline onClick={pointPendingLabel} />
        <canvas ref={overlayRef} className="detect-overlay" aria-hidden="true" />
        {!capturing && <div className="standby">
          <div className="standby-orbit" aria-hidden="true"><span /><span /></div>
          <div className="standby-content">
            <span className="standby-eyebrow"><span className="eyebrow-line" /> {previewReady ? "CAMERA PREVIEW · NOT RECORDING" : "THE LIVE APPRENTICE"}</span>
            <div className="standby-emblem"><img src="/veytac-logo.svg" alt="VEYTAC" /></div>
            <h1>Observe the work.<br /><em>Preserve the why.</em></h1>
            <p>Give VEYTAC the task context, then let it watch and ask while you work.</p>
          </div>
        </div>}
        {capturing && <div className={`observation-scan ${analyzing ? "analyzing" : ""}`} aria-hidden="true"><span /></div>}
        <div className="stage-shade" aria-hidden="true" />
        {capturing && <div className="viewfinder" aria-hidden="true"><span /><span /><span /><span /></div>}

        <header className="live-header">
          <div className="brand-lockup"><img src="/veytac-logo.svg" alt="VEYTAC" className="brand-logo" /><span>EXPERTISE, IN MOTION</span></div>
          {!capturing && <button type="button" className="library-trigger" onClick={() => setLibraryOpen((open) => !open)}>{libraryOpen ? "Camera" : "Library"}</button>}
          <div className="live-metadata">{capturing && <label className="model-calls-toggle"><input type="checkbox" checked={showModelCalls} onChange={(event) => setShowModelCalls(event.target.checked)} /> Show model calls</label>}<span className="mode-tag">{mode.toUpperCase()} MODE</span><span className={`live-indicator ${capturing ? "on" : ""}`}>{capturing ? `REC ${String(Math.floor(elapsedSeconds / 60)).padStart(2, "0")}:${String(elapsedSeconds % 60).padStart(2, "0")}${captureResolution ? ` · ${captureResolution}` : ""}` : previewReady ? "PREVIEW" : "READY"}</span></div>
        </header>

        {capturing && showModelCalls && <aside className="model-calls-panel" aria-label="Live model calls"><strong>MODEL CALLS <span>{mode === "live" ? "LIVE METADATA" : "MOCK MODE"}</span></strong>{modelCalls.length === 0 ? <p>{mode === "live" ? "Waiting for the first provider call…" : "No provider calls in mock mode."}</p> : modelCalls.slice(0, 5).map((call) => <div key={call.id} className="model-call-row"><span>{call.kind} · {call.status}</span><small>{call.model}</small><small>{call.latency_ms == null ? "In progress" : `${(call.latency_ms / 1000).toFixed(1)} s`}{call.usage?.total_tokens ? ` · ${call.usage.total_tokens} tokens` : ""}{call.cost_estimate_micro != null ? ` · ~$${(call.cost_estimate_micro / 1_000_000).toFixed(4)}` : ""}</small></div>)}</aside>}

        <div className="observation-label" role="status">
          <span className={`signal-dot ${capturing ? "on" : ""}`} />
          <div className="observation-copy"><strong>{capturing ? (analyzing ? "Analyzing this moment" : muted ? "Recording · muted" : source === "screen" ? "Observing the screen" : "Observing the work") : previewReady ? source === "screen" ? "Screen selected · not recording" : "Camera preview · not recording" : "Ready to observe"}</strong>
          {capturing && trackNote && <small>{trackNote}{voiceMode ? ` · voice ${voiceMode}` : ""}</small>}</div>
          {!capturing && !libraryOpen && <button type="button" className="source-switch" onClick={() => setSource((current) => current === "camera" ? "screen" : "camera")}>Source: {source === "camera" ? "Camera" : "Screen"} ↔</button>}
        </div>
        {capturing && (question || turns.length === 0) && latestObservation?.status === "proposed" && <p className="observed-evidence" aria-live="polite"><strong>{latestObservation.execution_mode === "live" ? "AI observation · unreviewed" : "MOCK observation"}</strong><span>{latestObservation.description}</span>{(latestObservation.objects?.length ?? 0) > 0 && <small>Visible objects: {latestObservation.objects!.join(", ")}</small>}</p>}

        {question && <section className="spoken-question" aria-live="assertive"><div className="question-eyebrow"><span className="question-pulse" />VEYTAC ASKS<span className="question-rule" /></div><p>{question.wording}</p>{listening && <small className="listening-state">Listening to your answer…</small>}{voiceNote && <small className="voice-status">{voiceNote}</small>}{answerText && <blockquote>{answerText}</blockquote>}<div className="question-actions"><button type="button" onClick={() => { if (sessionRef.current) speakThenListen(sessionRef.current, question.wording); }}>Hear question</button><button type="button" onClick={() => { stopVoice(); if (asrSupported()) { setVoiceMode("browser"); startListening(); } else void startVoiceAnswer(); }}>Listen now</button></div></section>}
        {!question && capturing && <p className="waiting-line">{voiceNote ?? "Watching for the next decision…"}</p>}
        {!capturing && !showReview && <p className="waiting-line">Start to describe your work and let VEYTAC observe it.</p>}
        {capturing && !questionsOpen && !muted && !question && <p className="question-gate-note">Tap Start when it is safe to hear more questions.</p>}

        {capturing && <p className="detect-legend"><span className="swatch human" />person / hand<span className="swatch object" />object</p>}
        {capturing && pendingLabel && <p className="expert-label-cue">Expert said “{pendingLabel.label}” · {pendingLabel.localization === "expert_pointed" ? "point marked" : "tap the object to mark its position"}</p>}
        <div className="glass-controls" aria-label="Live controls">
          <button className="glass-button" disabled={capturing || source === "screen"} title="Switch front/rear camera" aria-pressed={cameraFacing === "user"} onClick={() => setCameraFacing((f) => (f === "environment" ? "user" : "environment"))}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9a8 8 0 0 1 14-3l2 2M20 15a8 8 0 0 1-14 3l-2-2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /><path d="M20 4v4h-4M4 20v-4h4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg><span>{cameraFacing === "environment" ? "Rear" : "Front"}</span></button>
          <button className="glass-button primary" disabled={!!support && !support.ok} title={capturing ? "Allow questions for up to 10 minutes" : "Start capture"} onClick={() => {
            if (capturing && sessionId) void openQuestionWindow(sessionId).then(() => {
              if (questionRef.current && !listening) {
                speakThenListen(sessionId, questionRef.current.wording);
              }
            }).catch((e: Error) => setError(e.message));
            else beginSelectedCapture();
          }}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 5 11 7-11 7V5Z" fill="currentColor" /></svg><span>Start</span></button>
          <button className="glass-button" disabled={!capturing} onClick={() => void toggleCapture()}><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" /></svg><span>Stop</span></button>
          <button className={`glass-button ${muted ? "muted" : ""}`} disabled={!capturing} aria-pressed={muted} onClick={() => void toggleMute()}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15.5a3.5 3.5 0 0 0 3.5-3.5V6a3.5 3.5 0 1 0-7 0v6a3.5 3.5 0 0 0 3.5 3.5Zm6-3.5a6 6 0 0 1-12 0M12 18v3m-4 0h8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />{muted && <path d="m4 4 16 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />}</svg><span>{muted ? "Unmute" : "Mute"}</span></button>
        </div>
        {showConsent && <div className="consent-backdrop"><section className="consent-panel" role="dialog" aria-modal="true" aria-labelledby="consent-title"><span>BEFORE WE BEGIN</span><h2 id="consent-title">Observe with permission</h2><p>VEYTAC records {source === "screen" ? "the window or screen you select and your microphone" : "camera and microphone input"}. Selected frames go to the configured model provider; spoken answers may use its voice relay or your browser’s speech service. {source === "screen" ? "Choose a window without secrets, private messages, or unauthorized material. " : ""}Start only when it is safe to hear questions; Mute or Stop revokes permission. No training or publication permission is requested here.</p><label className="language-choice">Question and answer language<select value={language} onChange={(e) => setLanguage(e.target.value as SessionLanguage)}><option value="en">English</option><option value="ja">日本語 · Japanese</option><option value="zh">中文 · Mandarin (experimental)</option></select></label><label><input type="checkbox" checked={captureConsent} onChange={(e) => setCaptureConsent(e.target.checked)} /> I approve this session’s {source === "screen" ? "screen and microphone" : "camera and microphone"} capture.</label><label><input type="checkbox" checked={processingConsent} onChange={(e) => setProcessingConsent(e.target.checked)} /> I approve external processing for this session.</label><label><input type="checkbox" checked={questionConsent} onChange={(e) => setQuestionConsent(e.target.checked)} /> I allow spoken questions for up to 10 minutes while I can safely hear them.</label><label><input type="checkbox" checked={showModelCalls} onChange={(e) => setShowModelCalls(e.target.checked)} /> Show model calls on screen (metadata only).</label><div><button onClick={() => setShowConsent(false)}>Cancel</button><button disabled={!captureConsent || !processingConsent || !questionConsent} onClick={() => { primeVoiceAudio(); primeSpeechOutput(voiceLocale[language]); setShowConsent(false); beginSelectedCapture(); }}>Start session</button></div></section></div>}
      </div>

      {libraryOpen && !capturing && <Library ids={libraryIds} refresh={libraryRefresh} onImport={rememberSession} onBack={() => setLibraryOpen(false)} />}
      {(error || (support && !support.ok)) && <div className="live-notice" role="alert">{error ?? support?.reason}</div>}

      {!question && turns.length > 0 && <section className="dialogue-rail" aria-label="Live transcript">{turns.slice(-4).map((t, i) => <p key={`${t.at}-${i}`} className={t.who}><strong>{t.who === "ai" ? "VEYTAC" : "EXPERT"}</strong><span>{t.text}</span></p>)}</section>}

      {showReview && <section className="after-session" aria-label="Review captured knowledge"><div><h2>Session complete</h2><p>Review the expert’s statements and enter the scope you can approve. Recording is off; camera preview stays on.</p></div><div className="review-items">{decisions.length === 0 ? <p>No answered questions yet.</p> : decisions.map((d) => <article key={d.record_id}><span>{d.review.state}</span><p>{d.expert_original_statement}</p>{d.review.state !== "approved" && <div className="review-action"><label>Reviewer ID<input value={reviewerId} onChange={(e) => setReviewerId(e.target.value)} placeholder="Your review ID" /></label><label>Approved scope<input value={approvedScope} onChange={(e) => setApprovedScope(e.target.value)} placeholder="Where this explanation applies" /></label><button disabled={!reviewerId.trim() || !approvedScope.trim()} onClick={() => void approve(d.record_id)}>Approve this record</button></div>}</article>)}</div>{decisions.some((d) => d.review.state === "approved") && <button className="episode-button" onClick={() => void finishEpisode()}>Build episode + lesson</button>}{episodeId && <p>Episode {episodeId}</p>}{lessons.map((lesson) => <article className="lesson-card" key={lesson.id}><span>REVIEWED LEARNING CARD</span><h3>{lesson.title}</h3>{lesson.checkpoints.map((checkpoint, index) => <section key={index}><h4>{checkpoint.prompt}</h4><p><strong>Approved distinction:</strong> {checkpoint.expected_distinction}</p><p><strong>Expert said:</strong> {checkpoint.explanation}</p></section>)}<small>{lesson.limitations.join(" · ")}</small></article>)}</section>}
    </main>
  );
}
