const BASE = "";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new Error(
      `${init?.method ?? "GET"} ${path}: unreachable — is the backend on :8000 running?`,
    );
  }
  if (!res.ok) {
    const body = (await res.text()).slice(0, 200);
    throw new Error(`${init?.method ?? "GET"} ${path}: HTTP ${res.status} — ${body}`);
  }
  return (await res.json()) as T;
}

export interface SessionPayload {
  id: string;
  task_id: string;
  mode: string;
  lifecycle: string;
  questions_allowed: boolean;
  [k: string]: unknown;
}

export interface QuestionPayload {
  id: string;
  gap_id: string;
  wording: string;
  status: string;
  [k: string]: unknown;
}

export interface ObservationPayload {
  id: string;
  description: string;
  objects?: string[];
  status: string;
  execution_mode: string;
  [k: string]: unknown;
}

export interface SamMaskPayload {
  id: string;
  object_id: number;
  label: string;
  box: { x1: number; y1: number; x2: number; y2: number; w: number; h: number };
  frame_w: number;
  frame_h: number;
  svg: string | null;
  rle: unknown;
  mask?: { w: number; h: number; x?: number; y?: number };
  decoded: boolean;
  confidence?: number;
}

export interface TrackPrompt {
  id: number;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface SavedTrackSample {
  at_ms: number;
  frame_w: number;
  frame_h: number;
  tracks: Array<{ key: string; kind: "human" | "object"; label: string;
    box: { x: number; y: number; w: number; h: number } }>;
  hand_points: Array<Array<{ x: number; y: number }>>;
}

export interface ObjectLabelPayload {
  id: string;
  label: string;
  utterance: string;
  language: string;
  at_ms: number;
  localization: "unlocalized" | "on_device_candidate" | "sam_candidate" | "expert_pointed";
  track_key?: string | null;
  point?: { x: number; y: number } | null;
  point_at_ms?: number;
  box?: { x: number; y: number; w: number; h: number } | null;
  localized_at_ms?: number;
  mask_svg?: string | null;
  mask_size?: [number, number] | null;
  review_state: string;
}

export interface RecordingInfo {
  session_id: string;
  stream_id: string;
  source_type?: string;
  mime: string;
  chunk_count: number;
  size_bytes: number;
  complete: boolean;
  replay_duration_ms?: number | null;
  seekable?: boolean;
  tracking_samples: number;
  object_labels: number;
}

export interface OwnedRecording {
  id: string;
  created_at: string | null;
  title: string;
  source_type: string;
  chunk_count: number;
  size_bytes: number;
  complete: boolean;
  duration_ms: number | null;
}

export interface ModelCallReceipt {
  id: string;
  kind: string;
  provider: string;
  model: string;
  status: "running" | "completed" | "error";
  started_at: string;
  latency_ms: number | null;
  usage: Record<string, number> | null;
  estimated_cost_micro: number | null;
  cost_estimate_micro: number | null;
}

export interface RobotDatasetStatus {
  session_id: string;
  kind: "observation_only";
  training_permission: boolean;
  recording_complete: boolean;
  video_bytes: number;
  tracking_samples: number;
  expert_labels: number;
  action_policy_ready: false;
  missing_for_action_policy: string[];
}

export interface DatasetQuality {
  source_type: string;
  target_robot_format: string;
  source_rights: { declared: boolean; basis: string | null; origin: string | null };
  evidence: { recording_complete: boolean; seekable: boolean; video_bytes: number;
    chunk_count: number; timed_chunks: number; recording_gap_count: number;
    live_observations: number; mock_or_failed_observations: number;
    sam_masks: number; decoded_sam_masks: number; tracking_samples: number;
    expert_labels: number; dialogue_turns: number; approved_latest_decisions: number;
    grounded_approved_decisions: number;
    training_permission: boolean };
  gates: Record<string, { status: string; reasons: string[]; format: string }>;
  postprocess_stages: Array<{ role: string; status: string }>;
}

export interface SavedSamMask extends SamMaskPayload {
  recording_elapsed_ms: number;
  mask_size: [number, number];
  execution_mode: string;
}

export interface PostprocessRun {
  source_digest: string;
  execution_mode: "deterministic_local";
  model_calls: number;
  review_queue: Array<{ kind: string; id: string; reason: string; at_ms?: number;
    recording_elapsed_ms?: number }>;
  approved_grounded_record_ids: string[];
}

export interface DecisionPayload {
  record_id: string;
  revision: number;
  observed_action_description: string;
  expert_original_statement: string;
  review: { state: string };
  [k: string]: unknown;
}

export interface LessonPayload {
  id: string;
  title: string;
  task_context: string;
  checkpoints: Array<{ prompt: string; expected_distinction: string; explanation: string }>;
  limitations: string[];
}

export const api = {
  logDiagnostic: (sessionId: string, event: string) =>
    req<{ accepted: boolean }>(`/api/v1/sessions/${sessionId}/diagnostics`, {
      method: "POST", body: JSON.stringify({ event }),
    }),
  health: () => req<{ status: string; execution_mode: string }>("/api/v1/health"),
  createSession: (task_id: string, mode = "LIVE_CAPTURE", language = "en") =>
    req<{ session: SessionPayload }>("/api/v1/sessions", {
      method: "POST",
      body: JSON.stringify({ task_id, mode, languages: [language] }),
    }),
  setTaskBrief: (sessionId: string, text: string) =>
    req<{ task_brief: string }>(`/api/v1/sessions/${sessionId}/task-brief`, {
      method: "POST", body: JSON.stringify({ text }),
    }),
  consent: (sessionId: string, purpose: string, grant = true) =>
    req(`/api/v1/sessions/${sessionId}/consents`, {
      method: "POST",
      body: JSON.stringify({ actor_id: "usr_owner", purpose, grant }),
    }),
  questionWindow: (sessionId: string, allow: boolean, duration_s = 30) =>
    req(`/api/v1/sessions/${sessionId}/question-window`, {
      method: "POST",
      body: JSON.stringify({ actor_id: "usr_owner", allow, duration_s }),
    }),
  registerStream: (sessionId: string, source_type: string, epoch_id: string, clock_id: string, codec: string) =>
    req<{ stream: { id: string } }>(`/api/v1/sessions/${sessionId}/streams`, {
      method: "POST",
      body: JSON.stringify({ source_type, epoch_id, clock_id, codec }),
    }),
  uploadChunk: async (
    sessionId: string,
    streamId: string,
    seq: number,
    epoch: string,
    blob: Blob,
    intervalEndMs: number,
    recordingElapsedMs?: number,
    gapBeforeMs?: number | null,
  ): Promise<{ ack: string }> => {
    const buf = await blob.arrayBuffer();
    const path = `/api/v1/sessions/${sessionId}/streams/${streamId}/chunks/${seq}` +
      `?epoch_id=${epoch}&interval_end_ms=${Math.round(intervalEndMs)}` +
      (recordingElapsedMs === undefined ? "" : `&recording_elapsed_ms=${Math.max(0, Math.round(recordingElapsedMs))}`) +
      (gapBeforeMs === null || gapBeforeMs === undefined ? "" : `&gap_before_ms=${Math.round(gapBeforeMs)}`);
    for (let attempt = 0; attempt < 3; attempt++) {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 12_000);
      try {
        const res = await fetch(path, { method: "PUT", body: buf, signal: controller.signal });
        if (res.ok) return (await res.json()) as { ack: string };
        if (res.status < 500) throw new Error(`PUT chunk: ${res.status}`);
      } catch (error) {
        if (attempt === 2 || (error instanceof Error && /PUT chunk: 4\d\d/.test(error.message))) throw error;
      } finally {
        window.clearTimeout(timeout);
      }
      await new Promise((resolve) => window.setTimeout(resolve, 300 * (attempt + 1)));
    }
    throw new Error("PUT chunk failed after retries");
  },
  postFrame: (
    sessionId: string,
    atMs: number,
    jpegDataUrl?: string,
    trigger = "",
    frame?: { w: number; h: number; prompts: TrackPrompt[] },
    recordingElapsedMs?: number,
  ) =>
    req<{ observation: ObservationPayload; masks: SamMaskPayload[]; sam_error: string | null }>(
      `/api/v1/sessions/${sessionId}/frames`,
      {
        method: "POST",
        body: JSON.stringify({
          at_ms: Math.round(atMs),
          clock_id: "clk_client",
          jpeg_b64: jpegDataUrl ?? "",
          trigger,
          frame_w: frame?.w ?? 0,
          frame_h: frame?.h ?? 0,
          prompts: frame?.prompts ?? [],
          recording_elapsed_ms: recordingElapsedMs === undefined ? null : Math.max(0, Math.round(recordingElapsedMs)),
        }),
      },
    ),
  createGap: (sessionId: string, missing_fact: string) =>
    req(`/api/v1/sessions/${sessionId}/gaps`, {
      method: "POST",
      body: JSON.stringify({ missing_fact }),
    }),
  proposeQuestion: (sessionId: string) =>
    req<{ question: QuestionPayload | null; reason?: string }>(
      `/api/v1/sessions/${sessionId}/questions/propose`,
      { method: "POST", body: JSON.stringify({}) },
    ),
  deliverQuestion: (sessionId: string, question_id: string, nowMs: number) =>
    req<{ delivered: boolean; reason?: string; question?: QuestionPayload }>(
      `/api/v1/sessions/${sessionId}/questions/deliver`,
      { method: "POST", body: JSON.stringify({ question_id, now_ms: Math.round(nowMs) }) },
    ),
  answerQuestion: (sessionId: string, questionId: string, text: string, language: string) =>
    req(`/api/v1/sessions/${sessionId}/questions/${questionId}/answers`, {
      method: "POST",
      body: JSON.stringify({ text, language }),
    }),
  deferQuestion: (sessionId: string, questionId: string, reason: string) =>
    req(`/api/v1/sessions/${sessionId}/questions/${questionId}/defer`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  listDecisions: (sessionId: string) =>
    req<{ decisions: DecisionPayload[] }>(`/api/v1/sessions/${sessionId}/decisions`),
  createDecision: (sessionId: string, body: Record<string, unknown>) =>
    req<{ decision: DecisionPayload }>(`/api/v1/sessions/${sessionId}/decisions`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  reviewDecision: (recordId: string, action: string, reviewer_id: string, approved_scope?: string) =>
    req<{ decision: DecisionPayload }>(`/api/v1/decisions/${recordId}/reviews`, {
      method: "POST",
      body: JSON.stringify({ reviewer_id, action, approved_scope }),
    }),
  assembleEpisode: (sessionId: string) =>
    req<{ episode: { episode_id: string } }>(`/api/v1/sessions/${sessionId}/episodes`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  buildLesson: (episodeId: string) =>
    req<{ lesson: LessonPayload }>(`/api/v1/episodes/${episodeId}/lessons`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  listLessons: (sessionId: string) =>
    req<{ lessons: LessonPayload[] }>(`/api/v1/sessions/${sessionId}/lessons`),
  recordingInfo: (sessionId: string) =>
    req<RecordingInfo>(`/api/v1/sessions/${sessionId}/recording/info`),
  ownedRecordings: () => req<{ recordings: OwnedRecording[] }>("/api/v1/library/recordings"),
  modelCalls: (sessionId: string) => req<{ calls: ModelCallReceipt[] }>(`/api/v1/sessions/${sessionId}/model-calls`),
  importVideo: async (file: File): Promise<{ recording: RecordingInfo & { id: string } }> => {
    const body = new FormData();
    body.append("file", file);
    body.append("capture_permission", "true");
    const response = await fetch(file.name.toLowerCase().endsWith(".zip")
      ? "/api/v1/library/import-backup" : "/api/v1/library/import", { method: "POST", body });
    if (!response.ok) throw new Error(`Import failed: HTTP ${response.status} — ${(await response.text()).slice(0, 160)}`);
    return response.json() as Promise<{ recording: RecordingInfo & { id: string } }>;
  },
  completeRecording: (sessionId: string, streamId: string, expectedChunks: number) =>
    req<{ recording: RecordingInfo }>(`/api/v1/sessions/${sessionId}/recording/complete`, {
      method: "POST", body: JSON.stringify({ stream_id: streamId, epoch_id: "e0", expected_chunks: expectedChunks }),
    }),
  saveTracking: (sessionId: string, samples: SavedTrackSample[]) =>
    req<{ accepted: number }>(`/api/v1/sessions/${sessionId}/tracking`, {
      method: "POST", body: JSON.stringify({ samples }),
    }),
  getTracking: (sessionId: string) =>
    req<{ clock_id: string; source: string; samples: SavedTrackSample[] }>(`/api/v1/sessions/${sessionId}/tracking`),
  saveObjectLabel: (sessionId: string, label: Omit<ObjectLabelPayload, "id" | "review_state">) =>
    req<{ label: ObjectLabelPayload }>(`/api/v1/sessions/${sessionId}/object-labels`, {
      method: "POST", body: JSON.stringify(label),
    }),
  pointObjectLabel: (sessionId: string, labelId: string, point: { x: number; y: number; at_ms: number }) =>
    req<{ label: ObjectLabelPayload }>(`/api/v1/sessions/${sessionId}/object-labels/${labelId}/point`, {
      method: "POST", body: JSON.stringify(point),
    }),
  localizeObjectLabel: (sessionId: string, labelId: string, image: {
    jpeg_b64: string; frame_w: number; frame_h: number; at_ms: number;
  }) => req<{ status: string; label: ObjectLabelPayload; reason?: string }>(
    `/api/v1/sessions/${sessionId}/object-labels/${labelId}/localize`,
    { method: "POST", body: JSON.stringify(image) },
  ),
  getObjectLabels: (sessionId: string) =>
    req<{ labels: ObjectLabelPayload[] }>(`/api/v1/sessions/${sessionId}/object-labels`),
  saveExpertNote: (sessionId: string, text: string, language: string, atMs: number) =>
    req<{ note: { id: string } }>(`/api/v1/sessions/${sessionId}/expert-notes`, {
      method: "POST", body: JSON.stringify({ text, language, at_ms: Math.round(atMs) }),
    }),
  robotDataset: (sessionId: string) =>
    req<RobotDatasetStatus>(`/api/v1/sessions/${sessionId}/robot-dataset`),
  datasetQuality: (sessionId: string) =>
    req<DatasetQuality>(`/api/v1/sessions/${sessionId}/dataset/quality`),
  declareSourceRights: (sessionId: string, origin: string, attribution: string) =>
    req(`/api/v1/sessions/${sessionId}/source-rights`, {
      method: "POST", body: JSON.stringify({ origin, attribution, training_rights_confirmed: true }),
    }),
  runPostprocess: (sessionId: string) =>
    req<{ postprocess: PostprocessRun }>(`/api/v1/sessions/${sessionId}/postprocess/run`, {
      method: "POST", body: JSON.stringify({}),
    }),
  getMasks: (sessionId: string) =>
    req<{ source: string; total: number; truncated: boolean; masks: SavedSamMask[] }>(
      `/api/v1/sessions/${sessionId}/masks`),
  getSession: (sessionId: string) =>
    req<{ session: SessionPayload }>(`/api/v1/sessions/${sessionId}`),
};
