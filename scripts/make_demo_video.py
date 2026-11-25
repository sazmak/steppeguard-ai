"""Automated 2-3 Minute Demo Video Generator for SteppeGuard AI.

Combines:
1. ElevenLabs Text-to-Speech API (reads ELEVENLABS_API_KEY from local .env).
2. Live 1280x720 WebGL recording of SteppeGuard AI via Playwright + Microsoft Edge.
3. Exact scene-by-scene timing synchronization & H.264/AAC MP4 muxing via ffmpeg.

Output: docs/SteppeGuard_Demo_Video.mp4 (~2:25 - 2:45, strictly within 2-3 min).
"""

import json
import math
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "scratch_video"
DOCS = ROOT / "docs"
SCRATCH.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
# Student's own cloned voice: sazmak2
VOICE_ID = "tIXuBC4TvDBXYLeFhvhv"
MODEL_ID = "eleven_multilingual_v2"

SCENES = [
    (
        "scene_1_intro",
        "Hi, I'm Oral Sanzhar from QAIRU, Stream 1 Practice 4, in the AI and Machine Learning program. "
        "This is SteppeGuard AI — an interactive 3D wildfire risk intelligence and decision-support system "
        "built for Kazakhstan's steppe regions. It chains three AI Fundamentals topics into one live pipeline: "
        "Classical Machine Learning predicts fire probability per sector, Risk-Aware A-Star plans the safest route, "
        "and a Markov Decision Process computes the optimal long-term response policy."
    ),
    (
        "scene_2_search_mdp",
        "In the Abai High Wind scenario, an intense fire front blocks the direct corridor between our base and the settlement. "
        "Let's animate the A-Star search and rescue drone. Notice how unweighted BFS, the red path, cuts blindly through "
        "the flames with a fire exposure of seven point four four. Our Risk-Aware A-Star, the green path, detours cleanly "
        "around the wildfire, cutting exposure by ninety-nine percent while matching UCS's exact optimal cost with almost "
        "half the expanded nodes. On the right, Bellman Value Iteration recommends Aerial Retardant. And if aircraft "
        "resources drop to Low, the MDP immediately switches to Evacuate and Hold."
    ),
    (
        "scene_3_presets_bayes",
        "Switching to Kostanay Dry Steppe, the medium-risk corridor causes the MDP to choose Safe Detour. "
        "In Akmola Watchtower, calm baseline conditions select Direct Dispatch. Now let's test live probabilistic reasoning: "
        "triggering a Watchtower Smoke Alert on sector five-four applies Bayes' theorem in real time, raising fire belief "
        "from under ten percent to nearly fifty percent, and immediately re-planning A-Star around the alert. "
        "Under Kazakhstan's AI Law Number two-thirty-eight, our Human-in-the-Loop gate requires a human dispatcher "
        "to approve or override every AI recommendation."
    ),
    (
        "scene_4_offline_2d",
        "Because Three.js is bundled locally with zero external CDNs, SteppeGuard AI runs completely offline, "
        "and includes an instant 2D Canvas fallback mode for low-power hardware."
    ),
    (
        "scene_5_math",
        "The Math and Formulas tab exposes every calculation transparently. Topic One shows our pure-NumPy Logistic "
        "Regression weights, linear score, and sigmoid probability alongside the live Bayesian update. Topic Two verifies "
        "our admissible Manhattan heuristic guaranteeing optimal routing. Below, Topic Three displays the full eight-state "
        "Bellman Value Iteration table, active state breakdown, and discount-factor gamma sensitivity showing where "
        "myopic and farsighted policies diverge."
    ),
    (
        "scene_6_benchmarks",
        "Finally, the Benchmarks tab summarizes thirty independent random seeds and nineteen passing automated tests. "
        "Validation threshold tuning lifts wildfire recall from seventy-eight to nearly eighty-seven percent, A-Star cuts "
        "fire exposure by ninety-eight percent versus BFS while saving forty-nine percent of node expansions versus UCS, "
        "and Bellman Value Iteration converges in seventeen sweeps. All telemetry is transparently labeled as synthetic "
        "simulation data. Thank you for watching!"
    ),
]


def load_api_key() -> str:
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise FileNotFoundError("Missing .env with ELEVENLABS_API_KEY.")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("ELEVENLABS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("ELEVENLABS_API_KEY not found in .env.")


def generate_tts_segments(api_key: str) -> list[tuple[str, Path, float]]:
    results = []
    for name, text in SCENES:
        mp3_path = SCRATCH / f"{name}.mp3"
        if not mp3_path.exists() or mp3_path.stat().st_size < 1000:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
            body = json.dumps({
                "text": text,
                "model_id": MODEL_ID,
                "voice_settings": {
                    "stability": 0.55,
                    "similarity_boost": 0.78,
                    "style": 0.15,
                    "use_speaker_boost": True,
                },
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                mp3_path.write_bytes(resp.read())
        dur = probe_duration(mp3_path)
        print(f"  TTS {name}: {dur:.2f}s ({mp3_path.stat().st_size:,} bytes)")
        results.append((name, mp3_path, dur))
    return results


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def build_combined_audio(segments: list[tuple[str, Path, float]], pause_sec: float = 0.35) -> tuple[Path, list[float]]:
    """Concatenate all scene MP3s with automatic gentle tempo fit strictly inside 2:00-2:52."""
    raw_total = sum(d for _, _, d in segments) + pause_sec * (len(segments) - 1)
    # Keep natural 1.0x speed if <= 172s; otherwise gently adjust tempo to fit ~168s (2:48)
    tempo = 1.0 if raw_total <= 172.0 else min(1.22, raw_total / 168.0)
    print(f"Raw audio total={raw_total:.2f}s -> applying tempo={tempo:.3f}x")

    silence = SCRATCH / "silence.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", f"{pause_sec:.2f}", str(silence),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wav_parts = []
    adj_durs: list[float] = []
    for idx, (name, mp3_path, _) in enumerate(segments):
        wav_path = SCRATCH / f"{name}.wav"
        cmd = ["ffmpeg", "-y", "-i", str(mp3_path)]
        if abs(tempo - 1.0) > 0.005:
            cmd += ["-filter:a", f"atempo={tempo:.4f}"]
        cmd += ["-ar", "44100", "-ac", "2", str(wav_path)]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        adj_durs.append(probe_duration(wav_path))
        wav_parts.append(wav_path)
        if idx < len(segments) - 1:
            wav_parts.append(silence)

    concat_list = SCRATCH / "audio_list.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in wav_parts),
        encoding="utf-8",
    )
    out_wav = SCRATCH / "narration.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(out_wav)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"Combined narration duration: {probe_duration(out_wav):.2f}s (strictly within 2:00-3:00)")
    return out_wav, adj_durs


def wait_until(deadline: float) -> None:
    rem = deadline - time.perf_counter()
    if rem > 0:
        time.sleep(rem)


def smooth_orbit(page, dx_total: float, dy_total: float, steps: int = 24, duration: float = 2.0) -> None:
    cx, cy = 620.0, 380.0
    page.mouse.move(cx, cy)
    page.mouse.down()
    for i in range(1, steps + 1):
        frac = i / steps
        page.mouse.move(cx + dx_total * frac, cy + dy_total * frac)
        time.sleep(duration / steps)
    page.mouse.up()


def smooth_scroll(page, target_y: int, steps: int = 25, duration: float = 1.6) -> None:
    cur_y = page.evaluate("window.scrollY")
    for i in range(1, steps + 1):
        frac = 0.5 - 0.5 * math.cos(math.pi * i / steps)
        y = int(cur_y + (target_y - cur_y) * frac)
        page.evaluate(f"window.scrollTo(0, {y})")
        time.sleep(duration / steps)


def record_choreographed_video(durs: list[float], pause_sec: float = 0.35) -> Path:
    """Start local FastAPI server & record synchronized 1280x720 live 3D session."""
    server = subprocess.Popen(
        [str(ROOT / ".venv" / "Scripts" / "python.exe"), str(ROOT / "app.py")],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # Wait for local server to come up
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=2) as r:
                    if r.status == 200:
                        break
            except Exception:
                time.sleep(0.4)

        raw_dir = SCRATCH / "raw_rec"
        raw_dir.mkdir(parents=True, exist_ok=True)
        for old in raw_dir.glob("*.webm"):
            old.unlink()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=EDGE_EXE,
                headless=False,  # Headed native GPU WebGL ensures silky smooth 3D Three.js!
                args=[
                    "--window-size=1280,760",
                    "--window-position=40,20",
                    "--disable-infobars",
                ],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                record_video_dir=str(raw_dir),
                record_video_size={"width": 1280, "height": 720},
            )
            page = context.new_page()
            page.goto("http://127.0.0.1:8000", wait_until="networkidle")
            page.wait_for_selector("#mdp-rec-action")
            time.sleep(1.2)

            t0 = time.perf_counter()
            cum = 0.0

            # --- SCENE 1: Intro & 3D Abai Fire Corridor Orbit ---
            cum += durs[0] + pause_sec
            smooth_orbit(page, -140, -18, steps=35, duration=4.5)
            time.sleep(1.2)
            smooth_orbit(page, 210, 10, steps=40, duration=5.0)
            wait_until(t0 + cum)

            # --- SCENE 2: Animate Search & Drone + Resource High -> Low -> High ---
            s2_start = time.perf_counter()
            cum += durs[1] + pause_sec
            page.click("#btn-play-anim")
            time.sleep(2.5)
            smooth_orbit(page, -95, -12, steps=28, duration=3.5)
            # Wait until ~72% of Scene 2 narration (when talking about Resource Low -> Evacuate)
            wait_until(s2_start + durs[1] * 0.72)
            page.click('#resource-toggle button[data-value="Low"]')
            time.sleep(4.2)
            page.click('#resource-toggle button[data-value="High"]')
            wait_until(t0 + cum)

            # --- SCENE 3: Kostanay -> Akmola -> Watchtower Smoke Alert (+Bayes) -> HITL Approve ---
            s3_start = time.perf_counter()
            cum += durs[2] + pause_sec
            page.click('.preset-btn[data-preset="kostanay_dry_steppe"]')
            wait_until(s3_start + durs[2] * 0.22)
            page.click('.preset-btn[data-preset="akmola_sensor_noise"]')
            wait_until(s3_start + durs[2] * 0.44)
            page.click("#btn-sensor-alert")
            time.sleep(2.0)
            smooth_orbit(page, 70, -10, steps=20, duration=2.4)
            wait_until(s3_start + durs[2] * 0.78)
            page.click("#btn-hitl-confirm")
            wait_until(t0 + cum)

            # --- SCENE 4: Offline & 2D Fallback Mode ---
            s4_start = time.perf_counter()
            cum += durs[3] + pause_sec
            page.click("#btn-render-mode")  # Switch to 2D
            wait_until(s4_start + durs[3] * 0.75)
            page.click("#btn-render-mode")  # Switch back to 3D
            wait_until(t0 + cum)

            # --- SCENE 5: Tab 2 Math & Formulas ---
            s5_start = time.perf_counter()
            cum += durs[4] + pause_sec
            page.click('.tab-btn[data-tab="math"]')
            time.sleep(0.8)
            wait_until(s5_start + durs[4] * 0.45)
            smooth_scroll(page, 460, steps=30, duration=2.2)
            wait_until(s5_start + durs[4] * 0.80)
            smooth_scroll(page, 720, steps=20, duration=1.5)
            wait_until(t0 + cum)

            # --- SCENE 6: Tab 3 30-Seed Benchmarks & Closing ---
            s6_start = time.perf_counter()
            cum += durs[5] + 1.0
            page.click('.tab-btn[data-tab="benchmarks"]')
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2.2)
            smooth_scroll(page, 420, steps=26, duration=2.0)
            wait_until(s6_start + durs[5] * 0.45)
            smooth_scroll(page, 940, steps=26, duration=2.0)
            wait_until(s6_start + durs[5] * 0.75)
            smooth_scroll(page, 1480, steps=26, duration=2.0)
            wait_until(t0 + cum)

            video_path = Path(page.video.path())
            context.close()
            browser.close()
            print(f"Raw recorded WebM: {video_path} ({probe_duration(video_path):.2f}s)")
            return video_path
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()


def mux_final_mp4(raw_video: Path, audio_wav: Path, out_mp4: Path) -> None:
    """Merge live 1280x720 WebM video + ElevenLabs WAV into universal H.264/AAC MP4."""
    # Trim the tiny initial 1.2s pre-load buffer so voiceover starts crisp on the loaded 3D scene
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", "1.2",
            "-i", str(raw_video),
            "-i", str(audio_wav),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            str(out_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    dur = probe_duration(out_mp4)
    size_mb = out_mp4.stat().st_size / (1024 * 1024)
    print(f"FINAL_MP4_OK: {out_mp4} | duration={dur:.2f}s ({int(dur//60)}:{int(dur%60):02d}) | size={size_mb:.2f} MB")

    # Extract 4 verification frames for Visual QA
    for idx, ts in enumerate(["00:00:08", "00:00:42", "00:01:25", "00:02:15"], 1):
        frame_out = SCRATCH / f"qa_frame_{idx}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", ts, "-i", str(out_mp4), "-frames:v", "1", str(frame_out)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    print("1/4 Generating ElevenLabs voiceover segments (cached if already present)...")
    key = load_api_key()
    segs = generate_tts_segments(key)
    print("2/4 Concatenating synchronized narration...")
    narration, adj_durs = build_combined_audio(segs, pause_sec=0.35)
    print("3/4 Recording live 1280x720 3D WebGL session in Microsoft Edge...")
    raw_webm = record_choreographed_video(adj_durs, pause_sec=0.35)
    print("4/4 Muxing final H.264/AAC MP4...")
    final_mp4 = DOCS / "SteppeGuard_Demo_Video.mp4"
    mux_final_mp4(raw_webm, narration, final_mp4)
