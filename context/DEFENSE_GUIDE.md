# SteppeGuard AI — Шпаргалка к защите, Q&A и Сценарий Демо-Видео (RU + EN)

> **Автор:** Oral Sanzhar (Stream 1, Practice 4, 6B06101 AI and ML)  
> **Тайминг защиты (со скрина критериев):**  
> - **2 минуты** — Problem Statement & Project Objectives (Слайды 1–2)  
> - **3–5 минут** — Live Demo в 3D-приложении `http://127.0.0.1:8000`  
> - **2 минуты** — Explanation of the Three AI Topics Implemented (Слайды 3–5)  
> - **До 3 минут** — Q&A (вопросы преподавателя)

---

## ЧАСТЬ 1. Сценарий 2–3-минутного Demo Video (и Live Demo на защите)

Запускай заранее: `.\.venv\Scripts\python.exe app.py` → открой `http://127.0.0.1:8000` (разверни на весь экран `F11` или 1280×800). Запись экрана в Windows: **`Win + G` (Xbox Game Bar)** или **OBS Studio**.

1. **[0:00 – 0:25] Вступление (Tab 1 — `Abai High Wind`):**
   - Покрути 3D-карту мышкой (покажи 3D-пламя, искры, синий маяк базы `(5,0)` и зелёный маяк посёлка `(5,9)`).
   - **Скажи (EN):** *"Hi, I'm Oral Sanzhar. This is SteppeGuard AI — a 3D wildfire risk intelligence and decision-support system for Kazakhstan's steppe. It chains three AI Fundamentals topics: Classical ML predicts fire probability per sector, Risk-Aware A\* routes around danger, and an MDP computes the optimal long-term response policy."*
2. **[0:25 – 0:55] Показ Search & 3D Анимации (`Abai High Wind`):**
   - Нажми **`▶ Animate Search & Drone`** — покажи волну раскрытия узлов и дрон, летящий по зелёной трассе **A\*** в обход огня, пока красная трасса **BFS** прёт прямо в пожар!
   - Укажи на таблицу справа: *"Notice A\* matches UCS's exact optimal cost (`18.06`), expands 46% fewer nodes on this run (`44 vs 82` — and 48.7% fewer across 30 seeds), and cuts wildfire exposure by 99% compared to unweighted BFS."*
   - Переключи **`Emergency Resources` → `Low (Ground)`**: смотри, как MDP мгновенно переключился с **`Aerial Retardant`** на **`Evacuate / Hold`**! Верни `High`.
3. **[0:55 – 1:35] Смена пресетов + Живой Байес (`Kostanay` → `Akmola`):**
   - Кликни **`Kostanay Dry Steppe`** → MDP автоматически рекомендует **`Safe Detour`**.
   - Кликни **`Akmola Watchtower`** → спокойно, MDP рекомендует **`Direct Dispatch`**.
   - Кликни по любой клетке на зелёной линии (например `(5,4)`), затем нажми **`📡 Smoke Alert (+Bayes)`**!
   - **Скажи (EN):** *"When a noisy watchtower sensor triggers a smoke alert, Bayes' theorem updates this sector's fire belief live from ~10% to ~49%, and the system immediately re-plans A\* and re-solves the MDP."*
   - Нажми **`✓ Approve AI Policy`** (покажи Human-in-the-Loop по Закону РК №230-VIII).
4. **[1:35 – 2:10] Вкладка `Math & Formulas`:**
   - Открой вкладку **`Math & Formulas`** — покажи 3 карточки с живыми числами: веса Logistic Regression + сигмоида, $g(n)/h(n)/f(n)$ для A\*, и таблицу 8 состояний MDP + **$\gamma$-Sensitivity** (при $\gamma=0.50$ `Med/HighRes` выбирает `Aerial Retardant`, при $\gamma \ge 0.80$ — `Safe Detour`).
5. **[2:10 – 2:40] Вкладка `30-Seed Benchmarks` и Финал:**
   - Открой вкладку **`30-Seed Benchmarks`** — покажи 4 KPI карточки (`86.8%` Recall, `-98.3%` Fire Exposure Cut, `-48.7%` Nodes Saved, `17 sweeps`) и 3 графика.
   - **Финальная фраза (EN):** *"All 19 automated tests pass, the entire 3D app runs 100% offline, and all telemetry is transparently labeled as synthetic simulation data. Thank you!"*

---

## ЧАСТЬ 2. Как объяснить 3 алгоритма за 2 минуты (просто, чётко, с аналогиями)

### 1. Topic 1 — Classical ML (Week 8) + Bayes Bridge (Week 6)
- **Простыми словами (RU):** Модель смотрит на 5 признаков каждой клетки (температура, влажность, ветер, сухость травы, тепловой индекс), складывает их с выученными весами $z = w^T x + b$ и пропускает через сигмоиду $\sigma(z)$, получая вероятность пожара от 0 до 1. Порог $\tau \approx 0.35$ мы подобрали на validation-выборке, потому что пропустить реальный пожар (False Negative) в 2 раза опаснее, чем ложная тревога — это подняло Recall с ~78% до ~87%! Плюс при сигнале вышки работает формула Байеса (Week 6).
- **Готовая фраза (EN):** *"First, Logistic Regression written from scratch in NumPy predicts fire probability per sector from five standardized weather features via $P(\text{Fire}|x) = \sigma(w^T x + b)$, compared against a Gaussian Naive Bayes baseline. Because missing a real wildfire is far costlier than a false alarm, we tuned the threshold $\tau \approx 0.35$ on a separate validation split, boosting Recall from 78% to 87%. When a watchtower smoke sensor alerts, exact Bayesian updating refines that prior in real time."*

### 2. Topic 2 — Risk-Aware A\* Search (Week 2)
- **Простыми словами (RU):** A\* берёт карту вероятностей от ML и задаёт стоимость входа в клетку как `рельеф + 3.5 × P(Fire)`. Это как GPS, который видит пожар как гигантскую пробку. Эвристика $h(n) = c_{\min} \cdot \text{Manhattan}$ никогда не завышает истинную стоимость ($0 \le h(n) \le h^*(n)$), поэтому A\* **гарантированно** находит такой же оптимальный маршрут, как UCS, но раскрывает почти в 2 раза меньше узлов и снижает контакт с огнём на 98% по сравнению с BFS.
- **Готовая фраза (EN):** *"Second, Risk-Aware A\* directly consumes the ML probability map as step cost $c(v) = c_{\text{terrain}}(v) + \lambda P(\text{Fire}|x_v)$. Using $c_{\min} \times \text{Manhattan distance}$ as an admissible heuristic guarantees the exact same optimal cost as UCS while expanding 49% fewer nodes and reducing wildfire exposure by 98% versus unweighted BFS."*

### 3. Topic 3 — MDP Value Iteration (Week 5)
- **Простыми словами (RU):** Как сказано в Лекции 5: *«Поиск даёт маршрут, а MDP даёт стратегию (политику)»*. У нас 8 состояний (3 уровня риска × 2 уровня ресурсов + 2 терминальных: Потушен / Упущен) и 5 действий. Переходы зависят от ветра и от реального риска маршрутов BFS и A\*. Уравнение Беллмана сходится за 17 итераций и выдаёт оптимальное действие для каждой ситуации.
- **Готовая фраза (EN):** *"Third, an 8-state, 5-action MDP solved by Bellman Value Iteration links corridor risk, wind, and the BFS vs A\* route exposures into a long-term response policy. It converges in 17 sweeps, recommends three distinct strategies across our three presets, gates Aerial Retardant by aircraft resources, and shifts from myopic to safe proactive actions as discount factor $\gamma$ increases."*

---

## ЧАСТЬ 3. Топ-12 вероятных вопросов преподавателя на Q&A (и идеальные ответы)

1. **Q: Why is your A\* heuristic guaranteed to be admissible?**
   - **A:** Every free cell on the grid has cost $c(v) \ge c_{\min}$ (at least `1.0`), and each cardinal move changes Manhattan distance by at most `1`. Therefore $h(n) = c_{\min} \cdot \text{Manhattan}(n, \text{goal}) \le h^*(n)$ always underestimates or equals the true remaining cost. (Verified on 50 random grids in `test_search.py`!)

2. **Q: What is the difference between BFS, UCS, and A\* in your project?**
   - **A:** **BFS** uses a FIFO queue and minimizes hop count—so it walks straight through fire. **UCS** uses a priority queue on $g(n)$ (`h=0`), so it finds the safest optimal route but explores broadly in all directions. **A\*** uses $f(n)=g(n)+h(n)$, achieving the **exact same optimal cost as UCS** while expanding ~49% fewer nodes.

3. **Q: Why didn't you just use `sklearn` for Logistic Regression?**
   - **A:** Writing `StandardScaler`, `LogisticRegressionScratch`, and `GaussianNBScratch` in pure NumPy makes every step transparent—gradient descent, L2 regularization on weights only, numerically stable sigmoid, and log-sum-exp—so there is no black box.

4. **Q: Why is your ML accuracy ~87% instead of 100%?**
   - **A:** Real wildfire risk is inherently uncertain! We deliberately added stochastic Bernoulli outcomes, 2% label noise, and a nonlinear `low humidity × high wind` interaction, plus split by independent scenes (no spatial data leakage). A 100% score on synthetic data would indicate overfitting or an unrealistically trivial rule.

5. **Q: Why did you lower threshold $\tau$ from 0.50 to ~0.35 if F1 stayed ~80.6%?**
   - **A:** From Lecture 8 Slide 60 (*"High accuracy ≠ good decisions"*): in wildfire detection, a False Negative (missing a real fire) is much costlier than a False Positive. Tuning $\tau$ on the validation split using a 2:1 FN:FP cost ratio increased **Recall from 78.3% to 86.8%**.

6. **Q: What does Brier score `0.085` mean?**
   - **A:** Brier score measures mean squared error of predicted probabilities: $\frac{1}{N}\sum(p_i - y_i)^2$ (lower is better). Always predicting the base rate (~30%) gives a baseline Brier score of ~0.22, so `0.085` shows a strong reduction in probability error.

7. **Q: How are your three algorithms actually connected — not just 3 separate scripts?**
   - **A:** Strictly chained: **ML** outputs the 10×10 probability grid → **A\*** uses those exact probabilities as step costs $c(v)$ → **MDP** uses the ML corridor risk + per-step exposure of both BFS and A\* routes to parameterize transition probabilities! We even have a counterfactual unit test (`test_counterfactual_exposure_coupling_flips_policy`) proving that raising BFS exposure flips the MDP policy to `Safe Detour`.

8. **Q: What happens when you change discount factor $\gamma$ in the MDP?**
   - **A:** $\gamma$ controls how much future rewards matter (`Lecture 5, Slide 16`). At myopic $\gamma = 0.50$, `Med / HighRes` grabs immediate containment via `Aerial Retardant`. At farsighted $\gamma \ge 0.80$, future value matters more, so the MDP chooses **`Safe Detour`** to conserve aircraft resources and de-escalate `Med → Low`.

9. **Q: Why is `Aerial Retardant` not chosen in every state?**
   - **A:** Because it has a high operating cost (`-26`) and consumes aircraft resources (`High → Low`). At `Low Risk`, cheaper ground response wins; at `Low Resources`, aerial drops are gated/unavailable, so `High Risk | Low Resources` chooses **`Evacuate / Hold`** to prevent catastrophic loss (`-130`).

10. **Q: How does your Watchtower Bayes update work mathematically?**
    - **A:** It treats the ML sector probability as the prior $P(\text{Fire})$ and applies Bayes' theorem with fixed watchtower sensitivity `TPR = 0.90` and false alarm `FPR = 0.10`. For example, if prior = `0.097` and a smoke alert fires, $P(\text{Fire}|\text{Alert}) = \frac{0.90 \times 0.097}{0.90 \times 0.097 + 0.10 \times 0.903} = 0.492$. Then A\* and MDP immediately re-run!

11. **Q: How does SteppeGuard AI comply with Kazakhstan's AI Legal Framework?**
    - **A:** Under **Law No. 230-VIII ZRK (17 Nov 2025)** from our course lecture: wildfire emergency response is **High-Risk**, so we keep **Low Autonomy (Human-in-the-Loop)**—the UI requires dispatcher approval/override, labels all data as synthetic simulation, collects zero personal data, and exposes full step-by-step math for auditability.

12. **Q: What would you improve if you expanded this project next semester?**
    - **A:** Replace synthetic telemetry with real Kazhydromet weather & NASA FIRMS / MODIS satellite fire data, add probability calibration (Platt scaling), simulate dynamic multi-step fire spread with wind vectors, and upgrade the MDP to a POMDP or Deep Q-Network (DQN).
