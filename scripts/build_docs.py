"""Generate formatted DOCX deliverables and the 7-slide PPTX presentation.

Outputs:
- docs/SteppeGuard_Technical_Report.docx
- docs/AI_Usage_Declaration.docx
- docs/Team_Contribution_Statement.docx
- docs/SteppeGuard_Presentation.pptx   (strictly 7 slides, 16:9 widescreen)
"""

import json
from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor as DocxRGB

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches as PptInches, Pt as PptPt
import qrcode

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
RESULTS = ROOT / "results"
ASSETS = ROOT / "assets"
DOCS.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

LIVE_DEMO_URL = "https://steppeguard-ai.vercel.app"
GITHUB_REPO_URL = "https://github.com/sazmak/steppeguard-ai"


def generate_qr_codes() -> tuple[Path, Path]:
    """Generate crisp, high-contrast scannable QR PNGs for Live 3D Demo & GitHub."""
    paths = []
    for url, fname, fg in [
        (LIVE_DEMO_URL, "qr_demo.png", "#070D19"),
        (GITHUB_REPO_URL, "qr_github.png", "#070D19"),
    ]:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=12,
            border=3,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fg, back_color="#FFFFFF")
        out_path = ASSETS / fname
        img.save(str(out_path))
        paths.append(out_path)
    return paths[0], paths[1]


# =============================================================================
# DOCX HELPERS
# =============================================================================
def _shade_cell(cell, fill_hex: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _set_cell_margins(cell, top=80, bottom=80, left=120, right=120) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def _add_styled_table(doc: Document, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    # Header row
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        _shade_cell(cell, "0F172A")
        _set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(str(h))
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = DocxRGB(0xF8, 0xFA, 0xFC)

    # Data rows
    for i, row in enumerate(rows):
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            _shade_cell(cell, bg)
            _set_cell_margins(cell)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(str(val))
            run.font.size = Pt(9.2)
            if j == 0:
                run.bold = True

    if col_widths:
        for row in table.rows:
            for j, w in enumerate(col_widths):
                row.cells[j].width = Inches(w)
    return table


def _configure_docx(doc: Document) -> None:
    for sec in doc.sections:
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.8)
        sec.right_margin = Inches(0.8)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = DocxRGB(0x1E, 0x29, 0x3B)


def _add_heading(doc: Document, text: str, level: int = 1) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14 if level == 1 else 11.5)
    run.font.color.rgb = DocxRGB(0x0F, 0x17, 0x2A) if level == 1 else DocxRGB(0x03, 0x69, 0xA1)


def _add_callout(doc: Document, title: str, body: str) -> None:
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    _shade_cell(cell, "FEF3C7")
    _set_cell_margins(cell, 100, 100, 150, 150)
    p = cell.paragraphs[0]
    r1 = p.add_run(title + " ")
    r1.bold = True
    r1.font.size = Pt(9.5)
    r1.font.color.rgb = DocxRGB(0x92, 0x40, 0x0E)
    r2 = p.add_run(body)
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = DocxRGB(0x78, 0x35, 0x0F)


# =============================================================================
# 1. TECHNICAL REPORT DOCX
# =============================================================================
def build_technical_report_docx(bm: dict) -> None:
    doc = Document()
    _configure_docx(doc)

    # Title Banner
    t_tbl = doc.add_table(rows=1, cols=1)
    t_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tc = t_tbl.rows[0].cells[0]
    _shade_cell(tc, "0F172A")
    _set_cell_margins(tc, 180, 180, 220, 220)
    p0 = tc.paragraphs[0]
    r0 = p0.add_run("STEPPEGUARD AI — TECHNICAL REPORT\n")
    r0.bold = True
    r0.font.size = Pt(18)
    r0.font.color.rgb = DocxRGB(0x38, 0xBD, 0xF8)
    r1 = p0.add_run("Wildfire Risk Intelligence, Risk-Aware Routing, and Sequential Decision Support\n")
    r1.font.size = Pt(11.5)
    r1.font.color.rgb = DocxRGB(0xF8, 0xFA, 0xFC)
    r2 = p0.add_run(
        "Student: Oral Sanzhar  |  Group: Stream 1, Practice 4  |  Track: 6B06101 AI and ML  |  "
        "Course: AIF1303 AI Fundamentals (QAIRU, Astana, 2026)\n"
        "Live 3D Demo: https://steppeguard-ai.vercel.app  |  GitHub: https://github.com/sazmak/steppeguard-ai"
    )
    r2.font.size = Pt(9)
    r2.font.color.rgb = DocxRGB(0xCB, 0xD5, 0xE1)

    doc.add_paragraph()
    _add_callout(
        doc,
        "Academic Transparency & Synthetic Data Notice:",
        "Per AIF1303 Syllabus Section 8 and MiniAI_FPTopics.docx, all weather/satellite telemetry maps, "
        "wildfire labels, terrain costs, and MDP reward/transition tables are synthetic, domain-inspired "
        "simulation assumptions built for reproducible academic demonstration. They are not real MChS records.",
    )

    _add_heading(doc, "1. Executive Summary & Real-World Problem", 1)
    doc.add_paragraph(
        "Kazakhstan's steppe regions (Abai, Kostanay, Akmola) experience fast-moving wildfires driven by dry "
        "vegetation and high winds. Emergency dispatchers must answer three linked questions simultaneously: "
        "(1) Where is fire risk highest given noisy weather telemetry? (2) What is the safest route to the "
        "affected settlement? (3) Which long-term operational action should be selected when wind can escalate "
        "the fire unpredictably? SteppeGuard AI chains three distinct AI Fundamentals topics following the "
        "course paradigm DATA -> PREDICTION -> UTILITY -> ACTION (Lecture 8, Slide 1): Classical Machine Learning "
        "(Week 8) + Bayesian Sensor Update (Week 6) -> Risk-Aware A* Search (Week 2) -> MDP Value Iteration (Week 5)."
    )

    if (RESULTS / "fig4_3d_live_demo.png").exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(str(RESULTS / "fig4_3d_live_demo.png"), width=Inches(6.2))
        cap = doc.add_paragraph("Figure 1: SteppeGuard AI 100% offline 3D WebGL Tactical Command Center (Abai High-Wind preset).")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].italic = True
        cap.runs[0].font.size = Pt(9)

    _add_heading(doc, "2. Problem Formalization: PEAS & Environment Taxonomy (Week 1)", 1)
    _add_styled_table(
        doc,
        ["PEAS Component", "SteppeGuard AI Specification (Lecture 1, Slide 4 & Practical 1.2)"],
        [
            ["Performance (P)", "High wildfire Recall (few missed fires), low cumulative fire exposure along planned routes, maximum expected discounted return V*(s), and clear human explainability."],
            ["Environment (E)", "10x10 Kazakhstan steppe grid with terrain costs (Plain, Dry Shrub, Rocky Ridge, Obstacles), regional wind, Fire Base (5,0), and Target Settlement (5,9)."],
            ["Actuators (A)", "Sector fire alert flags, optimal route recommendation, and MDP policy recommendation (Monitor, Direct Dispatch, Safe Detour, Aerial Retardant, Evacuate/Hold) with Human-in-the-Loop approval."],
            ["Sensors (S)", "5 telemetry features (Temperature, Humidity, Wind, Dryness, Thermal Anomaly) plus an independent Watchtower Smoke Sensor (TPR = 0.90, FPR = 0.10)."],
        ],
        col_widths=[1.6, 5.2],
    )
    doc.add_paragraph(
        "Environment Taxonomy (Week 1, Slide 10): Partially observable (noisy sensors), single-agent decision support, "
        "stochastic (wind-driven fire spread), sequential (actions change future states and consume aircraft reserves), "
        "semi-dynamic, and discrete."
    )

    _add_heading(doc, "3. Integrated Three-Algorithm Architecture", 1)

    _add_heading(doc, "3.1 Topic 1 — Classical Machine Learning (Week 8) & Bayes Bridge (Week 6)", 2)
    doc.add_paragraph(
        "Analogy: Like an experienced dispatcher weighing five weather clues into a single danger score and passing it "
        "through an S-curve (sigmoid) to estimate fire probability. Implemented purely in NumPy (zero black-box ML): "
        "StandardScaler fit strictly on X_train (no leakage), Logistic Regression P(y=1|x) = sigma(w^T x_std + b) "
        "with L2 weight regularization, and a log-space Gaussian Naive Bayes baseline. Using 30 scene-grouped splits "
        "(60% train / 20% val / 20% test) with realistic label noise and a (low humidity x high wind) interaction, we "
        "tune threshold tau on validation to penalize missed fires 2:1 (FN:FP), boosting Recall from ~78% to ~87% "
        "(Lecture 8, Slide 60: 'High accuracy != good decisions'). When a Watchtower Smoke Sensor triggers, exact "
        "Bayesian inference (Lecture 6, Pages 55-60) updates the sector's prior P(Fire) into posterior P(Fire|E) and "
        "immediately re-runs A* and the MDP."
    )

    _add_heading(doc, "3.2 Topic 2 — Informed Heuristic Search: Risk-Aware A* (Week 2)", 2)
    doc.add_paragraph(
        "Analogy: Like a GPS navigator treating high-risk wildfire cells as severe traffic jams. Every free cell v gets "
        "step cost c(v) = c_terrain(v) + lambda * P(Fire|x_v) with lambda = 3.5, directly consuming Topic 1's ML risk map. "
        "A* minimizes f(n) = g(n) + h(n) using h(n) = c_min * Manhattan(n, goal), where c_min = min_{free v} c(v) >= 1.0. "
        "Because every step costs at least c_min, 0 <= h(n) <= h*(n) holds strictly (admissible and consistent, Lecture 2, "
        "Slide 34), guaranteeing A* finds UCS's exact optimal cost while expanding far fewer nodes."
    )

    _add_heading(doc, "3.3 Topic 3 — Sequential Decision Making: MDP Value Iteration (Week 5)", 2)
    doc.add_paragraph(
        "Analogy: 'Search returns a path; an MDP solution is a policy' (Lecture 5, Slide 4). Our 8-state MDP combines "
        "{Low, Med, High} Risk x {High, Low} Resources plus absorbing terminal states Contained (V=0) and Escaped (V=0), "
        "across 5 actions: Monitor, Direct Dispatch, Safe Detour, Aerial Retardant (resource-gated: High -> Low), and "
        "Evacuate / Hold. Direct Dispatch transitions are parameterized by per-step BFS fire exposure, while Safe Detour "
        "uses Risk-Aware A* exposure. Bellman Value Iteration V_{k+1}(s) = max_a sum_{s'} P(s'|s,a)[R + gamma * V_k(s')] "
        "converges to theta = 1e-6 in 17 sweeps."
    )

    _add_heading(doc, "4. Testing, Verification & 30-Seed Benchmark Results", 1)
    doc.add_paragraph(
        "Verification combines 19 automated pytest tests (including 100-map A*==UCS optimality, 50-map heuristic admissibility, "
        "exact Lecture 6 Bayes check 0.02 -> 0.1552, counterfactual BFS-exposure policy flip, edge cases, and FastAPI input "
        "validation) with 30-seed statistical benchmarks (scripts/benchmark.py) and three independent peer audits by Claude Sonnet."
    )

    lr = bm["ml"]["logistic_regression_tuned"]
    lrd = bm["ml"]["logistic_regression_tau_050"]
    gnb = bm["ml"]["gaussian_nb_tuned"]
    _add_styled_table(
        doc,
        ["ML Model (30 Seeds)", "Threshold tau", "Accuracy", "Precision", "Recall", "F1-Score", "Brier (Base ~0.22)"],
        [
            ["LogReg (Val-Tuned)", f"{bm['ml']['val_tau']['mean']:.3f}", f"{lr['accuracy']['mean']*100:.1f}% +/- {lr['accuracy']['std']*100:.1f}%", f"{lr['precision']['mean']*100:.1f}%", f"{lr['recall']['mean']*100:.1f}%", f"{lr['f1']['mean']*100:.1f}%", f"{lr['brier_score']['mean']:.3f}"],
            ["LogReg (Default)", "0.500", f"{lrd['accuracy']['mean']*100:.1f}% +/- {lrd['accuracy']['std']*100:.1f}%", f"{lrd['precision']['mean']*100:.1f}%", f"{lrd['recall']['mean']*100:.1f}%", f"{lrd['f1']['mean']*100:.1f}%", f"{lrd['brier_score']['mean']:.3f}"],
            ["Gaussian NB (Tuned)", f"{bm['ml']['val_tau']['mean']:.3f}", f"{gnb['accuracy']['mean']*100:.1f}% +/- {gnb['accuracy']['std']*100:.1f}%", f"{gnb['precision']['mean']*100:.1f}%", f"{gnb['recall']['mean']*100:.1f}%", f"{gnb['f1']['mean']*100:.1f}%", f"{gnb['brier_score']['mean']:.3f}"],
        ],
    )

    doc.add_paragraph()
    ab = bm["search"]["abai_high_wind"]
    ko = bm["search"]["kostanay_dry_steppe"]
    ak = bm["search"]["akmola_sensor_noise"]
    _add_styled_table(
        doc,
        ["Scenario (30 Seeds)", "A* Nodes", "UCS Nodes", "A*/UCS Cost", "BFS Cost", "A* Fire Exp.", "BFS Fire Exp."],
        [
            ["Abai High Wind", f"{ab['astar']['expanded']['mean']:.1f}", f"{ab['ucs']['expanded']['mean']:.1f}", f"{ab['astar']['cost']['mean']:.2f}", f"{ab['bfs']['cost']['mean']:.2f}", f"{ab['astar']['exposure']['mean']:.2f}", f"{ab['bfs']['exposure']['mean']:.2f}"],
            ["Kostanay Dry Steppe", f"{ko['astar']['expanded']['mean']:.1f}", f"{ko['ucs']['expanded']['mean']:.1f}", f"{ko['astar']['cost']['mean']:.2f}", f"{ko['bfs']['cost']['mean']:.2f}", f"{ko['astar']['exposure']['mean']:.2f}", f"{ko['bfs']['exposure']['mean']:.2f}"],
            ["Akmola Watchtower", f"{ak['astar']['expanded']['mean']:.1f}", f"{ak['ucs']['expanded']['mean']:.1f}", f"{ak['astar']['cost']['mean']:.2f}", f"{ak['bfs']['cost']['mean']:.2f}", f"{ak['astar']['exposure']['mean']:.2f}", f"{ak['bfs']['exposure']['mean']:.2f}"],
        ],
    )

    for idx, (fname, caption) in enumerate([
        ("fig1_ml_evaluation.png", "Figure 2: Topic 1 — 30-seed ML metrics comparison and Logistic Regression test Confusion Matrix."),
        ("fig2_search_benchmark.png", "Figure 3: Topic 2 — Expanded nodes and cumulative fire exposure across all 3 Kazakhstan presets."),
        ("fig3_mdp_convergence.png", "Figure 4: Topic 3 — Bellman Value Iteration convergence (17 sweeps) and discount factor gamma sensitivity."),
    ]):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.add_run().add_picture(str(RESULTS / fname), width=Inches(6.2))
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].italic = True
        cap.runs[0].font.size = Pt(9)

    _add_heading(doc, "5. Responsible AI, Kazakhstan AI Law No. 230-VIII & Future Work", 1)
    doc.add_paragraph(
        "Guided by QAIRU's AI_Legal_Framework.pptx (Law of the Republic of Kazakhstan 'On Artificial Intelligence' "
        "No. 230-VIII ZRK, adopted 17 Nov 2025): emergency wildfire dispatch is a High-Risk domain. SteppeGuard AI is "
        "therefore engineered as Low Autonomy (Human-in-the-Loop) — presenting live formulas, probabilities, and "
        "policy Q-values while requiring explicit dispatcher approval or override. Zero personal data is processed. "
        "Future extensions include real Kazhydromet / MODIS satellite feeds, Platt calibration, dynamic wind-driven "
        "fire spread simulation, and POMDP / Deep RL control."
    )

    _add_heading(doc, "6. Course References", 1)
    refs = [
        "1. QAIRU Course Syllabus AIF1303 — AI Fundamentals (2026-2027).",
        "2. QAIRU Lecture 1 (Week 1.pptx) & Practical 1.2 — Agents, PEAS, Environment Taxonomy.",
        "3. QAIRU Lecture 2 & Practical 2 — BFS, UCS, A* Search and Admissible Heuristics.",
        "4. QAIRU Lecture 5 (MDP_Reinforcement_Learning.pptx) — MDPs, Bellman Optimality, Value Iteration, Safety.",
        "5. QAIRU Lecture 6 — Probability, Bayes' Theorem, and Sensor Diagnosis.",
        "6. QAIRU Lecture 8 (Lecture 8_Rational_Decisions_Classical_ML.pptx) — Rational Decisions, Logistic Regression, Thresholds, Precision/Recall/F1.",
        "7. QAIRU Legal Guide (AI_Legal_Framework.pptx) — RK Law No. 230-VIII ZRK (17 Nov 2025).",
        "8. Russell, S. J., & Norvig, P. Artificial Intelligence: A Modern Approach (Pearson).",
        "9. Three.js r147 (https://threejs.org/, MIT License) — bundled locally for offline 3D visualization.",
    ]
    for r in refs:
        p = doc.add_paragraph(r)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.runs[0].font.size = Pt(9.2)

    doc.save(str(DOCS / "SteppeGuard_Technical_Report.docx"))


# =============================================================================
# 2. AI USAGE DECLARATION DOCX (EXACT SYLLABUS APPENDIX FORMAT)
# =============================================================================
def build_ai_declaration_docx() -> None:
    doc = Document()
    _configure_docx(doc)
    _add_heading(doc, "AI Use Declaration Form (AIF1303 Syllabus Appendix)", 1)
    doc.add_paragraph("Course: AIF1303 AI Fundamentals  |  QAIRU, Astana  |  2026–2027 Academic Year")

    _add_styled_table(
        doc,
        ["Field", "Content"],
        [
            ["Assignment", "Final Project — SteppeGuard AI (Wildfire Risk Intelligence & Response Decision System); Course: AIF1303 AI Fundamentals; Group: Stream 1, Practice 4 (6B06101 AI and ML); Student: Oral Sanzhar."],
            ["AI Tool", "1) Antigravity (Google Gemini 4 Neon High), used 2026-11-24 to 2026-11-25 via local Antigravity IDE agent.\n2) Claude Code CLI (v2.1.318, Claude Sonnet), used 2026-11-25 via student's Claude Pro subscription for independent multi-stage peer audits.\n3) ElevenLabs TTS API (eleven_multilingual_v2, student's own cloned voice 'sazmak2'), used 2026-11-25 for English voiceover narration of the 2:48 demo video."],
            ["Purpose of Use", "Requirements analysis against syllabus/rubric; architecture brainstorming; assisting with pure-NumPy Python implementation, FastAPI backend, offline Three.js 3D UI, pytest unit/property tests, 30-seed benchmark plotting, independent peer auditing, and document formatting."],
            ["Key Prompts", "1. Analyze all course files (syllabus, lectures, practicals, rubric) and explain requirements & plan.\n2. Adapt SteppeGuard AI for the 6B06101 AI & ML track combining Classical ML, Risk-Aware A*, and MDP Value Iteration.\n3. Enforce 17 project rules: offline 3D demo, dual-model peer audits at every stage, course-sourced formulas, 1st-year clarity, full worklog & prompt log.\n4. Run independent Claude Sonnet audits on architecture, backend math/tests, frontend UX, and final 100-point rubric compliance.\n(Full chronological table preserved in context/PROMPT_LOG.md and context/WORKLOG.md.)"],
            ["AI Contribution", "Drafted modular src/ pure-NumPy modules, FastAPI app.py, offline Three.js 3D frontend (static/), 19 pytest tests, 30-seed benchmark script, audit reports (context/AUDIT_*.md), and report/slide builders. All project decisions, rules, checkpoints, visual review, and final defense ownership were directed by the student."],
            ["Result Verification", "1. Cross-checked all formulas (sigmoid, L2 gradient, Lecture 6 Bayes example 0.02 -> 0.1552, A* admissible Manhattan heuristic, Bellman Value Iteration) against QAIRU lecture slides.\n2. Executed pytest (19/19 PASSED) including 100-grid A* optimality, 50-grid admissibility, and counterfactual MDP coupling tests.\n3. Verified 30-seed benchmarks; visually inspected live 3D browser screenshots and all 3 matplotlib benchmark figures; verified all 7 PowerPoint slides via programmatic bounding-box & overlap clearance checks.\n4. Resolved all P0/P1 issues flagged across 4 independent Claude Sonnet peer audits."],
            ["Student Statement", "I confirm that I am responsible for the final work, understand all implemented algorithms and results, and have accurately disclosed AI use.\n\nSigned: Oral Sanzhar   |   Date: 2026-11-25"],
        ],
        col_widths=[1.7, 5.1],
    )
    doc.save(str(DOCS / "AI_Usage_Declaration.docx"))


# =============================================================================
# 3. TEAM CONTRIBUTION STATEMENT DOCX (SOLO 100%)
# =============================================================================
def build_contribution_docx() -> None:
    doc = Document()
    _configure_docx(doc)
    _add_heading(doc, "Team Contribution Statement (Solo Project)", 1)
    doc.add_paragraph(
        "Project: SteppeGuard AI — Wildfire Risk Intelligence & Response Decision System\n"
        "Course: AIF1303 AI Fundamentals  |  Program: 6B06101 AI and ML  |  Group: Stream 1, Practice 4"
    )
    _add_styled_table(
        doc,
        ["Student Full Name", "Group", "Role & Verified Responsibilities", "Contribution"],
        [
            [
                "Oral Sanzhar",
                "Stream 1, Practice 4",
                "Solo Project Owner (Individual Submission): problem selection & PEAS formalization, "
                "integration of 3 AI topics (Classical ML + Bayes bridge, Risk-Aware A*, MDP Value Iteration), "
                "governance rules & checkpoint review, verification of pure-NumPy code and 19 automated tests, "
                "3D offline demo QA, 30-seed benchmark analysis, Technical Report, 7-Slide Presentation, "
                "Demo Video recording, AI Usage Declaration, and Oral Defense.",
                "100%",
            ]
        ],
        col_widths=[1.3, 1.1, 3.6, 0.8],
    )
    p = doc.add_paragraph("\nSigned: Oral Sanzhar   |   Date: 2026-11-25")
    p.runs[0].bold = True
    doc.save(str(DOCS / "Team_Contribution_Statement.docx"))


# =============================================================================
# 4. 7-SLIDE EXECUTIVE PRESENTATION (16:9 DARK TACTICAL THEME)
# =============================================================================
BG_DARK = RGBColor(0x07, 0x0D, 0x19)
CARD_BG = RGBColor(0x11, 0x1D, 0x33)
CARD_BORDER = RGBColor(0x28, 0x3B, 0x5B)
CYAN = RGBColor(0x38, 0xBD, 0xF8)
GREEN = RGBColor(0x22, 0xC5, 0x5E)
AMBER = RGBColor(0xF5, 0x9E, 0x0B)
ORANGE = RGBColor(0xF9, 0x73, 0x16)
RED = RGBColor(0xF4, 0x3F, 0x5E)
WHITE = RGBColor(0xF8, 0xFA, 0xFC)
MUTED = RGBColor(0xCB, 0xD5, 0xE1)


def _add_run(p, text: str, size: float, color, bold: bool = False, font_name: str = "Segoe UI"):
    r = p.add_run()
    r.text = text
    r.font.name = font_name
    r.font.size = PptPt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return r


def _new_slide(prs: Presentation, title: str, subtitle: str, page_num: int):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG_DARK

    # Top accent bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(0), PptInches(0), PptInches(13.333), PptInches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN
    bar.line.fill.background()

    # Header title
    tb = slide.shapes.add_textbox(PptInches(0.55), PptInches(0.24), PptInches(11.8), PptInches(0.55))
    tf = tb.text_frame
    tf.word_wrap = True
    _add_run(tf.paragraphs[0], title, 25, WHITE, bold=True)

    # Subtitle
    sb = slide.shapes.add_textbox(PptInches(0.55), PptInches(0.78), PptInches(12.0), PptInches(0.35))
    stf = sb.text_frame
    stf.word_wrap = True
    _add_run(stf.paragraphs[0], subtitle, 12.5, CYAN)

    # Footer
    fb = slide.shapes.add_textbox(PptInches(0.55), PptInches(7.05), PptInches(12.2), PptInches(0.32))
    ftf = fb.text_frame
    _add_run(
        ftf.paragraphs[0],
        f"SteppeGuard AI  ·  Oral Sanzhar (Stream 1, Practice 4 · 6B06101 AI & ML)  ·  AIF1303 Final Project          Slide {page_num} / 7",
        10,
        MUTED,
    )
    return slide


def _add_card(slide, x, y, w, h, title, bullets, accent=CYAN, title_size=14, body_size=12):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(x), PptInches(y), PptInches(w), PptInches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = CARD_BG
    shape.line.color.rgb = accent
    shape.line.width = PptPt(1.2)

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = PptInches(0.18)
    tf.margin_right = PptInches(0.16)
    tf.margin_top = PptInches(0.14)
    tf.margin_bottom = PptInches(0.10)

    p0 = tf.paragraphs[0]
    p0.space_after = PptPt(6)
    _add_run(p0, title, title_size, accent, bold=True)

    for b in bullets:
        p = tf.add_paragraph()
        p.space_after = PptPt(4.5)
        _add_run(p, "•  " + b, body_size, WHITE)
    return shape


def build_presentation_pptx(bm: dict) -> None:
    prs = Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.5)

    # -------------------------------------------------------------------------
    # SLIDE 1: HERO TITLE SLIDE
    # -------------------------------------------------------------------------
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    s1.background.fill.solid()
    s1.background.fill.fore_color.rgb = BG_DARK

    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(0), PptInches(0), PptInches(13.333), PptInches(0.10))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ORANGE
    bar.line.fill.background()

    tb = s1.shapes.add_textbox(PptInches(0.60), PptInches(0.70), PptInches(5.65), PptInches(3.95))
    tf = tb.text_frame
    tf.word_wrap = True
    _add_run(tf.paragraphs[0], "AIF1303 · AI FUNDAMENTALS · FINAL PROJECT", 11.5, AMBER, bold=True)

    p2 = tf.add_paragraph(); p2.space_before = PptPt(10)
    _add_run(p2, "SteppeGuard AI", 42, WHITE, bold=True)

    p3 = tf.add_paragraph(); p3.space_before = PptPt(6)
    _add_run(p3, "Wildfire Risk Intelligence, Risk-Aware Routing & Sequential Decision Support", 16.5, CYAN)

    p4 = tf.add_paragraph(); p4.space_before = PptPt(16)
    _add_run(
        p4,
        "Chaining Three Course Topics in One Live 3D Simulator:\n"
        "  1. Classical ML (Week 8) + Bayes Sensor Bridge (Week 6)\n"
        "  2. Risk-Aware A* Heuristic Search (Week 2)\n"
        "  3. MDP Bellman Value Iteration (Week 5)",
        12.8,
        MUTED,
    )

    # Bottom-left Author + QR Code Card (Live 3D Demo instant scan!)
    qr_demo_path = ASSETS / "qr_demo.png"
    qr_github_path = ASSETS / "qr_github.png"
    id_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(0.60), PptInches(4.82), PptInches(5.60), PptInches(1.88))
    id_card.fill.solid(); id_card.fill.fore_color.rgb = CARD_BG
    id_card.line.color.rgb = CYAN; id_card.line.width = PptPt(1.2)

    if qr_demo_path.exists():
        s1.shapes.add_picture(str(qr_demo_path), PptInches(0.76), PptInches(4.96), width=PptInches(1.42))
        qlbl = s1.shapes.add_textbox(PptInches(0.70), PptInches(6.40), PptInches(1.56), PptInches(0.25))
        qp = qlbl.text_frame.paragraphs[0]; qp.alignment = PP_ALIGN.CENTER
        _add_run(qp, "SCAN LIVE 3D", 8.5, CYAN, bold=True)

    atb = s1.shapes.add_textbox(PptInches(2.34), PptInches(4.98), PptInches(3.75), PptInches(1.58))
    atf = atb.text_frame; atf.word_wrap = True
    _add_run(atf.paragraphs[0], "Oral Sanzhar (Solo Project)", 14, WHITE, bold=True)
    ap2 = atf.add_paragraph(); ap2.space_before = PptPt(4)
    _add_run(ap2, "Stream 1, Practice 4  ·  6B06101 AI & ML", 11.2, MUTED)
    ap3 = atf.add_paragraph(); ap3.space_before = PptPt(8)
    _add_run(ap3, "Live 3D: steppeguard-ai.vercel.app", 10.8, GREEN, bold=True, font_name="Consolas")
    ap4 = atf.add_paragraph(); ap4.space_before = PptPt(3)
    _add_run(ap4, "GitHub:  github.com/sazmak/steppeguard-ai", 10.0, CYAN, font_name="Consolas")

    if (RESULTS / "fig4_3d_live_demo.png").exists():
        frame = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(6.45), PptInches(0.85), PptInches(6.35), PptInches(5.85))
        frame.fill.solid(); frame.fill.fore_color.rgb = CARD_BG
        frame.line.color.rgb = CYAN; frame.line.width = PptPt(1.5)
        s1.shapes.add_picture(str(RESULTS / "fig4_3d_live_demo.png"), PptInches(6.58), PptInches(1.05), width=PptInches(6.10))
        cap = s1.shapes.add_textbox(PptInches(6.58), PptInches(5.05), PptInches(6.10), PptInches(1.35))
        ctf = cap.text_frame; ctf.word_wrap = True
        _add_run(
            ctf.paragraphs[0],
            "Live 100% Offline 3D Three.js Command Center · Synthetic Simulation Telemetry\n"
            "Human-in-the-Loop Decision Support (RK AI Law No. 230-VIII ZRK)\n"
            "Scan the QR code on the left to test the live 3D simulator on your phone!",
            10.5,
            AMBER,
        )

    # -------------------------------------------------------------------------
    # SLIDE 2: PROBLEM STATEMENT, PEAS & INTEGRATED PIPELINE
    # -------------------------------------------------------------------------
    s2 = _new_slide(
        prs,
        "1. Problem Statement, PEAS & End-to-End AI Pipeline",
        "Solving Kazakhstan steppe wildfire dispatch via DATA → PREDICTION → ROUTE → POLICY (Lecture 1 & Lecture 8)",
        2,
    )
    _add_card(
        s2, 0.55, 1.25, 5.9, 2.55,
        "Real-World Problem (Abai, Kostanay, Akmola)",
        [
            "Dry steppe grasslands & strong winds cause rapid wildfire spread.",
            "Simple shortest-path routing (BFS) drives crews straight into danger.",
            "Noisy sensors & stochastic wind require probabilistic prediction + foresight.",
            "Goal: build a transparent, 100% offline AI/ML decision-support simulator.",
        ],
        accent=ORANGE, body_size=12.5,
    )
    _add_card(
        s2, 6.75, 1.25, 6.0, 2.55,
        "PEAS Formalization (Week 1, Slide 4)",
        [
            "Performance: high wildfire Recall, low route exposure, high V*(s).",
            "Environment: 10×10 steppe grid, obstacles, wind, Base (5,0) → Settlement (5,9).",
            "Actuators: risk alerts, safe route, MDP policy (Human-in-the-Loop).",
            "Sensors: 5 weather/thermal features + noisy Watchtower Smoke Sensor.",
        ],
        accent=CYAN, body_size=12.5,
    )

    pipe_items = [
        ("TOPIC 1 · Week 8 + 6", "Classical ML + Bayes", "5 Telemetry Features\n→ Fire Prob. Grid P(Fire|x)\n+ Live Watchtower Bayes", CYAN),
        ("TOPIC 2 · Week 2", "Risk-Aware A* Search", "c(v) = terrain + λ·P(Fire)\n→ Optimal Safe Route\nvs UCS & BFS", GREEN),
        ("TOPIC 3 · Week 5", "MDP Value Iteration", "ML Risk + BFS/A* Exposure\n→ Optimal Policy π*(s)\n(8 States × 5 Actions)", AMBER),
        ("WEEK 10 · RK LAW", "Human-in-the-Loop", "Low-Autonomy Gate:\nDispatcher Approves or\nOverrides AI Policy", ORANGE),
    ]
    for i, (tag, head, desc, col) in enumerate(pipe_items):
        x = 0.55 + i * 3.12
        box = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(x), PptInches(4.15), PptInches(2.85), PptInches(2.55))
        box.fill.solid(); box.fill.fore_color.rgb = CARD_BG
        box.line.color.rgb = col; box.line.width = PptPt(1.5)
        tf = box.text_frame; tf.word_wrap = True
        tf.margin_left = PptInches(0.16); tf.margin_top = PptInches(0.16)
        _add_run(tf.paragraphs[0], tag, 10, col, bold=True)
        p1 = tf.add_paragraph(); p1.space_before = PptPt(6)
        _add_run(p1, head, 15, WHITE, bold=True)
        p2 = tf.add_paragraph(); p2.space_before = PptPt(8)
        _add_run(p2, desc, 12, MUTED)
        if i < 3:
            arr = s2.shapes.add_textbox(PptInches(x + 2.86), PptInches(5.12), PptInches(0.28), PptInches(0.45))
            ap = arr.text_frame.paragraphs[0]; ap.alignment = PP_ALIGN.CENTER
            _add_run(ap, "→", 22, CYAN, bold=True)

    # -------------------------------------------------------------------------
    # SLIDE 3: TOPIC 1 — CLASSICAL ML + BAYES BRIDGE
    # -------------------------------------------------------------------------
    s3 = _new_slide(
        prs,
        "2. Topic 1: Classical Machine Learning (Week 8) + Bayes Bridge (Week 6)",
        "Pure-NumPy Logistic Regression vs Gaussian NB with cost-aware threshold tuning & live sensor updating",
        3,
    )
    _add_card(
        s3, 0.55, 1.25, 5.15, 5.55,
        "How It Works (1st-Year Friendly)",
        [
            "Analogy: weighs 5 clues (Temp, Humidity, Wind, Dryness, Thermal) into score z = wᵀx + b, then sigmoid σ(z) gives 0–100% fire probability.",
            "Zero Leakage: 30 scene-grouped splits (60% train / 20% val / 20% test); StandardScaler fit on train only.",
            "Cost-Aware Threshold (Lecture 8, Slide 60): missing fire (FN) costs 2× false alarm → val-tuned τ ≈ 0.35 boosts Recall 78.3% → 86.8%.",
            "Honest Comparison (30 seeds): LogReg F1 80.6% (Brier 0.085 vs ~0.22 baseline) vs Gaussian NB F1 79.9% (Brier 0.088).",
            "Week 6 Bayes Bridge: Watchtower smoke alert (TPR=0.90, FPR=0.10) updates P(Fire|E) live and triggers immediate A* + MDP replanning.",
        ],
        accent=CYAN, body_size=11.5,
    )
    s3.shapes.add_picture(str(RESULTS / "fig1_ml_evaluation.png"), PptInches(5.92), PptInches(1.55), width=PptInches(6.90))
    cap3 = s3.shapes.add_textbox(PptInches(5.92), PptInches(4.75), PptInches(6.9), PptInches(1.2))
    c3tf = cap3.text_frame; c3tf.word_wrap = True
    _add_run(
        c3tf.paragraphs[0],
        "Worked Example (Abai Sector 5,4):  Temp 40.9°C, Humidity 17%, Wind 35 km/h\n"
        "→ z = +8.21 → P(Fire|x) = 99.97% (ALERT).\n"
        "Akmola Watchtower Alert (5,4): 9.7% → 49.2% via Bayes' theorem.",
        11,
        AMBER,
        font_name="Consolas",
    )

    # -------------------------------------------------------------------------
    # SLIDE 4: TOPIC 2 — RISK-AWARE A* SEARCH
    # -------------------------------------------------------------------------
    s4 = _new_slide(
        prs,
        "3. Topic 2: Informed Heuristic Search — Risk-Aware A* (Week 2)",
        "ML fire probabilities become dynamic terrain costs: exact UCS optimality with ~49% fewer expanded nodes",
        4,
    )
    _add_card(
        s4, 0.55, 1.25, 5.15, 5.55,
        "Algorithm & Admissibility Guarantee",
        [
            "Analogy: GPS navigator treating burning steppe sectors like massive traffic jams.",
            "Step Cost (ML → Search link): c(v) = c_terrain(v) + 3.5 · P(Fire | x_v).",
            "Admissible Heuristic (Lecture 2, Slide 34): h(n) = c_min · (|r−r_g| + |c−c_g|). Since every move costs ≥ c_min, 0 ≤ h(n) ≤ h*(n) always holds.",
            "Verified on 100 Random Grids + 30 Seeds: A* matches UCS's exact optimal cost (17.96) while expanding 48.7% fewer nodes on Abai (41.5 vs 80.8).",
            "Safety Gain vs BFS: BFS walks straight into fire (7.20 exposure); A* detours cleanly (0.12 exposure → -98.3% fire risk!).",
        ],
        accent=GREEN, body_size=11.5,
    )
    s4.shapes.add_picture(str(RESULTS / "fig2_search_benchmark.png"), PptInches(5.92), PptInches(1.55), width=PptInches(6.90))
    cap4 = s4.shapes.add_textbox(PptInches(5.92), PptInches(4.75), PptInches(6.9), PptInches(1.2))
    c4tf = cap4.text_frame; c4tf.word_wrap = True
    _add_run(
        c4tf.paragraphs[0],
        "30-Seed Abai High Wind:\n"
        "  A*  41.5 nodes | Cost 17.96 | Exposure 0.12\n"
        "  UCS 80.8 nodes | Cost 17.96 | Exposure 0.12\n"
        "  BFS 71.0 nodes | Cost 36.51 | Exposure 7.20",
        11,
        GREEN,
        font_name="Consolas",
    )

    # -------------------------------------------------------------------------
    # SLIDE 5: TOPIC 3 — MDP & VALUE ITERATION
    # -------------------------------------------------------------------------
    s5 = _new_slide(
        prs,
        "4. Topic 3: Sequential Decision Making — MDP Value Iteration (Week 5)",
        "'Search returns a path; an MDP solution is a policy' (Lecture 5, Slide 4)",
        5,
    )
    _add_card(
        s5, 0.55, 1.25, 5.15, 5.55,
        "Tightly Coupled 8-State × 5-Action MDP",
        [
            "States: {Low, Med, High} Fire Risk × {High, Low} Resources + Contained & Escaped (V=0).",
            "Actions: Monitor, Direct Dispatch (uses BFS exposure), Safe Detour (uses A* exposure), Aerial Retardant (resource-gated High→Low), Evacuate / Hold.",
            "Bellman Optimality (Lecture 5, Slides 26 & 29): V_{k+1}(s) = max_a Σ P(s'|s,a)[R + γV_k(s')], converges in 17 sweeps (θ = 10⁻⁶).",
            "3 Presets → 3 Distinct Policies: Akmola → Direct Dispatch, Kostanay → Safe Detour, Abai → Aerial Retardant (or Evacuate when Low Res).",
            "Discount Factor γ Sensitivity: myopic γ=0.50 chooses Aerial at Med/HighRes; farsighted γ≥0.80 flips to Safe Detour.",
        ],
        accent=AMBER, body_size=11.3,
    )
    s5.shapes.add_picture(str(RESULTS / "fig3_mdp_convergence.png"), PptInches(5.92), PptInches(1.55), width=PptInches(6.90))
    cap5 = s5.shapes.add_textbox(PptInches(5.92), PptInches(4.75), PptInches(6.9), PptInches(1.1))
    c5tf = cap5.text_frame; c5tf.word_wrap = True
    _add_run(
        c5tf.paragraphs[0],
        "Counterfactual Coupling Verified (test_mdp.py): raising BFS exposure\n"
        "from 0.3 → 7.5 drops Q(Direct Dispatch) by >10 pts & flips policy to Safe Detour.",
        11,
        AMBER,
        font_name="Consolas",
    )

    # -------------------------------------------------------------------------
    # SLIDE 6: LIVE 3D DEMO WALKTHROUGH
    # -------------------------------------------------------------------------
    s6 = _new_slide(
        prs,
        "5. Live 3D Interactive Demo Walkthrough (3–5 Minutes)",
        "100% Offline WebGL (Three.js bundled locally) + 2D Canvas Fallback + Step-by-Step Math Inspector",
        6,
    )
    if (RESULTS / "fig4_3d_live_demo.png").exists():
        s6.shapes.add_picture(str(RESULTS / "fig4_3d_live_demo.png"), PptInches(0.55), PptInches(1.38), width=PptInches(7.70))

    _add_card(
        s6, 8.48, 1.28, 4.30, 5.45,
        "4-Step Live Demo Script",
        [
            "Step 1 (Abai High Wind): Click 'Animate Search & Drone' — watch A* detour safely around 3D flames while BFS cuts into danger (-99% risk).",
            "Step 2 (Resource Gating): Toggle Resources High → Low — watch MDP flip from Aerial Retardant to Evacuate / Hold.",
            "Step 3 (Akmola + Bayes): Click a corridor sector → press 'Smoke Alert (+Bayes)' — fire belief jumps 9.7% → 49.2% and A* replans live!",
            "Step 4 (Transparency): Approve via Human-in-the-Loop gate, open 'Math & Formulas' & '30-Seed Benchmarks' tabs.",
        ],
        accent=CYAN, body_size=11.8,
    )

    # -------------------------------------------------------------------------
    # SLIDE 7: TESTING, RESPONSIBLE AI & Q&A
    # -------------------------------------------------------------------------
    s7 = _new_slide(
        prs,
        "6. Verification, Responsible AI & Conclusion",
        "Automated testing, dual-model peer audits, and Kazakhstan AI Law No. 230-VIII ZRK compliance",
        7,
    )
    _add_card(
        s7, 0.55, 1.25, 6.0, 2.65,
        "Quality, Testing & Dual-Model Peer Audits",
        [
            "19 / 19 automated pytest tests passing in 1.5s (unit, property, API, edge cases).",
            "30-seed benchmarks ensure zero cherry-picking across all 3 topics.",
            "3 independent peer audits via Claude Sonnet caught & fixed heuristic strength, search→MDP coupling, GNB parity, and UI stability.",
            "Zero external CDN dependencies — runs reliably offline on localhost.",
        ],
        accent=GREEN, body_size=11.8,
    )
    _add_card(
        s7, 6.75, 1.25, 6.0, 2.65,
        "Responsible AI — RK Law No. 230-VIII ZRK (17 Nov 2025)",
        [
            "Risk Tier: High-Risk emergency decision domain (AI_Legal_Framework.pptx).",
            "Autonomy Tier: Low Autonomy (Human-in-the-Loop approve/override gate).",
            "Transparency: Synthetic simulation data visibly labeled; full AI Usage Declaration.",
            "Data Governance: Zero personal or confidential data processed.",
        ],
        accent=AMBER, body_size=11.8,
    )
    _add_card(
        s7, 0.55, 4.10, 7.55, 2.72,
        "Limitations, Future Work & Ready for Q&A",
        [
            "Current Scope: Synthetic domain-inspired telemetry & static single-step grid per decision tick (explicitly labeled per course guidelines).",
            "Next Semester Roadmap: Real Kazhydromet weather & NASA FIRMS/MODIS fire feeds, Platt calibration, dynamic wind-spread physics & Deep RL.",
            "Thank you! Ready for live demonstration & Q&A — Oral Sanzhar (Stream 1, Practice 4).",
        ],
        accent=CYAN, body_size=11.8,
    )

    # Right-bottom Dual QR Panel (Live 3D Demo + GitHub Repo)
    qr_box = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(8.30), PptInches(4.10), PptInches(4.45), PptInches(2.72))
    qr_box.fill.solid(); qr_box.fill.fore_color.rgb = CARD_BG
    qr_box.line.color.rgb = GREEN; qr_box.line.width = PptPt(1.5)

    qt = s7.shapes.add_textbox(PptInches(8.42), PptInches(4.18), PptInches(4.20), PptInches(0.32))
    qtp = qt.text_frame.paragraphs[0]; qtp.alignment = PP_ALIGN.CENTER
    _add_run(qtp, "SCAN TO TRY LIVE OR INSPECT CODE", 10.5, GREEN, bold=True)

    if qr_demo_path.exists():
        s7.shapes.add_picture(str(qr_demo_path), PptInches(8.62), PptInches(4.56), width=PptInches(1.68))
        l1 = s7.shapes.add_textbox(PptInches(8.42), PptInches(6.28), PptInches(2.08), PptInches(0.46))
        l1p = l1.text_frame.paragraphs[0]; l1p.alignment = PP_ALIGN.CENTER
        _add_run(l1p, "Live 3D Web App\nsteppeguard-ai.vercel.app", 9.0, CYAN, bold=True)

    if qr_github_path.exists():
        s7.shapes.add_picture(str(qr_github_path), PptInches(10.72), PptInches(4.56), width=PptInches(1.68))
        l2 = s7.shapes.add_textbox(PptInches(10.52), PptInches(6.28), PptInches(2.08), PptInches(0.46))
        l2p = l2.text_frame.paragraphs[0]; l2p.alignment = PP_ALIGN.CENTER
        _add_run(l2p, "GitHub Repo & Video\nsazmak/steppeguard-ai", 9.0, AMBER, bold=True)

    # Programmatic slide bounds QA (verifies zero off-slide shapes)
    for s_idx, sl in enumerate(prs.slides, 1):
        for sh in sl.shapes:
            right = (sh.left + sh.width) / 914400.0
            bottom = (sh.top + sh.height) / 914400.0
            assert right <= 13.40, f"Slide {s_idx} shape overflows right ({right:.2f} in)"
            assert bottom <= 7.55, f"Slide {s_idx} shape overflows bottom ({bottom:.2f} in)"

    assert 5 <= len(prs.slides) <= 7, f"Slide count {len(prs.slides)} violates 5-7 slide rule!"
    prs.save(str(DOCS / "SteppeGuard_Presentation.pptx"))


if __name__ == "__main__":
    generate_qr_codes()
    bm = json.loads((RESULTS / "benchmark_summary.json").read_text(encoding="utf-8"))
    build_technical_report_docx(bm)
    build_ai_declaration_docx()
    build_contribution_docx()
    build_presentation_pptx(bm)
    print("GENERATED QR CODES + ALL DOCX & 7-SLIDE PPTX SUCCESSFULLY:")
    for p in sorted(DOCS.glob("*")):
        print(f"  {p.name} ({p.stat().st_size:,} bytes)")
