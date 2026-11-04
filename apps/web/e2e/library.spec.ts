import { expect, test } from "@playwright/test";

test("a finished recording has a replay view and a separately gated robot dataset", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("veytac-private-sessions", JSON.stringify(["ses_libraryfixture"]));
  });
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    const body = url.endsWith("/health") ? { status: "ok", execution_mode: "mock" }
      : url.endsWith("/library/recordings") ? { recordings: [{
        id: "ses_libraryfixture", title: "Packing a mug", created_at: "2026-11-05T00:00:00Z",
        source_type: "camera", chunk_count: 2, size_bytes: 1024, complete: true, duration_ms: 1000,
      }] }
      : url.endsWith("/recording/info") ? {
        session_id: "ses_libraryfixture", stream_id: "str_fixture", mime: "video/webm",
        chunk_count: 2, size_bytes: 1024, complete: true, tracking_samples: 1, object_labels: 1,
      }
      : url.endsWith("/tracking") ? { samples: [{ at_ms: 100, frame_w: 1280, frame_h: 720,
        tracks: [{ key: "tool-1", kind: "object", label: "screw · expert said",
          box: { x: 0.3, y: 0.3, w: 0.1, h: 0.1 } }], hand_points: [] }] }
      : url.endsWith("/object-labels") ? { labels: [{ id: "lbl_fixture", label: "screw",
        at_ms: 100, localization: "on_device_candidate", point: null }] }
      : url.endsWith("/masks") ? { source: "sam-3.1", total: 0, truncated: false, masks: [] }
      : url.endsWith("/dataset/quality") ? {
        source_type: "camera", target_robot_format: "LeRobot v3 (future action-aligned adapter)",
        source_rights: { declared: false, basis: null, origin: null },
        evidence: { recording_complete: true, seekable: true, video_bytes: 1024,
          chunk_count: 2, timed_chunks: 0, recording_gap_count: 0,
          live_observations: 1, mock_or_failed_observations: 0, sam_masks: 0,
          decoded_sam_masks: 0, tracking_samples: 1, expert_labels: 1,
          dialogue_turns: 0, approved_latest_decisions: 0,
          grounded_approved_decisions: 0, training_permission: false },
        gates: {
          visual_ai: { status: "BLOCKED", reasons: ["training permission not granted"], format: "VEYTAC observation ZIP" },
          reviewed_sft: { status: "BLOCKED", reasons: ["no latest approved decision records"], format: "VEYTAC JSONL" },
          robot_policy: { status: "BLOCKED", reasons: ["no robot actions"], format: "LeRobot v3" },
          code_agent_harness: { status: "BLOCKED", reasons: ["no tool traces"], format: "none" },
        },
        postprocess_stages: [{ role: "media_integrity", status: "PASS" },
          { role: "human_review", status: "BLOCKED" }],
      }
      : url.endsWith("/postprocess/run") ? { postprocess: {
        execution_mode: "deterministic_local", model_calls: 0, source_digest: "fixture",
        review_queue: [{ kind: "object_label", id: "lbl_fixture", reason: "needs visual confirmation" }],
        approved_grounded_record_ids: [],
      } }
      : url.endsWith("/robot-dataset") ? {
        session_id: "ses_libraryfixture", kind: "observation_only", training_permission: false,
        recording_complete: true, video_bytes: 1024, tracking_samples: 1, expert_labels: 1,
        action_policy_ready: false,
        missing_for_action_policy: ["robot_state", "robot_action", "calibration", "action_alignment"],
      } : {};
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Library" }).click();
  await expect(page.getByRole("heading", { name: "Recorded demonstration" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Packing a mug/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "Download video" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Download session data ZIP" })).toBeVisible();
  await expect(page.getByLabel("Import video or VEYTAC backup")).toBeVisible();
  await expect(page.locator(".replay-frame video")).toHaveAttribute("controls", "");
  await expect(page.locator(".replay-frame video")).toHaveCSS("object-fit", "contain");
  await expect(page.getByText("screw", { exact: true })).toBeVisible();
  await page.screenshot({ path: "../../output/playwright/library-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "../../output/playwright/library-mobile.png" });
  await page.getByRole("button", { name: "Robot dataset" }).click();
  await expect(page.getByText("Action-policy training: blocked")).toBeVisible();
  await expect(page.getByText(/robot_state.*robot_action.*calibration.*action_alignment/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Download observation dataset ZIP" })).toHaveCount(0);
  await page.getByRole("button", { name: "AI dataset" }).click();
  await expect(page.getByText("Reviewed examples: BLOCKED")).toBeVisible();
  await page.getByRole("button", { name: "Assemble review queue" }).click();
  await expect(page.getByText("1 items need review")).toBeVisible();
});
