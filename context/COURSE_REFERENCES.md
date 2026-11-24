# Course-Sourced Formulas, Notation & Citations

> **Rule #6 Compliance:** All core definitions, mathematical notation, and responsible-AI principles below are extracted directly from the AIF1303 course materials stored in `C:\Users\sazmak\Desktop\AIF FINAL\`.

---

## 1. Intelligent Agents & PEAS (`Week 1.pptx`, `AIF_Practical_1.2.docx`)
- **Design Workflow** (`Week 1.pptx`, Slide 38): `PEAS → Environment Taxonomy → Representation → Architecture → Evaluation`.
- **PEAS** (`Week 1.pptx`, Slide 4):
  - **P (Performance measure):** What counts as success (e.g., high wildfire recall, safe low-risk routes, high expected long-term return, timely containment).
  - **E (Environment):** 10×10 Kazakhstan steppe grid with heterogeneous terrain, wind/weather telemetry, obstacles, and stochastic fire evolution.
  - **A (Actuators):** Route recommendation, sector alert flag, and operational dispatch action (`Direct Dispatch`, `Safe Detour`, `Aerial Retardant`, `Sensor Re-scan`, `Evacuate / Hold`).
  - **S (Sensors):** Sector telemetry features (Temperature °C, Humidity %, Wind Speed km/h, Vegetation Dryness/NDVI, Thermal IR index) + optional live noisy smoke-detector reading.
- **Environment Taxonomy** (`Week 1.pptx`, Slides 10–14):
  - **Observability:** Partially observable (noisy sensors & uncertain fire ignition).
  - **Agents:** Single-agent decision support (with human-in-the-loop dispatcher).
  - **Uncertainty:** Stochastic (wind can shift fire state unpredictably).
  - **Structure:** Sequential (each action affects future fire spread and remaining resources).
  - **Timing:** Semi-dynamic / dynamic across simulation ticks.
  - **Action space:** Discrete (grid moves N/S/E/W + discrete MDP response actions).

---

## 2. Topic 1 — Classical Machine Learning & Probabilistic Reasoning
**Sources:** `Lecture 8_Rational_Decisions_Classical_ML.pptx` (Slides 1, 22, 41–46, 60–64) + `499122fa-a771-4744-a3da-8be5b985e10e.pdf` (Week 6 Bayes, Pages 55–60).

- **Core Paradigm** (`Lecture 8`, Slide 1): `DATA → PREDICTION → UTILITY → ACTION`.
- **Feature Standardization** (`Lecture 8`, Slide 46):
  $$z_j = \frac{x_j - \mu_j}{\sigma_j}$$
  Fit mean $\mu_j$ and std $\sigma_j$ strictly on `X_train` to prevent **data leakage** (`Lecture 8`, Slide 64).
- **Logistic Regression** (`Lecture 8`, Slides 42–43):
  $$z = \mathbf{w}^\top \mathbf{x} + b, \qquad P(y = 1 \mid \mathbf{x}) = \sigma(z) = \frac{1}{1 + e^{-z}}$$
  Trained via binary cross-entropy loss minimization (gradient descent with L2 regularization).
- **Gaussian Naive Bayes Baseline** (`Syllabus Week 8`):
  $$P(y = c \mid \mathbf{x}) \propto P(y = c) \prod_{j=1}^{d} \mathcal{N}(x_j \mid \mu_{c,j}, \sigma^2_{c,j})$$
  Used as an interpretable probabilistic baseline to compare against Logistic Regression.
- **Decision Threshold $\tau$** (`Lecture 8`, Slides 22, 45):
  $$\hat{y} = \mathbb{I}[P(\text{Fire} \mid \mathbf{x}) \ge \tau]$$
  In high-cost wildfire scenarios (where missing a real fire — FN — is far costlier than a false alarm — FP), choosing $\tau < 0.5$ (e.g., $\tau = 0.35$) increases Recall.
- **Evaluation Metrics** (`Lecture 8`, Slides 60–62):
  - $\text{Accuracy} = \frac{TP + TN}{N}$
  - $\text{Precision} = \frac{TP}{TP + FP}$
  - $\text{Recall} = \frac{TP}{TP + FN}$
  - $F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$
  - Key insight (`Slide 60`): *"High accuracy ≠ good decisions"* — missing real fires (low recall) is dangerous.
- **Live Bayesian Sensor Update Bridge** (`Week 6 PDF`, Pages 55–60):
  When a sector receives a live smoke-sensor observation $E \in \{\text{Alert}, \text{Clear}\}$:
  $$P(\text{Fire} \mid E) = \frac{P(E \mid \text{Fire})\, P(\text{Fire})}{P(E \mid \text{Fire})\, P(\text{Fire}) + P(E \mid \neg\text{Fire})\, (1 - P(\text{Fire}))}$$
  Here, the ML-predicted probability acts as the **prior** $P(\text{Fire})$, and the noisy sensor refines it into the **posterior** $P(\text{Fire} \mid E)$.

---

## 3. Topic 2 — Informed Heuristic Search (`b985f194-ff50-477d-a9fa-4d910e1cde4f.pdf`, `AI_Fundamentals_Practice_week_2.docx`)
- **State-Space Abstraction** (`Lecture 2 PDF`, Page 3):
  - State: $(r, c)$ grid coordinates
  - Actions: `UP, DOWN, LEFT, RIGHT` (4-connected N/S/E/W)
  - Goal test: $(r, c) = \text{goal}$
- **Step Cost (Risk-Aware Integration with Topic 1):**
  $$c(u \to v) = c_{\text{terrain}}(v) + \lambda \cdot P(\text{Fire} \mid \mathbf{x}_v)$$
  where $c_{\text{terrain}}(v) \ge 1.0$ (plain = 1.0, dry bush = 1.3, rough hill = 1.8) and $\lambda > 0$ is the risk penalty weight (e.g. $\lambda = 8.0$).
- **A\* Evaluation Function** (`Lecture 2 PDF`, Pages 29–31, 44):
  $$f(n) = g(n) + h(n)$$
  - $g(n)$: exact accumulated path cost from start to $n$.
  - $h(n)$: **Manhattan distance** $|r_n - r_{\text{goal}}| + |c_n - c_{\text{goal}}|$ multiplied by the minimum possible step cost ($c_{\min} = 1.0$).
- **Admissibility & Optimality Guarantee** (`Lecture 2 PDF`, Pages 34–38):
  - Because every move costs at least $1.0$ (since $c_{\text{terrain}} \ge 1.0$ and $\lambda P(\text{Fire}) \ge 0$), Manhattan distance satisfies $0 \le h(n) \le h^*(n)$ (admissible and consistent!).
  - Therefore, **A\* guarantees the minimum-cost (safest/fastest weighted) path** while expanding significantly fewer nodes than UCS (`Lecture 2 PDF`, Page 47).
- **Comparison Baselines** (`Lecture 2 PDF`, Pages 14–28; `Practical 2`):
  - **BFS (FIFO queue):** fewest steps, completely ignores fire risk & terrain cost.
  - **UCS (priority queue on $g(n)$):** optimal risk-aware cost ($h(n) = 0$), explores broadly in all directions.
  - **A\* (priority queue on $f(n) = g(n) + h(n)$):** same optimal cost as UCS, fewer expanded nodes.

---

## 4. Topic 3 — Sequential Decision Making: MDP & Value Iteration (`MDP_Reinforcement_Learning.pptx`)
- **Search vs MDP** (`MDP_Reinforcement_Learning.pptx`, Slide 4):
  - *"Search returns a path; an MDP solution is a policy $\pi(s)$."*
- **MDP Tuple** (`Week 1`, Slide 35; `MDP`, Slides 2, 13–29): $(S, A, P, R, \gamma)$
  - **States $S$:** Composite discrete operational states combining `(FireRiskLevel, ResourceLevel)` plus terminal states `Contained` and `Escaped/Critical` (e.g., 3 risk levels × 2 resource levels + 2 terminal = 8 clean, inspectable states — directly interpretable for a 1st-year defense!).
  - **Actions $A$:** `Direct Dispatch`, `Safe Detour`, `Aerial Retardant`, `Sensor Re-scan`, `Evacuate / Hold`.
  - **Transition Probabilities $P(s' \mid s, a)$:** Stochastic transitions parameterized by current **wind intensity** and **A\* route exposure** (higher wind increases probability of fire escalation).
  - **Rewards $R(s, a, s')$:** Positive reward for containment (`+100`), severe penalty for uncontrolled fire/loss (`-120`), moderate operational costs for actions (`-5` to `-18`), ensuring safety outweighs reckless speed (`MDP`, Slide 13 & Slide 69).
  - **Discount Factor $\gamma \in (0, 1)$:** Default $\gamma = 0.90$, with live sensitivity analysis ($\gamma \in \{0.50, 0.80, 0.90, 0.95\}$ per Slide 17).
- **Bellman Optimality Equation** (`MDP`, Slides 22, 26):
  $$Q^*(s, a) = \sum_{s'} P(s' \mid s, a)\,\big[R(s, a, s') + \gamma V^*(s')\big]$$
  $$V^*(s) = \max_{a \in A} Q^*(s, a), \qquad \pi^*(s) = \arg\max_{a \in A} Q^*(s, a)$$
- **Value Iteration** (`MDP`, Slides 29–30):
  $$V_{k+1}(s) = \max_{a \in A} \sum_{s'} P(s' \mid s, a)\,\big[R(s, a, s') + \gamma V_k(s')\big]$$
  Iterate until $\max_{s} |V_{k+1}(s) - V_k(s)| < \theta$ (e.g., $\theta = 10^{-6}$). Record $\Delta_k = \max_s |V_{k+1}(s) - V_k(s)|$ at every iteration to plot Bellman convergence.

---

## 5. Responsible AI & Kazakhstan Legal Framework (`AI_Legal_Framework.pptx`)
- **Primary Legal Reference:** Law of the Republic of Kazakhstan *"On Artificial Intelligence"*, **No. 230-VIII ZRK**, adopted **17 November 2025** (`AI_Legal_Framework.pptx`, Slides 2, 4, 22).
- **Risk Classification** (`Slide 6`): Emergency wildfire response is **High-Risk** (potential serious impact on human life, environment, and infrastructure).
- **Autonomy Classification** (`Slide 7`): SteppeGuard AI is deliberately designed as **Low Autonomy (Human-in-the-Loop)** — AI predicts probabilities, computes routes, and recommends an MDP policy with full numerical reasoning, while a human emergency dispatcher makes the final operational decision.
- **Transparency & Synthetic Labeling** (`Slide 9`): UI and reports prominently label all telemetry as synthetic simulation data and disclose AI assistance.
- **Safety Constraint** (`MDP`, Slide 69; `AI_Legal_Framework`, Slide 21): Hard operational safety override ("Human Override / Confirm Action") is exposed in the interface.
