# Problem B · First-round modeling report

The problem has **four top-level questions**. Question 2 contains two distinct optimization tasks. This report supplies the mathematical design, input contract and verification cases for the numerical stage. All numerical examples in the verification section use constructed inputs.

## 1. Inputs, scope and dependencies

The B folder contains one five-page problem PDF. Its first two pages supply all baseline geometry. There is no separate B data spreadsheet. Coordinates are in metres, time in seconds. The southwest corner is the origin, east is the positive \(x\)-axis, north the positive \(y\)-axis. Targets are stationary during deployment. The following values are transcribed inputs.

| Building | \(x\) interval | \(y\) interval | Height |
|---|---|---|---|
| B1 | [22,34] | [16,26] | 20 |
| B2 | [63,79] | [59,71] | 28 |
| B3 | [10,24] | [65,76] | 12 |
| B4 | [72,86] | [22,34] | 24 |
| B5 | [41,51] | [38,46] | 32 |

| Vehicle | V1 | V2 | V3 | V4 | V5 |
|---|---|---|---|---|---|
| Initial centre | (15,14) | (88,10) | (14,86) | (88,68) | (50,93) |

| Alert | Bearing from dispatch centre | Horizontal range from dispatch centre | Target altitude |
|---|---|---|---|
| T1 | 30° | 40 | 45 |
| T2 | 150° | 45 | 35 |
| T3 | 285° | 38 | 55 |
| New alert in Q4 | [0°,360°) | [30,50] | 50 |

The five building IDs, five vehicle IDs and three base alert IDs are distinct within their respective sets. All three collections have their required fields. Q4 supplies ranges for the new alert and a conditional uniform distribution for the identity of a failed vehicle. It supplies no probability distribution for alert bearing, range or communications recovery time. No training sample is involved.

| Work unit | Inputs and decisions | Objective and expected output | Dependency |
|---|---|---|---|
| Q1 | T1 and the common geometry. Choose one station. | Maximize inverse horizontal range. Deliver the observable-region plot, selected coordinates, range, elevation and tie rule. | The feasibility test is reusable for every target. |
| Q2(1) | T2, five initial centres, two independent bearing measurements. Choose two vehicles and two stations. | Minimize first-order horizontal position RMSE. Deliver vehicle IDs, stations, baseline, intersection angle, two travel times and RMSE. | Uses Q1 geometry for T2 and obstacle-aware travel. |
| Q2(2) | T1–T3 released together. Choose two vehicles per alert, stations, and service order per vehicle. | Minimize the latest observation start. Deliver optimized and nearest-assignment plans, paths and vehicle timelines. | Uses visibility, valid bearing intersection and the event clock. |
| Q3 | Fixed true vehicle-to-target horizontal range 40 and three independent error sources. | Estimate the maximum cumulative travel distance and the feasible \((a,b)\) region at 80 m. Deliver source contributions and a nonlinear check. | Shares the bearing convention. The specified error experiment is independent of the dispatch solution. |
| Q4 | Freeze the Q2(2) optimized plan. Introduce observed disturbances at 5 s. | Compare retention and rescheduling by completion ratio, then latest start in a 60 s window. Deliver matched scenarios and timelines. | Requires paths parameterized by length, intermediate gimbal angles, existing commands and outstanding actions. |

## 2. Notation

| Symbol | Definition |
|---|---|
| \(\Omega,O\) | Field \([0,100]^2\) and dispatch centre \((50,50)\). |
| \(D_m,h_m,B_m\) | Building footprint, height and closed prism \(D_m\times[0,h_m]\). |
| \(i,j,I_j\) | Vehicle index, alert index, and set of two distinct vehicles serving alert \(j\). |
| \(p_i^0,p_i(t),p_{ij}\) | Initial vehicle centre, current centre and assigned station for alert \(j\). |
| \(\rho,v,h_c,\omega,\tau\) | Disk radius 1.5 m, travel speed 3 m/s, camera height 2 m, gimbal-axis speed 30°/s, joint observation duration 5 s. |
| \(\theta_j,R_j,H_j,u_j,T_j\) | Alert bearing, centre range and altitude, horizontal target projection \(u_j=O+R_j(\cos\theta_j,\sin\theta_j)\), and \(T_j=(u_j,H_j)\). |
| \(C(p),r_j(p),\alpha_j(p),\beta_j(p)\) | Camera \((p_x,p_y,h_c)\), horizontal station range, azimuth and elevation. |
| \(\mathcal F,\mathcal V_j,\Gamma,d_{\mathcal F},s_i(t)\) | Vehicle space, station set for alert \(j\), a vehicle path, shortest feasible travel length and cumulative actual mileage. |
| \(L_j,\gamma_j,e_j\) | Straight-line station baseline, horizontal intersection angle in \([0,\pi]\), and horizontal RMSE. |
| \(D_{ij},A_{ij},g_{ij},S_j,E_j,F_{ij}\) | Departure, arrival, slew duration, joint start, joint end and individual release after reset. \(D_{ij}\) is a time, whereas \(D_m\) is a footprint. |
| \(P,\hat P,\varepsilon_0,\varepsilon_c,\Delta\psi\) | True and estimated vehicle position, gimbal zero-offset and control errors, and total wrapped bearing deviation. |
| \(t_d,t_{\rm rec},N,k,\eta,t_{\rm last}\) | Disturbance time 5 s, recovery time, alert count, valid starts, completion ratio and scored latest start. |

Use radians in computation. Convert all supplied angular speeds and standard deviations at the input boundary. Use degrees in figures and reported angles. Define \(\operatorname{wrap}(x)=(x+\pi)\bmod(2\pi)-\pi\) and

\[
r_j(p)=\|u_j-p\|_2,\quad
\alpha_j(p)=\operatorname{atan2}(u_{jy}-p_y,u_{jx}-p_x),\quad
\beta_j(p)=\operatorname{atan2}(H_j-h_c,r_j(p)).
\]

## 3. Assumption and sensitivity precheck

| Issue and competing readings | Decision for the main analysis | Check or alternative |
|---|---|---|
| Vehicle boundary contact versus optical tangency | The disk may touch the field or a building externally. The field boundary may not be crossed and the building interior may not be entered. Any optical contact with the closed prism blocks the segment. | Test a vehicle tangent to a wall and a sightline tangent to a roof separately. Report physical clearance and numerical tolerances separately. |
| Does the Q2(1) limit apply to all scheduled actions? | Apply 30 s to each vehicle's **initial travel** in Q2(1). Preserve all slew, wait, observation and reset events in the Q2(2) clock. | A vehicle arriving exactly at the travel limit remains eligible even when it still has to point. |
| Distinct azimuths versus an added precision threshold in Q2(2) | Require two distinct vehicles and a full-rank horizontal intersection. Record \(\lvert\sin\gamma\rvert\) and station clearances for selected pairs. | If operational robustness is discussed, repeat with explicit positive angular or clearance margins and label them as sensitivity assumptions. |
| Azimuth rotation and simultaneous events | Use the shorter bidirectional pan rotation. Each moving axis slews at the limit and holds when aligned. At \(t=5\), process disturbance and communication availability before testing a new start at exactly that time. | Only starts strictly before the disturbance are locked under the wording of Q4. Record both state and event order at ties. |
| Meaning of the communication interval | Main case uses the explicit interval \([5,t_{\rm rec}]\) and \(5<t_{\rm rec}\le30\). Preloaded commands continue throughout the outage. A new command can take effect at recovery. | This gives duration \(0<t_{\rm rec}-5\le25\). The separate wording “duration within [5,30]” instead implies \(10\le t_{\rm rec}\le35\). Repeat affected scenarios under the second interpretation and label the time as duration or absolute recovery time. |
| Failure leaves a partner without a valid pair | Preload the nominal timetable. Under strict retention an unmatched healthy partner holds its assigned slot, resets and follows its next original instruction. A new alert receives no slot in that policy. | This defines a reproducible comparator without advance knowledge of a failure. The replanner can change the unstarted slot once new instructions can be received. |

All base and new target heights exceed all five building heights, and the camera is below every roof. This checked ordering permits the exact shadow construction below. The nominal Q1, Q2 and Q4 calculations use the specified parameters, with the stated 1° measurement model in Q2(1). Q3 supplies a separate uncertainty experiment. Vehicle steering, acceleration, deceleration and collision-avoidance time follow the problem's stated simplifications.

## 4. Q1 · Observable region and single station

### Vehicle space and line of sight

\[
\mathcal F=\{p\in[\rho,100-\rho]^2:\ \operatorname{dist}(p,D_m)\ge\rho\quad\forall m\}.
\]

The Euclidean disk offset of a rectangular footprint has straight sides and rounded corners. Check the centre's distance to the actual footprint. For optical visibility intersect the **original** closed three-dimensional prism with \(C(p)+\lambda(T_j-C(p))\), \(0\le\lambda\le1\). Intersect the three closed slab parameter intervals with \([0,1]\). A singleton intersection blocks visibility. A zero direction component imposes the corresponding slab-membership test. An obstacle past the target cannot block this segment.

### An exact planar cross-check

For a building \(m\), let \(\kappa_{mj}=(H_j-h_c)/(H_j-h_m)\). Its closed shadow in station coordinates is

\[
W_{mj}=\operatorname{conv}\!\left(D_m\ \cup\ \{u_j+\kappa_{mj}(d-u_j):d\in D_m\}\right).
\]

At a possible intersection below roof height, write the horizontal intersection point as \(d=u_j+(1-\lambda)(p-u_j)\). Solving for the station gives \(p=u_j+c(d-u_j)\), where \(1\le c\le\kappa_{mj}\). The union of these scaled copies of the convex rectangle is the convex hull of its two endpoint copies. The polygon can be built from eight corners. This gives an independent test for the finite three-dimensional segment, including the case where \(u_j\) projects onto a roof.

\[
\mathcal V_j=\{p\in\mathcal F:\ -10^\circ\le\beta_j(p)\le80^\circ\}
               \ \setminus\ \bigcup_m W_{mj}.
\]

### Objective, search and output

Maximize \(Q_1(p)=1/r_1(p)\) on \(\mathcal V_1\). The upper elevation limit gives a continuous lower bound \(r_0=(H_1-h_c)/\tan 80^\circ\). Intersect the circle \(r_1(p)=r_0\) with the free and visible region. A retained point certifies that this bound is attained. Among equally good points, maximize the minimum spatial sightline clearance over buildings, then use coordinate order. For this tie test, include all feasible circular arcs and endpoints, respecting open shadow boundaries.

If that circle has no feasible point, search increasing distance through the exact boundary arrangement or use a refined feasible search with a lower bound and an explicit remaining gap. A limit on an excluded shadow boundary may be an infimum. Report the achievable station, horizontal range, elevation and certificate or approximation gap. Plot the field, rounded forbidden regions, shadows, observable set and selected point in equal-axis MATLAB coordinates.

**Two error checks.** Keep vehicle contact and optical contact predicates separate. Use horizontal station range and show whether the minimum radius is attained.

## 5. Q2 · Two-station geometry and concurrent dispatch

### Q2(1) · Precision and individual travel limits

For each of the ten unordered vehicle pairs, assign stations \(p_{ij}\in\mathcal V_2\). Include both vehicle-to-station assignments where relevant. For station \(l\), the row of the horizontal bearing Jacobian with respect to target position is \(J_l=(-\sin\alpha_l,\cos\alpha_l)/r_l\). With independent angular errors of standard deviation \(\sigma_\alpha=\pi/180\), the first-order covariance and error metric are

\[
\Sigma_T\simeq(J^\top J/\sigma_\alpha^2)^{-1},\qquad
e=\sqrt{\operatorname{tr}\Sigma_T}
 =\frac{\sigma_\alpha\sqrt{r_1^2+r_2^2}}{|\sin\gamma|},\qquad
L^2=r_1^2+r_2^2-2r_1r_2\cos\gamma .
\]

The metric estimates root mean squared horizontal displacement in metres. Calculate the full angle in \([0,\pi]\) from the dot product and absolute cross product of the two bearing vectors. Enforce \(d_{\mathcal F}(p_i^0,p_{i2})/v\le30\) for **each** vehicle. Minimize \(e\) over admissible pairs. As \(\gamma\) approaches either end of its range, the two bearing rows become dependent. A feasible elevation boundary alone does not cause this rank loss. Exact shadow tangency already fails visibility.

For \(d_{\mathcal F}\), test a clear direct segment first. Otherwise build a tangent graph for the rounded rectangles with the source, destination, valid tangencies, boundary-line joins and arcs. Use straight and arc lengths on their corresponding graph edges. Reject any edge entering an obstacle or leaving the inset field. Dijkstra returns both length and ordered segments, in \(O((V+E)\log V)\) time once the graph is constructed. Cache reusable legs. A conservative polygonal approximation is an alternative if its outward error is bounded and stated. Recheck the reported routes against the analytic disk constraint.

Seed station candidates on observable boundaries, circle arcs and a refined interior grid, with the strict visibility test applied to each. Compare the best feasible RMSE to the lower bound \(\sigma_\alpha\sqrt{2}\,r_0\), here using the Q2 target's own \(r_0\). If it is not attained, report the search resolution and bound gap. Test the analytic covariance on well-conditioned pairs with independent simulated azimuth perturbations. Report near-singular geometry separately.

### Q2(2) · Event clock and assignment

For each alert choose two distinct vehicles and a full-rank station pair. Choose a sequence of jobs per vehicle with no overlapping occupations. Build a precedence graph from vehicle orders and common jobs, then discard cyclic schedules. For each assigned leg use

\[
\begin{aligned}
A_{ij}&=D_{ij}+d_{\mathcal F}(p_i^{\rm prev},p_{ij})/v,\\
g_{ij}&=\max\{|\operatorname{wrap}(\alpha_j(p_{ij}))|,|\beta_j(p_{ij})|\}/\omega,\\
S_j&=\max_{i\in I_j}(A_{ij}+g_{ij}),\qquad E_j=S_j+\tau,\qquad F_{ij}=E_j+g_{ij}.
\end{aligned}
\]

The first nominal dispatch may start at zero. A preassigned next leg departs at that vehicle's \(F_{ij}\). At the station each vehicle starts slewing immediately after arrival, then waits if its partner is later. Reset equals nominal slew duration because the target is stationary and each undisturbed departure starts facing due east horizontally. Minimize \(\max_{j=1,2,3} S_j\).

For the finite candidate stations enumerate vehicle pairs, sequences and compatible station pairs, pruning by an admissible lower bound. One such bound is the maximum over pending alerts of their earliest two-car readiness with other pending jobs ignored. An incumbent from the feasible baseline bounds the search from above. Exhausting the surviving branches certifies the finite candidate set result. Refine the station set and report the change and continuous lower bound where available. A feasible incumbent by itself provides an upper bound on the minimum start-time objective.

**Nearest-assignment comparator.** Process simultaneous alerts in ID order. For each, append it to the two vehicle queues whose last assigned positions give the smallest sum of obstacle-aware distances to a feasible station pair. Break ties by predicted joint start, then vehicle IDs and station coordinates. Use the same candidate stations, travel model, full-rank check, waiting rule, observation time and individual release clock as in the optimized plan. Save all five time axes, including idle vehicles. Compare per-alert starts, vehicle reuse, travel, waiting and reset time to explain the difference.

**Two error checks.** Apply the 30 s limit to individual travel in Q2(1) and diagnose numerical conditioning separately from station feasibility. In Q2(2) pair each arrival with its own slew before taking the maximum, and release the two vehicles individually.

## 6. Q3 · Horizontal pointing uncertainty

Here the target is perfectly known and \(r=40\) m is the true horizontal range from the vehicle. Let \(\delta P=\hat P-P\). In axes parallel and perpendicular to the true horizontal bearing, \(\delta_\parallel,\delta_\perp\) remain independent \(N(0,\sigma_P(s)^2)\) because the specified coordinate-error law is isotropic. The prescribed baseline law is \(\sigma_P(s)=0.3+0.02s\) m, where \(s\) accumulates actual travelled path length. The exact geometric bearing error and combined pointing deviation are

\[
\phi=\operatorname{atan2}(-\delta_\perp,r-\delta_\parallel),\qquad
\Delta\psi=\operatorname{wrap}(\phi+\varepsilon_0+\varepsilon_c).
\]

The two independent gimbal standard deviations are \(\sigma_0=0.8\pi/180\) and \(\sigma_c=0.6\pi/180\) radians. Linearization at zero position error gives \(\phi\simeq-\delta_\perp/r\). With \(d=5\pi/180\), \(z=\Phi^{-1}(0.975)\),

\[
V(s)=\frac{\sigma_P(s)^2}{r^2}+\sigma_0^2+\sigma_c^2,\quad
p_{\rm lin}(s)=2\Phi\big(d/\sqrt{V(s)}\big)-1,\quad
\sigma_{\rm crit,lin}=r\sqrt{(d/z)^2-\sigma_0^2-\sigma_c^2}.
\]

When the radicand is positive and the baseline is feasible at zero travel, the linearized mileage limit is \((\sigma_{\rm crit,lin}-0.3)/0.02\). For the alternate model the linearized region is \(a,b\ge0,\ a+80b\le\sigma_{\rm crit,lin}\). Report the three contributions by dividing the three individual variance terms by \(V(s)\). At first order only transverse localization error changes azimuth.

For numerical validation define \(p(\sigma)=\Pr(|\operatorname{wrap}(\phi+\varepsilon_0+\varepsilon_c)|\le d)\) using the original geometry. For a given sampled or quadrature value of \(\phi\), integrate the two gimbal terms analytically. With \(\sigma_g^2=\sigma_0^2+\sigma_c^2\), the conditional probability is

\[
\sum_{n\in\mathbb Z}\left[
\Phi\!\left(\frac{d+2\pi n-\phi}{\sigma_g}\right)-
\Phi\!\left(\frac{-d+2\pi n-\phi}{\sigma_g}\right)\right].
\]

Average over both position-error coordinates by Gaussian quadrature, increasing the quadrature order and the retained period range until the reported precision is stable with negligible omitted normal tail mass. Bracket the 0.95 crossing by refinement, verify the feasible side, and independently check the bracket with fixed-seed Monte Carlo and a binomial interval. Record sample size and bracket width when results are produced. The full nonlinear admissible set at 80 m is \(a,b\ge0,\ p(a+80b)\ge0.95\). Compare the nonlinear boundary with the analytic approximation before adopting the latter in a deployment recommendation. Use an English probability-versus-mileage plot with the 0.95 threshold and a separate \((a,b)\) feasible-region plot.

**Two error checks.** Distinguish cumulative travel \(s\) from fixed optical range \(r\), and wrap all azimuth differences. Use the two-sided probability and independent variances in the same angular units.

## 7. Q4 · Rescheduling after disturbances

### Freeze and resume

Retain the timestamped Q2(2) optimized plan as the common \(t=0\) history for both policies. At \(5^{-}\) reconstruct, per vehicle, its path position, mileage, action, continuous pan/tilt angles, remaining action time, health and issued task queue. A vehicle travelling on an arc is placed by distance along the arc. During a slew, advance each axis by at most \(\omega\Delta t\) toward its target and hold the axis upon arrival.

For alerts with \(S_j<5\), lock the success and prohibit reassignment. Healthy participants still consume the remaining observation and reset time. Apply the relevant events at \(t_d=5\). A failed vehicle immediately withdraws and does not block paths. A new alert is released only now and needs two vehicles. At a simultaneous boundary process the disturbance first as recorded in the assumption table.

During an outage all healthy vehicles execute their last received instructions. A planner may observe information as it becomes available. New vehicle actions take effect when commands can be received. At recovery use the actual state then, including any newly committed observations. Never give either policy the realized new alert, failure identity or future recovery time at \(t=0\). With a working link, replan immediately at the event. A moving vehicle reroutes from its actual centre. A stationary vehicle that must travel first returns its actual pan and tilt to zero. A stationary vehicle retargeting at the same site slews from its actual pose. At any new departure, enforce the due-east horizontal movement attitude.

### Policies, scenarios and scoring

* **Retain the schedule.** Keep original healthy vehicle assignments, stations and timed queues. Under the predeclared slot rule an unpaired slot contributes no success but consumes its reserved interval. New alerts remain unassigned. This policy is the Q4 comparator, whereas nearest assignment is the Q2(2) comparator.
* **Reschedule.** From the first executable decision epoch, preserve committed tasks, exclude the failed vehicle and reassign pending jobs. Use the same path generator, station tests, gimbal rates, pre-event log and success predicate as the retentive policy. Search the remaining finite choices using the two priorities below. Only currently known attributes of a new alert may be used.
* **Scenario design.** Include the no-disturbance control, the three single disturbances, three pairwise combinations and the triple combination. For a new alert use directions in open sectors and on either side of representative building-shadow transitions. Choose the lower, middle and upper allowable ranges and fixed altitude 50 m. For failures enumerate each vehicle with conditional weight \(1/5\). For outages sample short, intermediate and upper-end cases on an explicitly labelled recovery-time or duration axis. Match the exact realized inputs between policies. Report each outcome and the worst case. Label any unweighted average over designed cases as a scenario-set summary.

With closed evaluation window \(0\le t\le60\), \(N=3+\mathbf1_{\rm new}\) and \(k\) equal to the number of alerts with a valid joint observation start in the window, set

\[
\eta=k/N,\qquad
t_{\rm last}=
\begin{cases}
60,&k<N,\\
\max_j S_j,&k=N .
\end{cases}
\]

A start exactly at 60 s qualifies under the adopted closed-window convention. Judge a pair of outcomes lexicographically by larger \(\eta\), then smaller \(t_{\rm last}\). When both leave alerts incomplete with the same \(k\), distinguish their operational differences in the timeline discussion while preserving the score tie. For the outage-only case with a fully preloaded feasible timetable, unchanged execution provides a useful control. Annotate failure, outage and recovery on the MATLAB comparison timelines.

**Two error checks.** Plans must share their realized pre-event path and respect communication and resource occupancy. Use the number of successful **starts**, include new alerts in the denominator, and assign the 60 s penalty when any alert misses the window.

## 8. Checks performed in the first round

The checks below use manufactured inputs and can be reproduced with `tools/check_round1.py` from the project directory.

| Check | Observed result |
|---|---|
| Exact shadow versus finite closed-segment slab test | Each method agreed on 1,875 rational-coordinate cases, from 625 grid locations and three target projections placed outside a rectangle, inside it and on a corner. Both computations used rational arithmetic. |
| Roof contact, lower roof and building beyond target | The tangent roof blocked the segment. Lowering that roof cleared it, and the separate building beyond the endpoint had no effect. The round-corner case preserved a legal station that a square offset would discard. |
| Two-station error propagation | The inverse-information trace and scalar geometric formula agreed to floating-point tolerance on a non-orthogonal synthetic pair. |
| Synchronized clock | For synthetic arrivals (2,5) s and slews (4,1) s, the common interval was [6,11] s. The vehicles became free at 15 s and 12 s, respectively. |
| Disturbance and observation window | The lock test distinguished a start just before 5 s from a start at 5 s. A missed alert set the latest start to 60 s. A valid start exactly at the closed endpoint counted as successful. |
| Rotational invariance | Rotating the target and one localization-error sample across the signed azimuth boundary preserved the computed bearing deviation. |

The original five-page B PDF has SHA-256 `9585081e724cef939d4e5713ea72f9eddefd4469a3b519a8ce184677d407692a`. The upstream strict intake recorded two LOW text-contrast flags, on the ordinary words “angle” and “and” on page 3. The rendered page confirms their use in the visible problem statement. The PDF text mapping also yields 24 unpaired UTF-16 units in eight mathematical fragments on pages 1, 2 and 5. The source-bound transcription in `tools/ingest_problem.py` restores the visually checked symbols, including \(O\), \((\theta,R,H)\), the coordinates and \(\eta=k/N\), after detection and before UTF-8 hashing. The intake manifest, detector report and text are in `stage_S-1_ingest/`. The original PDF remains the reference for equation layout.

Three independent Codex reviews covered single/dual-station geometry, event scheduling and probability/scenario design. Their main decisions are the exact shadow cross-check, per-vehicle release times, a predeclared unmatched-slot policy and independent nonlinear verification of the probability threshold. The fixed upstream checkout is `e081f5ea98253450edc5d192e438b73a4096061d`. The vendor-specific DeepSeek/GLM/Kimi/Qwen orchestrator was not invoked. No synthetic dry-run reply was used as modeling evidence.

## 9. Implementation handoff

| Task | Inputs | Outputs for analysis and MATLAB | Method | Acceptance |
|---|---|---|---|---|
| Geometry and Q1 | Field, building extents/heights, camera, T1 | Observable boundaries, excluded edges, comparison station, \(r,\alpha,\beta,Q\) | Circle/arc clipping, exact shadow and independent 3D segment tests | Every reported point passes all three observable tests. Identify an attained lower bound or report the remaining gap. |
| Q2(1) | T2, vehicle starts, angular noise | Vehicle/target/station IDs, coordinates, \(r_1,r_2,L,\gamma,e\) and individual travel times | Enumerate vehicle pairs, generate candidates, tangent graph and Jacobian | Replay each route within 30 s, test rank, units, clearances and RMSE identity. |
| Q2(2) | Three station sets, five vehicle starts | `stations.csv`, `path_segments.csv`, `events.csv` and per-policy objective table | Finite assignment/sequence search, deterministic nearest comparator and event replay | Six slots, two distinct cars per alert, no vehicle overlap, joint times agree, individual release respected. |
| Q3 | \(r,\sigma_P(s),\sigma_0,\sigma_c,d\) | Threshold bracket, \((a,b)\) frontier, contribution table and probability curves | Delta method, exact-angle integration and Monte Carlo with binomial intervals | All curves use cumulative mileage, two-sided success and radians internally. Verify zero position error and wrap invariance. |
| Q4 | Frozen paths/events, new-alert parameters, failure identity, recovery time | Shared event snapshot, per-policy paths/events, paired scenario table \((N,k,\eta,t_{\rm last})\) | Event-driven replan, eligibility checks at command delivery, paired comparison | Pre-event histories match. No mid-outage command takes effect. All missed alerts and starts at the horizon are scored consistently. |

For path segments store scheduling policy, alert and vehicle IDs, leg ID, segment order, endpoints, line/arc type, length, and for arcs the centre, radius and signed angular sweep. For events store scenario, policy, vehicle, alert, station, action, start/end time and start/end pan and tilt. MATLAB should read these outputs directly, preserve circular arcs, draw an equal-scale map, and distinguish slew, waiting, observation and reset. Formal captions, legends, axis labels, table headings and units must follow the official English-format instructions in `plan.md`.
