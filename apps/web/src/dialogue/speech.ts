/* On-device speech: talk the question, hear the answer (TRD 7.4 prototype path).
   Browser speech is a rehearsal-grade interface: text stays the required
   fallback, and transcripts keep original language + corrections. */

export function ttsSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

export function primeSpeechOutput(lang = "en-US"): void {
  if (!ttsSupported()) return;
  const cue = lang.startsWith("ja") ? "準備できました" : lang.startsWith("zh") ? "准备好了" : "VEYTAC ready";
  try {
    const utter = new SpeechSynthesisUtterance(cue);
    utter.lang = lang;
    window.speechSynthesis.speak(utter);
  } catch { /* question text and Listen now remain available */ }
}

export function speak(text: string, lang = "en-US", onDone?: (outcome: "ended" | "error" | "timeout") => void, onStart?: () => void): boolean {
  if (!ttsSupported()) return false;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = lang;
  utter.rate = 1;
  let finished = false;
  let watchdog: number | undefined;
  const finish = (outcome: "ended" | "error" | "timeout") => {
    if (finished) return;
    finished = true;
    window.clearTimeout(watchdog);
    onDone?.(outcome);
  };
  utter.onstart = () => {
    onStart?.();
    window.clearTimeout(watchdog);
    watchdog = window.setTimeout(() => { window.speechSynthesis.cancel(); finish("timeout"); }, 10_000);
  };
  utter.onend = () => finish("ended");
  utter.onerror = () => finish("error");
  try {
    watchdog = window.setTimeout(() => { window.speechSynthesis.cancel(); finish("timeout"); }, 4_000);
    window.speechSynthesis.speak(utter);
    return true;
  } catch {
    window.clearTimeout(watchdog);
    return false;
  }
}

export function stopSpeaking(): void {
  if (ttsSupported()) window.speechSynthesis.cancel();
}

type RecogCtor = new () => {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((ev: { resultIndex?: number; results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }> }) => void) | null;
  onerror: ((ev: unknown) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

function recogCtor(): RecogCtor | null {
  const w = window as unknown as Record<string, RecogCtor | undefined>;
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function asrSupported(): boolean {
  return recogCtor() !== null;
}

export interface Listener {
  stop: () => void;
}

export function listen(
  onInterim: (text: string) => void,
  onFinal: (text: string) => void,
  onError: (message: string) => void,
  lang = "en-US",
): Listener | null {
  const Ctor = recogCtor();
  if (!Ctor) return null;
  const rec = new Ctor();
  let stopped = false;
  rec.lang = lang;
  rec.continuous = true;
  rec.interimResults = true;
  rec.onresult = (ev) => {
    let interim = "";
    const results = Array.from(ev.results as unknown as Array<{ 0: { transcript: string }; isFinal: boolean }>);
    for (const res of results.slice(ev.resultIndex ?? 0)) {
      if (res.isFinal) onFinal(res[0].transcript);
      else interim += res[0].transcript;
    }
    if (interim) onInterim(interim);
  };
  rec.onerror = (event) => { if (!stopped) onError(`Speech recognition error: ${String((event as { error?: string }).error ?? "unknown")}`); };
  rec.onend = () => { if (!stopped) onError("Speech recognition stopped. Tap Start to try again."); };
  try {
    rec.start();
  } catch (error) {
    onError(`Speech recognition could not start: ${error instanceof Error ? error.message : "unknown error"}`);
    return null;
  }
  return { stop: () => { stopped = true; rec.stop(); } };
}
