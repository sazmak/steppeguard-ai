"""Rebuild docs/SteppeGuard_Presentation.pptx from scratch via 1920x1080 HTML->PNG->PPTX.

Guarantees:
- 100% identical agency-grade dark visual design in PowerPoint, Google Slides & Keynote
- Zero broken python-pptx rounded rectangles, zero font clipping, zero overlaps
- High-contrast scannable QR codes on Slide 1 (Live 3D Demo) & Slide 7 (Demo + GitHub)
"""

import base64
from pathlib import Path
from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.util import Inches

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
RESULTS = ROOT / "results"
ASSETS = ROOT / "assets"
SLIDE_DIR = ROOT / "scratch_video" / "slides"
SLIDE_DIR.mkdir(parents=True, exist_ok=True)
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def data_uri(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    mime = "image/svg+xml" if ext == "svg" else f"image/{ext}"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_slides_html() -> str:
    img_3d = data_uri(RESULTS / "fig4_3d_live_demo.png")
    img_ml = data_uri(RESULTS / "fig1_ml_evaluation.png")
    img_search = data_uri(RESULTS / "fig2_search_benchmark.png")
    img_mdp = data_uri(RESULTS / "fig3_mdp_convergence.png")
    img_pipe = data_uri(ASSETS / "pipeline.svg")
    qr_demo = data_uri(ASSETS / "qr_demo.png")
    qr_git = data_uri(ASSETS / "qr_github.png")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #000; font-family: "Segoe UI", system-ui, -apple-system, sans-serif; color: #f8fafc; }}
  .slide {{
    width: 1920px; height: 1080px;
    background: radial-gradient(circle at 18% 12%, #132544 0%, #070d19 58%);
    position: relative; overflow: hidden;
    padding: 58px 74px 62px 74px;
    display: flex; flex-direction: column;
  }}
  .top-bar {{
    position: absolute; top: 0; left: 0; right: 0; height: 8px;
    background: linear-gradient(90deg, #f97316, #f59e0b, #38bdf8);
  }}
  .hdr {{ margin-bottom: 30px; }}
  .eyebrow {{ font-size: 16px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #f59e0b; margin-bottom: 8px; }}
  .title {{ font-size: 46px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px; line-height: 1.12; }}
  .subtitle {{ font-size: 21px; color: #38bdf8; margin-top: 8px; font-weight: 500; }}
  .footer {{
    position: absolute; bottom: 24px; left: 74px; right: 74px;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 16px; color: #94a3b8; border-top: 1px solid rgba(148,163,184,0.18); padding-top: 12px;
  }}
  .card {{
    background: rgba(17, 29, 51, 0.86);
    border: 1.5px solid rgba(148, 163, 184, 0.24);
    border-radius: 18px;
    padding: 28px 32px;
  }}
  .card-cyan {{ border-color: rgba(56, 189, 248, 0.55); }}
  .card-green {{ border-color: rgba(34, 197, 94, 0.55); }}
  .card-amber {{ border-color: rgba(245, 158, 11, 0.55); }}
  .card-orange {{ border-color: rgba(249, 115, 22, 0.55); }}
  .card h3 {{ font-size: 23px; font-weight: 700; margin-bottom: 16px; letter-spacing: 0.2px; }}
  .c-cyan {{ color: #38bdf8; }}
  .c-green {{ color: #4ade80; }}
  .c-amber {{ color: #fbbf24; }}
  .c-orange {{ color: #fb923c; }}
  ul.pts {{ list-style: none; display: flex; flex-direction: column; gap: 13px; font-size: 20px; line-height: 1.42; color: #e2e8f0; }}
  ul.pts li {{ padding-left: 24px; position: relative; }}
  ul.pts li::before {{ content: "▸"; position: absolute; left: 0; color: #38bdf8; font-weight: 800; }}
  .mono-box {{
    font-family: "Cascadia Code", "Consolas", monospace;
    background: rgba(7, 13, 25, 0.92);
    border: 1px solid rgba(56, 189, 248, 0.45);
    border-radius: 12px;
    padding: 16px 20px;
    font-size: 17.5px;
    line-height: 1.55;
    color: #7dd3fc;
    margin-top: 18px;
  }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 28px; flex: 1; }}
  .grid-topic {{ display: grid; grid-template-columns: 0.92fr 1.08fr; gap: 32px; flex: 1; align-items: stretch; }}
  .img-wrap {{
    background: rgba(11, 20, 38, 0.92);
    border: 1.5px solid rgba(56, 189, 248, 0.35);
    border-radius: 18px;
    padding: 18px;
    display: flex; flex-direction: column; justify-content: center;
  }}
  .img-wrap img {{ width: 100%; height: auto; border-radius: 10px; display: block; }}
  .img-cap {{ font-size: 17px; color: #cbd5e1; margin-top: 14px; line-height: 1.4; }}
  .pill-row {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 22px; }}
  .pill {{
    padding: 9px 18px; border-radius: 999px; font-size: 16px; font-weight: 700;
    font-family: "Cascadia Code", Consolas, monospace;
  }}
  .p-cyan {{ background: rgba(56,189,248,0.16); color: #7dd3fc; border: 1px solid rgba(56,189,248,0.45); }}
  .p-green {{ background: rgba(34,197,94,0.16); color: #86efac; border: 1px solid rgba(34,197,94,0.45); }}
  .p-amber {{ background: rgba(245,158,11,0.16); color: #fde68a; border: 1px solid rgba(245,158,11,0.45); }}

  /* Slide 1 Hero */
  .hero-grid {{ display: grid; grid-template-columns: 0.94fr 1.06fr; gap: 42px; flex: 1; align-items: center; }}
  .hero-title {{ font-size: 76px; font-weight: 900; letter-spacing: -1.5px; line-height: 1.05; margin: 14px 0 18px 0; }}
  .hero-sub {{ font-size: 27px; color: #38bdf8; font-weight: 500; line-height: 1.35; margin-bottom: 24px; }}
  .hero-qr-card {{
    margin-top: 32px; display: flex; align-items: center; gap: 24px;
    background: rgba(17, 29, 51, 0.92); border: 1.5px solid rgba(56, 189, 248, 0.55);
    border-radius: 18px; padding: 18px 24px;
  }}
  .hero-qr-card img {{ width: 148px; height: 148px; border-radius: 10px; background: #fff; padding: 6px; }}
  .tbl {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 17px; }}
  .tbl th {{ text-align: left; color: #94a3b8; padding: 10px 12px; border-bottom: 1.5px solid rgba(148,163,184,0.28); }}
  .tbl td {{ padding: 10px 12px; border-bottom: 1px solid rgba(148,163,184,0.14); font-family: "Cascadia Code", Consolas, monospace; }}
  .tbl tr.hi td {{ color: #4ade80; font-weight: 700; background: rgba(34,197,94,0.08); }}
  .step-item {{
    background: rgba(7, 13, 25, 0.72); border-left: 4px solid #38bdf8;
    border-radius: 10px; padding: 14px 18px; font-size: 19px; line-height: 1.38; color: #e2e8f0;
  }}
  .step-item strong {{ color: #38bdf8; display: block; margin-bottom: 4px; font-size: 20px; }}
  .qr-dual {{
    display: flex; justify-content: space-around; align-items: center; gap: 24px; height: 100%;
  }}
  .qr-unit {{ text-align: center; }}
  .qr-unit img {{ width: 188px; height: 188px; border-radius: 12px; background: #fff; padding: 8px; display: block; margin: 0 auto 10px auto; }}
  .qr-unit .lbl {{ font-size: 18px; font-weight: 700; color: #f8fafc; }}
  .qr-unit .url {{ font-size: 14px; font-family: "Cascadia Code", Consolas, monospace; color: #38bdf8; margin-top: 2px; }}
</style>
</head>
<body>

<!-- SLIDE 1: HERO -->
<section class="slide" id="slide-1">
  <div class="top-bar"></div>
  <div class="hero-grid">
    <div>
      <div class="eyebrow">AIF1303 · AI Fundamentals · Final Project</div>
      <div class="hero-title">SteppeGuard <span class="c-cyan">AI</span></div>
      <div class="hero-sub">3D Wildfire Risk Intelligence, Risk-Aware Routing &amp; Sequential Decision Support for Kazakhstan</div>
      <ul class="pts" style="font-size:21px;">
        <li><strong>Topic 1 (Week 8 + 6):</strong> Pure-NumPy Logistic Regression &amp; Gaussian NB + Live Watchtower Bayes</li>
        <li><strong>Topic 2 (Week 2):</strong> Risk-Aware A* Search vs UCS &amp; BFS (-98.3% fire risk)</li>
        <li><strong>Topic 3 (Week 5):</strong> 8-State MDP Bellman Value Iteration + γ Sensitivity</li>
      </ul>
      <div class="hero-qr-card">
        <img src="{qr_demo}" alt="QR Live 3D Demo">
        <div>
          <div style="font-size:24px;font-weight:800;color:#f8fafc;">Oral Sanzhar <span style="font-size:16px;color:#fbbf24;font-weight:700;">(Solo Project)</span></div>
          <div style="font-size:18px;color:#cbd5e1;margin-top:4px;">Stream 1, Practice 4 · 6B06101 AI and ML · QAIRU</div>
          <div style="font-size:17px;font-family:Consolas,monospace;color:#4ade80;margin-top:10px;font-weight:700;">▶ steppeguard-ai.vercel.app</div>
          <div style="font-size:16px;font-family:Consolas,monospace;color:#38bdf8;margin-top:4px;">★ github.com/sazmak/steppeguard-ai</div>
          <div style="font-size:14px;color:#94a3b8;margin-top:6px;">Scan QR code to try the live 3D simulator on your phone</div>
        </div>
      </div>
    </div>
    <div class="img-wrap">
      <img src="{img_3d}" alt="SteppeGuard 3D Command Center">
      <div class="img-cap" style="color:#fbbf24;">
        <strong>100% Offline Three.js 3D Command Center</strong> · Live HTTPS &amp; Localhost Demo<br>
        <span style="color:#cbd5e1;">Synthetic simulation telemetry · Human-in-the-Loop Decision Support (RK AI Law No. 230-VIII ZRK)</span>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>SteppeGuard AI · Oral Sanzhar (Stream 1, Practice 4 · 6B06101 AI &amp; ML)</span>
    <span>Slide 1 / 7</span>
  </div>
</section>

<!-- SLIDE 2: PROBLEM, PEAS & PIPELINE -->
<section class="slide" id="slide-2">
  <div class="top-bar"></div>
  <div class="hdr">
    <div class="eyebrow">1. Problem Statement &amp; System Architecture (2 min)</div>
    <div class="title">Problem Statement, PEAS &amp; Integrated AI Pipeline</div>
    <div class="subtitle">From Kazakhstan steppe wildfire dispatch to DATA → PREDICTION → ROUTE → POLICY (Lecture 1 &amp; Lecture 8)</div>
  </div>
  <div class="grid-2" style="flex:0 0 auto; margin-bottom:26px;">
    <div class="card card-orange">
      <h3 class="c-orange">Real-World Challenge (Abai · Kostanay · Akmola)</h3>
      <ul class="pts">
        <li>Dry steppe grasslands &amp; high winds drive rapid, unpredictable wildfire spread.</li>
        <li>Shortest-path routing (BFS) sends crews straight through active burning zones.</li>
        <li>Noisy weather telemetry requires probabilistic risk estimation + long-term foresight.</li>
        <li><strong>Objective:</strong> build a transparent, 100% offline 3D AI/ML decision-support platform.</li>
      </ul>
    </div>
    <div class="card card-cyan">
      <h3 class="c-cyan">PEAS Formalization (Week 1, Slide 4)</h3>
      <ul class="pts">
        <li><strong>Performance (P):</strong> High wildfire Recall, low route fire exposure, maximum V*(s).</li>
        <li><strong>Environment (E):</strong> 10×10 steppe grid, terrain, obstacles, wind, Base (5,0) → Settlement (5,9).</li>
        <li><strong>Actuators (A):</strong> Risk alerts, safe route, MDP policy gated by Human-in-the-Loop approval.</li>
        <li><strong>Sensors (S):</strong> 5 telemetry features + noisy Watchtower Smoke Sensor (TPR=0.90, FPR=0.10).</li>
      </ul>
    </div>
  </div>
  <div style="margin-top:4px;">
    <img src="{img_pipe}" style="width:100%;height:auto;border-radius:14px;display:block;" alt="AI Pipeline">
  </div>
  <div class="footer">
    <span>SteppeGuard AI · Oral Sanzhar (Stream 1, Practice 4 · 6B06101 AI &amp; ML)</span>
    <span>Slide 2 / 7</span>
  </div>
</section>

<!-- SLIDE 3: TOPIC 1 ML + BAYES -->
<section class="slide" id="slide-3">
  <div class="top-bar"></div>
  <div class="hdr">
    <div class="eyebrow">2. Topic 1 · Classical Machine Learning (Week 8) + Bayes Bridge (Week 6)</div>
    <div class="title">Wildfire Probability Prediction &amp; Live Sensor Updating</div>
    <div class="subtitle">Pure-NumPy Logistic Regression vs Gaussian Naive Bayes with cost-aware validation thresholding</div>
  </div>
  <div class="grid-topic">
    <div class="card card-cyan" style="display:flex;flex-direction:column;justify-content:space-between;">
      <div>
        <h3 class="c-cyan">How It Works (Clear &amp; Transparent)</h3>
        <ul class="pts">
          <li><strong>Analogy:</strong> Weighs 5 weather clues into score <code>z = wᵀx + b</code>, then sigmoid <code>σ(z)</code> outputs 0–100% fire probability.</li>
          <li><strong>Zero Leakage:</strong> 30 scene-grouped splits (60% train / 20% val / 20% test); <code>StandardScaler</code> fit strictly on train.</li>
          <li><strong>Cost-Aware Threshold (Lecture 8, Slide 60):</strong> Missing fire (FN) costs 2× false alarm → val-tuned <code>τ ≈ 0.353</code> lifts Recall <strong>78.3% → 86.8%</strong>.</li>
          <li><strong>Honest 30-Seed Results:</strong> LogReg F1 <code>80.6%</code> (Brier <code>0.085</code> vs <code>~0.22</code> baseline) comparable to Gaussian NB F1 <code>79.9%</code>.</li>
          <li><strong>Week 6 Bayes Bridge:</strong> Watchtower smoke alert updates <code>P(Fire|E)</code> live &amp; triggers immediate A* + MDP replanning.</li>
        </ul>
      </div>
      <div class="mono-box">
        Abai Sector (5,4): z = +8.21 → P(Fire|x) = 99.97% (ALERT)<br>
        Akmola Watchtower Bayes (5,4): 9.7% → 49.2% after Smoke Alert
      </div>
    </div>
    <div class="img-wrap">
      <img src="{img_ml}" alt="ML Evaluation">
      <div class="img-cap">
        <strong>Figure 1 (30 Independent Seeds):</strong> Val-tuned Logistic Regression boosts wildfire Recall by +8.5 percentage points while keeping false negatives low (only 11 FN on test split).
      </div>
    </div>
  </div>
  <div class="footer">
    <span>SteppeGuard AI · Oral Sanzhar (Stream 1, Practice 4 · 6B06101 AI &amp; ML)</span>
    <span>Slide 3 / 7</span>
  </div>
</section>

<!-- SLIDE 4: TOPIC 2 RISK-AWARE A* -->
<section class="slide" id="slide-4">
  <div class="top-bar"></div>
  <div class="hdr">
    <div class="eyebrow">3. Topic 2 · Informed Heuristic Search (Week 2)</div>
    <div class="title">Risk-Aware A* Search vs UCS &amp; Unweighted BFS</div>
    <div class="subtitle">ML fire probabilities become dynamic terrain costs — exact UCS optimality with ~49% fewer expanded nodes</div>
  </div>
  <div class="grid-topic">
    <div class="card card-green" style="display:flex;flex-direction:column;justify-content:space-between;">
      <div>
        <h3 class="c-green">Algorithm &amp; Admissibility Proof</h3>
        <ul class="pts">
          <li><strong>Analogy:</strong> GPS navigator treating burning steppe sectors as severe traffic jams.</li>
          <li><strong>ML → Search Integration:</strong> Step cost <code>c(v) = c_terrain(v) + 3.5 · P(Fire|x_v)</code>.</li>
          <li><strong>Admissible Heuristic (Lecture 2, Slide 34):</strong> <code>h(n) = c_min · Manhattan(n, goal)</code> satisfies <code>0 ≤ h(n) ≤ h*(n)</code> everywhere.</li>
          <li><strong>100-Grid Property Test:</strong> A* matches UCS's exact optimal cost while cutting Abai fire exposure by <strong>98.3%</strong> vs BFS.</li>
        </ul>
      </div>
      <table class="tbl">
        <thead><tr><th>Abai (30 Seeds)</th><th>Nodes</th><th>Cost</th><th>Fire Exp.</th></tr></thead>
        <tbody>
          <tr class="hi"><td>Risk-Aware A*</td><td>41.5 ± 5.0</td><td>17.96</td><td>0.12</td></tr>
          <tr><td>UCS (h = 0)</td><td>80.8 ± 2.5</td><td>17.96</td><td>0.12</td></tr>
          <tr style="color:#fda4af;"><td>BFS (Unweighted)</td><td>71.0 ± 0.0</td><td>36.51</td><td>7.20</td></tr>
        </tbody>
      </table>
    </div>
    <div class="img-wrap">
      <img src="{img_search}" alt="Search Benchmark">
      <div class="img-cap">
        <strong>Figure 2 (30 Seeds Across All 3 Presets):</strong> Risk-Aware A* cuts node expansions by 48.7% on Abai (and 86.4% on Akmola) vs UCS, while avoiding the fire corridor that BFS enters blindly.
      </div>
    </div>
  </div>
  <div class="footer">
    <span>SteppeGuard AI · Oral Sanzhar (Stream 1, Practice 4 · 6B06101 AI &amp; ML)</span>
    <span>Slide 4 / 7</span>
  </div>
</section>

<!-- SLIDE 5: TOPIC 3 MDP VALUE ITERATION -->
<section class="slide" id="slide-5">
  <div class="top-bar"></div>
  <div class="hdr">
    <div class="eyebrow">4. Topic 3 · Sequential Decision Making (Week 5)</div>
    <div class="title">Markov Decision Process &amp; Bellman Value Iteration</div>
    <div class="subtitle">"Search returns a path; an MDP solution is a policy π*(s)" (Lecture 5, Slide 4)</div>
  </div>
  <div class="grid-topic">
    <div class="card card-amber" style="display:flex;flex-direction:column;justify-content:space-between;">
      <div>
        <h3 class="c-amber">Tightly Coupled 8-State × 5-Action MDP</h3>
        <ul class="pts">
          <li><strong>States (8):</strong> <code>{{Low, Med, High}} Risk × {{High, Low}} Resources</code> + terminal <code>Contained</code> &amp; <code>Escaped</code> (V=0).</li>
          <li><strong>Actions (5):</strong> Monitor, Direct Dispatch <em>(BFS exposure)</em>, Safe Detour <em>(A* exposure)</em>, Aerial Retardant <em>(resource-gated High→Low)</em>, Evacuate / Hold.</li>
          <li><strong>Bellman Optimality:</strong> <code>V_(k+1)(s) = max_a Σ P(s'|s,a)[R + γV_k(s')]</code> converges in <strong>17 sweeps</strong> (θ = 10⁻⁶).</li>
          <li><strong>3 Presets → 3 Policies:</strong> Akmola → <code>Direct Dispatch</code> · Kostanay → <code>Safe Detour</code> · Abai → <code>Aerial Retardant</code> (or <code>Evacuate</code> if Low Res).</li>
          <li><strong>γ Sensitivity:</strong> Myopic <code>γ=0.50</code> picks Aerial at Med/HighRes; farsighted <code>γ≥0.80</code> flips to <code>Safe Detour</code>.</li>
        </ul>
      </div>
      <div class="mono-box" style="color:#fde68a;border-color:rgba(245,158,11,0.45);">
        Counterfactual Coupling Test (PASSED): raising BFS exposure 0.3 → 7.5 drops Q(Direct) by &gt;10 pts &amp; flips policy to Safe Detour.
      </div>
    </div>
    <div class="img-wrap">
      <img src="{img_mdp}" alt="MDP Convergence">
      <div class="img-cap">
        <strong>Figure 3 (Bellman Convergence &amp; γ-Sensitivity):</strong> Geometric residual decay to θ = 10⁻⁶ in 17 sweeps; higher discount factor γ shifts preference toward long-term resource conservation.
      </div>
    </div>
  </div>
  <div class="footer">
    <span>SteppeGuard AI · Oral Sanzhar (Stream 1, Practice 4 · 6B06101 AI &amp; ML)</span>
    <span>Slide 5 / 7</span>
  </div>
</section>

<!-- SLIDE 6: LIVE 3D DEMO WALKTHROUGH -->
<section class="slide" id="slide-6">
  <div class="top-bar"></div>
  <div class="hdr">
    <div class="eyebrow">5. Live Interactive Demonstration (3–5 min)</div>
    <div class="title">Live 3D Command Center Walkthrough</div>
    <div class="subtitle">100% Offline WebGL (Three.js bundled locally) · 2D Canvas Fallback · Step-by-Step Math Inspector</div>
  </div>
  <div style="display:grid;grid-template-columns:1.35fr 0.65fr;gap:30px;flex:1;align-items:stretch;">
    <div class="img-wrap">
      <img src="{img_3d}" alt="Live 3D Demo">
      <div class="pill-row" style="margin-top:16px;justify-content:center;">
        <span class="pill p-green">● Live HTTPS: steppeguard-ai.vercel.app</span>
        <span class="pill p-cyan">● Offline Localhost Backup</span>
        <span class="pill p-amber">● 2:54 HD Demo Video Ready</span>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;justify-content:space-between;gap:14px;">
      <div class="step-item" style="border-left-color:#f97316;">
        <strong style="color:#fb923c;">Step 1 · Abai 3D Fire Corridor</strong>
        Click <em>Animate Search &amp; Drone</em> — watch green A* detour around 3D flames while red BFS cuts into fire (-99.2% risk).
      </div>
      <div class="step-item" style="border-left-color:#fbbf24;">
        <strong style="color:#fbbf24;">Step 2 · Resource Gating Flip</strong>
        Toggle Resources <em>High → Low</em> — MDP immediately switches from <code>Aerial Retardant</code> to <code>Evacuate / Hold</code>.
      </div>
      <div class="step-item" style="border-left-color:#4ade80;">
        <strong style="color:#4ade80;">Step 3 · Live Watchtower Bayes</strong>
        Switch to <em>Akmola</em> → trigger <em>Smoke Alert (+Bayes)</em> on (5,4) — fire belief jumps 9.7% → 49.2% and A* replans live!
      </div>
      <div class="step-item" style="border-left-color:#38bdf8;">
        <strong style="color:#38bdf8;">Step 4 · Math &amp; Benchmarks</strong>
        Approve via Human-in-the-Loop gate, toggle 2D Fallback, inspect live formulas &amp; 30-seed benchmarks.
      </div>
    </div>
  </div>
  <div class="footer">
    <span>SteppeGuard AI · Oral Sanzhar (Stream 1, Practice 4 · 6B06101 AI &amp; ML)</span>
    <span>Slide 6 / 7</span>
  </div>
</section>

<!-- SLIDE 7: VERIFICATION, RESPONSIBLE AI & DUAL QR Q&A -->
<section class="slide" id="slide-7">
  <div class="top-bar"></div>
  <div class="hdr">
    <div class="eyebrow">6. Verification, Responsible AI &amp; Q&amp;A</div>
    <div class="title">Testing, Kazakhstan AI Law Compliance &amp; Next Steps</div>
    <div class="subtitle">19 automated tests, 4 independent Claude Sonnet peer audits, and live scannable access</div>
  </div>
  <div class="grid-2" style="flex:0 0 auto;margin-bottom:26px;">
    <div class="card card-green">
      <h3 class="c-green">Verification &amp; Engineering Rigor</h3>
      <ul class="pts">
        <li><strong>19 / 19 pytest passing</strong> (unit, 100-grid optimality, 50-grid admissibility, counterfactual coupling, API validation).</li>
        <li><strong>30-seed benchmarks</strong> eliminate single-map cherry-picking across all 3 topics.</li>
        <li><strong>4 Claude Sonnet peer audits</strong> caught &amp; resolved heuristic strength, coupling, GNB parity &amp; UI race conditions.</li>
      </ul>
    </div>
    <div class="card card-amber">
      <h3 class="c-amber">Kazakhstan AI Law No. 230-VIII ZRK (17 Nov 2025)</h3>
      <ul class="pts">
        <li><strong>Risk Tier:</strong> High-Risk emergency domain (Course <code>AI_Legal_Framework.pptx</code>).</li>
        <li><strong>Autonomy Tier:</strong> Low Autonomy (Human-in-the-Loop approve/override gate).</li>
        <li><strong>Transparency &amp; Data:</strong> Synthetic telemetry clearly labeled; zero personal data; full AI Usage Declaration.</li>
      </ul>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1.18fr 0.82fr;gap:28px;flex:1;">
    <div class="card card-cyan">
      <h3 class="c-cyan">Limitations, Future Roadmap &amp; Ready for Q&amp;A</h3>
      <ul class="pts">
        <li><strong>Current Scope:</strong> Synthetic domain-inspired telemetry &amp; single-step grid per decision tick (explicitly disclosed per course rules).</li>
        <li><strong>Next Semester Expansion:</strong> Live Kazhydromet weather &amp; NASA FIRMS / MODIS fire feeds, Platt calibration, dynamic multi-step wind-spread automata, and POMDP / Deep RL control.</li>
        <li><strong>Thank you!</strong> Ready for Live Demo &amp; Questions — <strong>Oral Sanzhar (Stream 1, Practice 4)</strong>.</li>
      </ul>
    </div>
    <div class="card card-green" style="padding:20px 24px;">
      <div class="qr-dual">
        <div class="qr-unit">
          <img src="{qr_demo}" alt="QR Live 3D App">
          <div class="lbl">Live 3D Web App</div>
          <div class="url">steppeguard-ai.vercel.app</div>
        </div>
        <div class="qr-unit">
          <img src="{qr_git}" alt="QR GitHub Repo">
          <div class="lbl">GitHub Repo &amp; Video</div>
          <div class="url">sazmak/steppeguard-ai</div>
        </div>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>SteppeGuard AI · Oral Sanzhar (Stream 1, Practice 4 · 6B06101 AI &amp; ML)</span>
    <span>Slide 7 / 7</span>
  </div>
</section>

</body>
</html>
"""


def render_and_pack_pptx() -> None:
    html_path = SLIDE_DIR / "deck.html"
    html_path.write_text(build_slides_html(), encoding="utf-8")

    slide_pngs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE_EXE, headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        page.goto(html_path.as_uri(), wait_until="load")
        for i in range(1, 8):
            out_png = SLIDE_DIR / f"slide_{i}.png"
            page.locator(f"#slide-{i}").screenshot(path=str(out_png))
            slide_pngs.append(out_png)
        browser.close()

    pptx_path = DOCS / "SteppeGuard_Presentation.pptx"
    if pptx_path.exists():
        pptx_path.unlink()

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    notes_list = [
        "Slide 1 (Intro): Introduce SteppeGuard AI, 6B06101 AI & ML solo project by Oral Sanzhar. Invite graders to scan QR for live 3D app.",
        "Slide 2 (Problem & PEAS - 2 min): Explain Kazakhstan steppe wildfire challenge, PEAS formalization, and how ML -> A* -> MDP connect.",
        "Slide 3 (Topic 1 - Classical ML + Bayes): Pure-NumPy Logistic Regression vs Gaussian NB, val-tuned threshold tau=0.353 boosting Recall 78.3%->86.8%, Watchtower Bayes update.",
        "Slide 4 (Topic 2 - Risk-Aware A*): Dynamic step cost c(v) = terrain + 3.5*P(Fire), admissible c_min*Manhattan heuristic, -98.3% exposure vs BFS & -48.7% nodes vs UCS.",
        "Slide 5 (Topic 3 - MDP Value Iteration): 8 states x 5 actions, 17-sweep Bellman convergence, 3 presets -> 3 policies, gamma sensitivity flip & counterfactual coupling test.",
        "Slide 6 (Live 3D Demo - 3-5 min): Switch to live browser at steppeguard-ai.vercel.app (or offline localhost:8000) and run the 4-step live walkthrough.",
        "Slide 7 (Verification, RK Law & Q&A): 19/19 pytest, 4 Claude Sonnet audits, RK AI Law No. 230-VIII Low Autonomy Human-in-the-Loop, Dual QR codes for live app & GitHub.",
    ]

    for png_path, note in zip(slide_pngs, notes_list):
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        sl.shapes.add_picture(str(png_path), Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))
        sl.notes_slide.notes_text_frame.text = note

    prs.save(str(pptx_path))
    print(f"REBUILT CLEAN 7-SLIDE PPTX: {pptx_path} ({pptx_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    render_and_pack_pptx()
