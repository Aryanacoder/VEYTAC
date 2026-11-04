# VEYTAC self-hosting runbook (demo + rehearsal)

Anyone can host the core loop on their own WiFi. No cloud account needed
for capture → question → review → lesson in mock mode.

## 1. Backend (this PC or any host on the LAN)

```bash
python -m pip install -e ".[dev]"
copy .env.example .env        # Windows; `cp` on macOS/Linux
$env:PYTHONPATH = "src"       # until the package is pip-installed
python -m veytac.cli serve --host 127.0.0.1 --port 8000
```

`serve` and `doctor` load the repo-root `.env` automatically (explicit
process env wins). `doctor` prints which file it loaded and the effective
mode — if it says `mode=mock`, your live settings are not applied. Live
rehearsal needs all three in `.env`: key in `VEYTAC_META_API_KEY`,
`VEYTAC_EXECUTION_MODE=live`, `VEYTAC_ALLOW_PAID_CALLS=true`.

Health on the PC: `http://127.0.0.1:8000/api/v1/health` → `{"status":"ok",...}`.
The phone uses the web server's HTTPS `/api` proxy; it does not connect
directly to port 8000.

If the UI reports HTTP 500 on session creation, the backend is down or an
old server is running: restart it with the command above (from the repo
root) and read its terminal output — the real error is printed there.

## 2. Web app

```bash
cd apps/web
npm install   # required after every package.json change (adds the on-device tracker)
npm run dev:lan     # plain HTTP, this PC via localhost only for camera
```

From the repository root, run `python scripts/setup_vision_assets.py` after
`npm install`. This verifies and installs the pinned hand and object models and
copies the MediaPipe runtime into the Git-ignored `apps/web/public/vision/`
directory. The browser loads these assets from this PC over the same LAN HTTPS
origin; it does not contact Google's model CDN at runtime. If they cannot load,
the app says tracking is unavailable and falls back to timed model frames. It
never fakes detections. Review upstream redistribution terms before including
these assets in a public release.

Open the printed URL. The dev proxy forwards `/api` to port 8000.

## 2b. Phone or iPad on the same WiFi and the same PC IP

Browsers require a secure context for camera/microphone access. An ordinary
`http://192.168.x.y:5173` page cannot capture. Vite 5 also does not accept a
`--https` CLI flag. Use the provided IP-bound certificate and HTTPS config:

1. On the PC, find the WiFi IPv4 address with `ipconfig` (currently this host
   reported `YOUR_WIFI_IP`; check it again if the network changes).
2. From the repo root, start one current backend process:
   `python -m veytac.cli serve --host 127.0.0.1 --port 8000`.
   Stop old VEYTAC processes on port 8000 first. A second listener can serve
   stale code even while `doctor` reports current settings. The current
   `/api/v1/health` response includes
   `"observation_contract":"observation-inference-v2"`; if missing, the
   backend is stale and must be restarted.
3. From `apps/web`, run `npm run cert:lan -- --ip YOUR_WIFI_IP` once, then
   `npm run dev:https`. The script creates `apps/web/.certs/lan-ca.crt`,
   `lan-server.crt`, and a private `lan-server.key`. The directory is ignored
   by Git. If the IP changes, use `npm run cert:lan -- --ip NEW_IP --renew`
   and re-trust the new CA on each device.
4. Transfer **only** `lan-ca.crt` to your own iPhone/iPad (AirDrop or Files),
   install its certificate profile, then enable it under **Settings → General
   → About → Certificate Trust Settings → Enable full trust for root
   certificates**. Installing a profile alone does not enable SSL trust.
   On Android, install this local CA through the device's certificate settings.
   Never transfer `lan-server.key`.
5. Open `https://YOUR_WIFI_IP:5173` in Safari/Chrome. The address must match
   the generated certificate's IP. Check
   `https://YOUR_WIFI_IP:5173/api/v1/health` first; it should return JSON.
   Then allow camera and microphone when the browser prompts.
6. If it cannot connect, allow Node/Vite inbound TCP 5173 on the Windows
   **Private** network and ensure the WiFi does not isolate clients. Keep the
   backend API on `127.0.0.1`; Vite proxies `/api` and the voice WebSocket.

Do not treat a certificate warning bypass as a reliable camera permission
setup on iOS. The generated CA is for this local rehearsal only. Remove its
trust from the phone/tablet when the rehearsal is finished.

Sources: [Vite server HTTPS](https://vite.dev/config/server-options.html#server-https),
[secure contexts](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts),
[Apple certificate trust](https://support.apple.com/en-us/102390).

## 4. Live-provider mode (real Meta inference)

```bash
# .env
VEYTAC_EXECUTION_MODE=live
VEYTAC_META_API_KEY=<server-side only, never in Git or the browser>
VEYTAC_ALLOW_PAID_CALLS=true
```

Per-session ceiling: `VEYTAC_SESSION_COST_CAP_USD` (default $3.00).
Spend is reserved before every call and reconciled after (TRD 13.2).
Voice relay reserves a 2-minute audio block up front and reconciles actual
seconds on close. The browser posts an initial frame, tracked changes, and a
bounded context refresh about every 8 seconds while recording. If a provider
observation fails, it pauses further frame calls in that session; recording
and local tracking continue.

On iPhone Safari, tap **Start session** while speaker audio is enabled. The
app plays a short ready cue, then asks the opening question. If the question
is visible but silent, tap **Hear question**. If speech input does not begin,
tap **Listen now**. Those controls use the same consented session. Safari
speech support can depend on device settings; a successful browser mock does
not establish audio on a real phone. After a test, keep the session ID so
the server's status-only interaction diagnostics can identify whether TTS,
the voice socket, and microphone frames started. Do not send recordings or
secrets for diagnosis.

The app requests 9:16 camera capture in portrait and 16:9 in landscape and
updates constraints on rotation. The displayed resolution is the actual
camera format chosen by the device; a camera may ignore an ideal aspect
request. Check the saved recording's dimensions before claiming either
format is supported on a specific phone.

## 5. Verify your host

```bash
python -m pytest tests/ -q -p no:cacheprovider -p no:rerunfailures
python -m veytac.cli doctor
```

Playwright e2e needs a dev machine (not the restricted sandbox):
`cd apps/web && npm run test:e2e`.
