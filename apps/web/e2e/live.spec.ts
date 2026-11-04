import { expect, test } from "@playwright/test";


test("single live screen exposes start, stop, and mute", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".brand-logo")).toHaveAttribute("alt", "VEYTAC");
  await expect(page.getByRole("button", { name: "Start" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Stop" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Mute" })).toBeDisabled();
  // Localhost is a secure context; camera guidance appears only when support fails.
  expect(await page.evaluate(() => window.isSecureContext)).toBe(true);
  await expect(page.locator(".live-notice")).toHaveCount(0);
  await expect(page.locator(".live-video")).toBeVisible();
});

test("desktop screen source starts in the click and restores camera preview", async ({ page }) => {
  await page.addInitScript(() => {
    const camera = document.createElement("canvas");
    camera.width = 320; camera.height = 240;
    const display = document.createElement("canvas");
    display.width = 1280; display.height = 720;
    setInterval(() => {
      camera.getContext("2d")!.fillRect(0, 0, 320, 240);
      display.getContext("2d")!.fillRect(0, 0, 1280, 720);
    }, 100);
    (window as any).__screenCalled = false;
    (window as any).__apiCalled = false;
    (window as any).__screenCallAfterApi = false;
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: {
      getUserMedia: async (constraints: MediaStreamConstraints) =>
        constraints.video ? camera.captureStream(5) : new MediaStream(),
      getDisplayMedia: async () => {
        (window as any).__screenCalled = true;
        (window as any).__screenCallAfterApi = (window as any).__apiCalled;
        return display.captureStream(5);
      },
    } });
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      cancel: () => {}, speak: () => {},
    } });
  });
  let sourceType = "";
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    if (url.endsWith("/sessions") && route.request().method() === "POST") {
      const screenCalled = await page.evaluate(() => (window as any).__screenCalled);
      expect(screenCalled).toBe(true);
      await page.evaluate(() => { (window as any).__apiCalled = true; });
    }
    if (url.endsWith("/streams")) sourceType = JSON.parse(route.request().postData() ?? "{}").source_type;
    const body = url.endsWith("/health") ? { status: "ok", execution_mode: "mock" }
      : url.endsWith("/sessions") ? { session: { id: "ses_screen_e2e" } }
      : url.endsWith("/streams") ? { stream: { id: "str_screen_e2e" } }
      : url.endsWith("/recording/info") ? { session_id: "ses_screen_e2e", stream_id: "str_screen_e2e", mime: "video/webm", chunk_count: 1, size_bytes: 1000, complete: true, tracking_samples: 0, object_labels: 0 }
      : url.endsWith("/decisions") ? { decisions: [] }
      : url.endsWith("/frames") ? { observation: { id: "obs_screen", status: "proposed", execution_mode: "mock", description: "Screen visible" }, masks: [] }
      : {};
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
  await page.goto("/");
  await page.getByRole("button", { name: /Source: Camera/ }).click();
  await expect(page.getByRole("button", { name: /Source: Screen/ })).toBeVisible();
  await page.getByRole("button", { name: "Start" }).click();
  await page.getByRole("checkbox", { name: /screen and microphone capture/ }).check();
  await page.getByRole("checkbox", { name: /external processing/ }).check();
  await page.getByRole("checkbox", { name: /spoken questions/ }).check();
  await page.getByRole("button", { name: "Start session" }).click();
  await expect.poll(() => sourceType).toBe("screen");
  await expect.poll(() => page.evaluate(() => (window as any).__screenCalled)).toBe(true);
  expect(await page.evaluate(() => (window as any).__screenCallAfterApi)).toBe(false);
  await expect(page.getByRole("button", { name: "Stop" })).toBeEnabled();
  await page.getByRole("button", { name: "Stop" }).click();
  await expect(page.locator(".live-app")).toHaveClass(/has-preview/);
  expect(await page.locator(".live-video").evaluate((video: HTMLVideoElement) =>
    video.srcObject instanceof MediaStream && video.srcObject.getVideoTracks()[0]?.readyState === "live",
  )).toBe(true);
});

test("camera preview follows portrait and landscape without ending the track", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 720; canvas.height = 1280;
    const paint = () => canvas.getContext("2d")!.fillRect(0, 0, 720, 1280);
    paint();
    setInterval(paint, 100);
    (window as any).__formats = [];
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: {
      getUserMedia: async (constraints: MediaStreamConstraints) => {
        (window as any).__formats.push(constraints.video);
        const stream = canvas.captureStream(5);
        const track = stream.getVideoTracks()[0];
        Object.defineProperty(track, "applyConstraints", { value: async (format: MediaTrackConstraints) => {
          (window as any).__formats.push(format);
        } });
        return stream;
      },
    } });
  });
  await page.route("**/api/v1/health", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok", execution_mode: "mock" }) }));
  await page.goto("/");
  await expect(page.locator(".live-app")).toHaveClass(/has-preview/);
  await expect(page.locator(".standby")).toBeHidden();
  await expect(page.locator(".live-video")).toHaveCSS("object-fit", "contain");
  await expect.poll(() => page.evaluate(() => (window as any).__formats[0]?.aspectRatio?.ideal)).toBe(9 / 16);
  await page.setViewportSize({ width: 844, height: 390 });
  await expect.poll(() => page.evaluate(() => {
    const formats = (window as any).__formats;
    return formats[formats.length - 1]?.aspectRatio?.ideal;
  })).toBe(16 / 9);
  expect(await page.locator(".live-video").evaluate((video: HTMLVideoElement) =>
    video.srcObject instanceof MediaStream && video.srcObject.getVideoTracks()[0]?.readyState === "live",
  )).toBe(true);
  const overlay = await page.locator(".detect-overlay").evaluate((canvas: HTMLCanvasElement) =>
    [canvas.width, canvas.height, canvas.clientWidth, canvas.clientHeight],
  );
  expect(overlay.slice(0, 2)).toEqual(overlay.slice(2));
});

test("silent phone speech can switch immediately to live voice input", async ({ page }) => {
  await page.addInitScript(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 320; canvas.height = 240;
    setInterval(() => canvas.getContext("2d")!.fillRect(0, 0, 320, 240), 100);
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: {
      getUserMedia: async () => canvas.captureStream(5),
    } });
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      cancel: () => {}, speak: () => {},
    } });
    (window as any).SpeechRecognition = class {
      lang = ""; continuous = true; interimResults = true;
      onresult: ((value: any) => void) | null = null;
      onerror = null; onend = null;
      start() {
        (window as any).__recognitionStarted = true;
        setTimeout(() => this.onresult?.({ resultIndex: 0, results: [{ 0: { transcript: "Inspecting a valve." }, isFinal: true }] }), 100);
      }
      stop() {}
    };
  });
  let taskBrief = "";
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    if (url.endsWith("/task-brief")) taskBrief = JSON.parse(route.request().postData() ?? "{}").text;
    const body = url.endsWith("/health") ? { status: "ok", execution_mode: "mock" }
      : url.endsWith("/sessions") ? { session: { id: "ses_silent" } }
      : url.endsWith("/streams") ? { stream: { id: "str_silent" } }
      : url.endsWith("/decisions") ? { decisions: [] }
      : {};
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Start" }).click();
  await page.getByRole("checkbox", { name: /camera and microphone capture/ }).check();
  await page.getByRole("checkbox", { name: /external processing/ }).check();
  await page.getByRole("checkbox", { name: /spoken questions/ }).check();
  await page.getByRole("button", { name: "Start session" }).click();
  await expect(page.locator(".spoken-question p")).toBeVisible();
  await page.getByRole("button", { name: "Listen now" }).click();
  await expect.poll(() => page.evaluate(() => (window as any).__recognitionStarted)).toBe(true);
  await expect.poll(() => taskBrief).toBe("Inspecting a valve.");
});

test("failed live observation pauses repeated frame calls while recording continues", async ({ page }) => {
  await page.addInitScript(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 320; canvas.height = 240;
    setInterval(() => canvas.getContext("2d")!.fillRect(0, 0, 320, 240), 100);
    Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: {
      getUserMedia: async () => canvas.captureStream(5),
    } });
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      cancel: () => {}, speak: () => {},
    } });
  });
  let frameCalls = 0;
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    if (url.endsWith("/frames")) frameCalls += 1;
    const body = url.endsWith("/health") ? { status: "ok", execution_mode: "live" }
      : url.endsWith("/sessions") ? { session: { id: "ses_provider_failed" } }
      : url.endsWith("/streams") ? { stream: { id: "str_provider_failed" } }
      : url.endsWith("/frames") ? { observation: { id: "obs_failed", status: "failed", findings: [{ code: "PROVIDER_EMPTY" }] } }
      : url.endsWith("/decisions") ? { decisions: [] }
      : {};
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Start" }).click();
  await page.getByRole("checkbox", { name: /camera and microphone capture/ }).check();
  await page.getByRole("checkbox", { name: /external processing/ }).check();
  await page.getByRole("checkbox", { name: /spoken questions/ }).check();
  await page.getByRole("button", { name: "Start session" }).click();
  await expect.poll(() => frameCalls, { timeout: 20000 }).toBe(1);
  await expect(page.getByRole("button", { name: "Stop" })).toBeEnabled();
  await expect(page.getByText(/Live observation paused \(PROVIDER_EMPTY\)/)).toBeVisible();
  await page.waitForTimeout(9000);
  expect(frameCalls).toBe(1);
  await expect(page.getByRole("button", { name: "Stop" })).toBeEnabled();
});

test("start observes, asks, and records a spoken answer", async ({ page }) => {
  await page.addInitScript(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext("2d")!;
    const paint = () => { ctx.fillStyle = "#5272a0"; ctx.fillRect(0, 0, 320, 240); };
    paint();
    setInterval(paint, 100);
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: async () => canvas.captureStream(5) },
    });
    const audioEvents: string[] = [];
    (window as any).__audioEvents = audioEvents;
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      cancel: () => audioEvents.push("cancel"),
      speak: (utterance: SpeechSynthesisUtterance) => {
        audioEvents.push(utterance.text);
        utterance.onstart?.(new Event("start") as SpeechSynthesisEvent);
        setTimeout(() => { audioEvents.push("speech-ended"); utterance.onend?.(new Event("end") as SpeechSynthesisEvent); }, 300);
      },
    } });
    let voiceTurn = 0;
    (window as any).SpeechRecognition = class {
      lang = "en-US"; continuous = true; interimResults = true;
      onresult: ((value: any) => void) | null = null;
      onerror = null; onend = null;
      start() {
        audioEvents.push("recognition-started");
        const text = ++voiceTurn === 1 ? "I am inspecting a fitting." : "I choose this tool because the fitting is worn.";
        setTimeout(() => this.onresult?.({ resultIndex: 0, results: [{ 0: { transcript: text.slice(0, 8) }, isFinal: false }] }), 300);
        setTimeout(() => this.onresult?.({ resultIndex: 0, results: [{ 0: { transcript: text }, isFinal: true }] }), 1500);
      }
      stop() {}
    };
  });
  let answered = false;
  let reviewed = false;
  let lessonBuilt = false;
  let taskBrief = "";
  const windows: Array<{ allow: boolean; duration_s: number }> = [];
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    const json = (body: object) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
    if (url.endsWith("/health")) return json({ status: "ok", execution_mode: "mock" });
    if (url.endsWith("/sessions")) return json({ session: { id: "ses_test" } });
    if (url.endsWith("/streams")) return json({ stream: { id: "str_test" } });
    if (url.endsWith("/task-brief")) { taskBrief = JSON.parse(route.request().postData() ?? "{}").text; return json({ task_brief: taskBrief }); }
    if (url.endsWith("/question-window")) {
      windows.push(JSON.parse(route.request().postData() ?? "{}"));
      return json({});
    }
    if (url.endsWith("/frames")) return json({ observation: { id: "obs_test", status: "proposed", description: "expert uses a tool", execution_mode: "mock" } });
    if (url.endsWith("/questions/propose")) return json({ question: { id: "q_test", gap_id: "gap_test", wording: "Why did you choose that tool?", status: "candidate" } });
    if (url.endsWith("/questions/deliver")) return json({ delivered: true, question: { id: "q_test", gap_id: "gap_test", wording: "Why did you choose that tool?", status: "delivered" } });
    if (url.endsWith("/answers")) { answered = true; return json({ turn: { id: "turn_test" } }); }
    if (url.endsWith("/lessons")) {
      const lesson = { id: "les_test", title: "Fitting inspection", task_context: "fitting", checkpoints: [{ prompt: "When choose this tool?", expected_distinction: "worn fittings only", explanation: "I choose this tool because the fitting is worn." }], limitations: ["Expert report, not engineering validation"] };
      if (route.request().method() === "POST") { lessonBuilt = true; return json({ lesson }); }
      return json({ lessons: lessonBuilt ? [lesson] : [] });
    }
    if (url.endsWith("/reviews")) {
      reviewed = true;
      return json({ decision: { record_id: "rec_test", revision: 1, review: { state: "approved" }, expert_original_statement: "I choose this tool because the fitting is worn.", observed_action_description: "expert uses a tool" } });
    }
    if (url.endsWith("/episodes")) return json({ episode: { episode_id: "ep_test" } });
    if (url.endsWith("/decisions")) {
      const decision = { record_id: "rec_test", revision: 1, review: { state: "draft" }, expert_original_statement: "I choose this tool because the fitting is worn.", observed_action_description: "expert uses a tool" };
      return json(route.request().method() === "GET" ? { decisions: [decision] } : { decision });
    }
    return json({});
  });
  await page.route(/https:\/\/(cdn\.jsdelivr\.net|storage\.googleapis\.com)\//, (route) => route.abort());
  await page.goto("/");
  await page.getByRole("button", { name: "Start" }).click();
  await expect(page.getByRole("dialog", { name: "Observe with permission" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start session" })).toBeDisabled();
  await page.getByRole("checkbox", { name: /camera and microphone capture/ }).check();
  await expect(page.getByRole("button", { name: "Start session" })).toBeDisabled();
  await page.getByRole("checkbox", { name: /external processing/ }).check();
  await page.getByRole("checkbox", { name: /spoken questions/ }).check();
  await page.getByRole("button", { name: "Start session" }).click();
  await expect(page.locator(".spoken-question p")).toHaveText("What kind of work are you going to do today?");
  await expect.poll(() => page.evaluate(() => {
    const events: string[] = (window as any).__audioEvents;
    const question = events.indexOf("What kind of work are you going to do today?");
    const listening = events.indexOf("recognition-started");
    return [events.includes("VEYTAC ready"), question >= 0, listening > question];
  })).toEqual([true, true, true]);
  await expect.poll(() => taskBrief).toBe("I am inspecting a fitting.");
  await expect.poll(() => windows.some((window) => window.allow && window.duration_s === 600)).toBe(true);
  await expect(page.locator(".spoken-question p")).toHaveText("Why did you choose that tool?", { timeout: 20000 });
  await page.screenshot({ path: "../../output/playwright/live-active.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "../../output/playwright/live-active-mobile.png" });
  await expect.poll(() => answered, { timeout: 10000 }).toBe(true);
  await expect(page.locator(".dialogue-rail .expert span").last()).toHaveText("I choose this tool because the fitting is worn.");
  await expect(page.locator(".observation-copy small")).toContainText("seeing:", { timeout: 30000 });
  await page.getByRole("button", { name: "Mute" }).click();
  await expect(page.getByRole("button", { name: "Unmute" })).toBeVisible();
  await page.getByRole("button", { name: "Stop" }).click();
  await expect(page.getByText("Session complete")).toBeVisible();
  await expect(page.locator(".live-app")).toHaveClass(/has-preview/);
  expect(await page.locator(".live-video").evaluate((video: HTMLVideoElement) =>
    video.srcObject instanceof MediaStream && video.srcObject.getVideoTracks()[0]?.readyState === "live",
  )).toBe(true);
  await page.getByRole("textbox", { name: "Reviewer ID" }).fill("reviewer_test");
  await page.getByRole("textbox", { name: "Approved scope" }).fill("worn fittings only");
  await page.getByRole("button", { name: "Approve this record" }).click();
  await expect.poll(() => reviewed).toBe(true);
  await page.getByRole("button", { name: "Build episode + lesson" }).click();
  await expect(page.getByText("Fitting inspection")).toBeVisible();
  await expect(page.getByText("worn fittings only")).toBeVisible();
});

test("Japanese opening question uses Japanese speech and recognition locale", async ({ page }) => {
  await page.addInitScript(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 320; canvas.height = 240;
    const paint = () => canvas.getContext("2d")!.fillRect(0, 0, 320, 240);
    paint();
    setInterval(paint, 100);
    Object.defineProperty(navigator, "mediaDevices", { configurable: true,
      value: { getUserMedia: async () => canvas.captureStream(5) } });
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      cancel: () => {},
      speak: (utterance: SpeechSynthesisUtterance) => {
        (window as any).__spokenLang = utterance.lang;
        utterance.onstart?.(new Event("start") as SpeechSynthesisEvent);
        setTimeout(() => utterance.onend?.(new Event("end") as SpeechSynthesisEvent), 50);
      },
    } });
    (window as any).SpeechRecognition = class {
      lang = ""; continuous = true; interimResults = true;
      onresult = null; onerror = null; onend = null;
      start() { (window as any).__recognitionLang = this.lang; }
      stop() {}
    };
  });
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    const body = url.endsWith("/health") ? { status: "ok", execution_mode: "mock" }
      : url.endsWith("/sessions") ? { session: { id: "ses_ja" } }
      : url.endsWith("/streams") ? { stream: { id: "str_ja" } }
      : url.endsWith("/frames") ? { observation: { id: "obs_ja", status: "proposed", description: "mock observation", execution_mode: "mock" } }
      : { decisions: [] };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
  await page.route(/https:\/\/(cdn\.jsdelivr\.net|storage\.googleapis\.com)\//, (route) => route.abort());
  await page.goto("/");
  await page.getByRole("button", { name: "Start" }).click();
  await page.getByRole("combobox", { name: "Question and answer language" }).selectOption("ja");
  await page.getByRole("checkbox", { name: /camera and microphone capture/ }).check();
  await page.getByRole("checkbox", { name: /external processing/ }).check();
  await page.getByRole("checkbox", { name: /spoken questions/ }).check();
  await page.getByRole("button", { name: "Start session" }).click();
  await expect(page.locator(".spoken-question p")).toHaveText("今日はどのような作業をしますか？");
  await expect.poll(() => page.evaluate(() => (window as any).__spokenLang)).toBe("ja-JP");
  await expect.poll(() => page.evaluate(() => (window as any).__recognitionLang)).toBe("ja-JP");
});
