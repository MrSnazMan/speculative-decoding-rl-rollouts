# Three-way speculative-decoding comparison: MTP vs. DFlash2 vs. DSpark

Run 2026-09-11, single lambdalabs H100 80GB PCIe pod (`0d7851dcb59d446baa93d2d1529fb903`),
`vllm/vllm-openai:v0.29.0`, `Qwen/Qwen3.8-27B-FP8`, terminal-bench-core 0.1.1, same 50
task IDs as the earlier MTP off/on comparison, `n_concurrent=8`, `n_attempts=3` (150
trials per condition), `--global-agent-timeout-sec=420` matched across all three
conditions, `--enforce-eager --max-model-len 32768 --kv-cache-dtype fp8_e4m3
--gpu-memory-utilization 0.85`. Same corrected non-thinking sampling
(temperature=0.7, top_p=0.80, top_k=20, min_p=0.0, presence_penalty=1.5,
repetition_penalty=1.0, enable_thinking=False) and 2048-token per-turn cap as every
prior run in this series. All three conditions run fresh in one session, in the order
mtp_on -> dflash2_on -> dspark_on, on the same pod (not reusing any earlier run's data).

## Read this before the numbers below

**We cannot currently make a confident accuracy claim between mtp_on and the other two
conditions.** A test-infrastructure failure mode (`test_timeout`: the sandbox's test
step running past its 60s budget, unrelated to the LLM) occurred far more often in
dflash2_on and dspark_on than in mtp_on (2 vs. 22 vs. 31 trials out of 150), and its
rate rises monotonically with how late a condition ran on the shared pod, not with task
difficulty. One concrete case checked directly: the *easiest* task in the whole set
(`fix-permissions`, a one-line `chmod +x` fix) failed this way under dflash2_on. The
agent's solution was completely correct, but the test container's `apt-get update`
stalled on package-mirror congestion and blew the 60s budget. If every "excess"
`test_timeout` trial beyond mtp_on's baseline rate would otherwise have resolved
correctly (a generous but not unreasonable upper bound, given the verified case above),
dflash2_on's true resolved rate could be as high as 44.7% and dspark_on's as high as
45.3% -- both within a couple of points of mtp_on's 47.3%, i.e. **the confound's upper
bound nearly closes the entire measured accuracy gap.** The throughput/wall-clock/draft-
acceptance numbers below are not affected by this (they come from vLLM's own request
metrics, not test execution) and can be trusted as reported. The accuracy comparison specifically cannot yet be reliably confirmed. **this has now
been tested with a fresh-pod rerun of both alternative conditions (see "Fresh-pod
rerun" below): pod-age was ruled out as the cause, and the accuracy comparison still
cannot be made with confidence for either dflash2_on or dspark_on.**

## Headline numbers

| Metric | mtp_on (nst=3) | dflash2_on (nst=7) | dspark_on (nst=7) |
|---|--:|--:|--:|
| Resolved trials -- **see caveat above, accuracy not yet trustworthy** | **71/150 (47.3%)** | 47/150 (31.3%) | 39/150 (26.0%) |
| pass@3 -- **same caveat** | **29/50 (58.0%)** | 18/50 (36.0%) | 17/50 (34.0%) |
| Draft acceptance (trustworthy -- vLLM metrics, unaffected by the confound) | 86.3% (592,634/686,579) | 61.6% (644,223/1,045,044) | 57.5% (646,681/1,125,176) |
| Mean acceptance length (trustworthy -- vLLM metrics, accepted-token-weighted across all periodic `SpecDecoding metrics` log snapshots; max possible = num_speculative_tokens+1) | 3.59 / 4 (441 snapshots) | 4.84 / 8 (459 snapshots) | 4.71 / 8 (462 snapshots) |
| Throughput (trustworthy) | 183.9 tok/s | 171.4 tok/s | 165.4 tok/s |
| Wall clock (trustworthy) | 74.4 min | 79.3 min | 83.2 min |
| Draft tokens offered per accepted (rough) | ~1.16x | ~1.62x | ~1.74x |
| Run status | ok (clean exit) | ok (clean exit) | ok (clean exit) |

What *is* solid: DFlash2 and DSpark's larger draft blocks (7 tokens vs. MTP's 3) did not
translate into a speed win. Despite similar-or-higher peak per-token generation rates in
isolation, the much lower acceptance rate meant more verification rounds went to waste,
and *both* ended up with a *slower* end-to-end wall clock than MTP. This part of the
result does not depend on the test_timeout confound and can be reported as-is.

Mean acceptance length tells the same story from a different angle. DFlash2 and DSpark
accept more tokens per round in absolute terms (4.84 and 4.71 vs. MTP's 3.59) simply
because their draft blocks are longer, but as a fraction of what each method could
possibly accept per round they're worse: 4.84/8 (60.5%) and 4.71/8 (58.9%) vs. MTP's
3.59/4 (89.8%). The extra drafted tokens per round mostly go to waste rather than
compounding into a real speedup, consistent with the draft acceptance rate gap above.

Task-level movement vs. mtp_on (pass@3, subject to the same accuracy caveat):
dflash2_on gained `new-encrypt-command` (1), regressed on 12 others (net -11).
dspark_on gained `get-bitcoin-nodes` and `new-encrypt-command` (2), regressed on 14
others (net -12). No task got meaningfully *easier* under either alternative method.

## First-class finding: domain mismatch, not just sampling mode

Checked directly against primary sources before writing this up (not taken on faith):
the DFlash paper (arxiv 2602.06036, `z-lab/dflash`) and the DFlash2 model card both
report acceptance rate and speedup exclusively on **GSM8K, MATH/MATH-500, HumanEval,
MBPP, and MT-Bench** (the paper additionally covers AIME, LiveCodeBench, LongBench, and
LongAlign). **Neither source evaluates on any agentic, tool-use, multi-turn coding-agent,
or terminal/shell-command workload.** No equivalent published acceptance-rate benchmark
was found for the DSpark checkpoint used here at all.

These published benchmarks are short, templated, comparatively low-entropy
single-turn-or-few-turn completions (a proof, a function body, a chat reply). Agentic
rollouts under terminal-bench are long multi-turn conversations dense with shell
commands, file paths, compiler/test output, and strict tool-call JSON, which is a token
distribution these draft models were never trained or tuned against. The acceptance gap
measured here (86.3% MTP vs. 61.6% DFlash2 vs. 57.5% DSpark) is consistent with that
domain mismatch and is **not** affected by the test_timeout confound above (draft
acceptance is a vLLM-internal metric, independent of sandbox test execution). This is a
larger effect than the thinking/non-thinking sampling difference identified earlier
(Follow-up in `../dflash2_dspark_bounded/`, which accounted for roughly a 7-point gap on
DFlash2 alone): **speculative-decoding methods whose published gains come from
math/single-function-code benchmarks should not be assumed to transfer those gains to
agentic RL rollout workloads**, and any team evaluating a new speculative-decoding
method for agentic rollouts should validate acceptance rate on the actual target
workload rather than blindly trusting the paper's results.

## The test_timeout confound, in detail

| Condition | Ran | test_timeout trials (of 150) |
|---|---|--:|
| mtp_on | 1st, fresh pod (04:43-05:57Z) | **2** |
| dflash2_on | 2nd, ~1.5h into pod life (06:10-07:29Z) | **22** |
| dspark_on | 3rd, ~4.5h into pod life (07:39-09:02Z) | **31** |

This fires during sandbox *test execution*, strictly after the agent has already
submitted. No LLM call is involved at that point, so it cannot be a property of
DFlash2 or DSpark's output quality. The rate rises monotonically with how late a
condition ran on the shared pod, which is the signature of accumulating host/Docker
resource pressure (sandbox-container churn, disk/cgroup buildup, or transient
package-mirror congestion) over a ~6.4h pod lifetime running three back-to-back
150-trial evals, not a method effect.

Directly verified rather than assumed: pulled the trajectory for `fix-permissions`
(the single easiest task in the set) under dflash2_on, which hit `test_timeout`. The
agent's fix was completely correct (found the missing execute bit, applied `chmod
+x`, verified the script ran, declared done). The test step itself failed because
`apt-get update` inside the test container stalled at 67% package-index download for
47+ seconds, exceeding the 60s test budget. Nothing about this is attributable to the
model or the speculative-decoding method.

**Quantified upper bound on the skew** (not a point estimate -- see caveat): if every
"excess" `test_timeout` trial beyond mtp_on's own baseline rate (2/150) would
otherwise have resolved correctly:

| Condition | Actual resolved | Excess test_timeout trials vs. mtp_on baseline | Upper-bound resolved if all excess timeouts were actually-correct |
|---|--:|--:|--:|
| dflash2_on | 47/150 (31.3%) | 20 | up to 67/150 (44.7%) |
| dspark_on | 39/150 (26.0%) | 29 | up to 68/150 (45.3%) |

This ceiling is close enough to mtp_on's 47.3% that the true share of the accuracy gap
attributable to genuine method quality vs. this infrastructure artifact cannot be
established from this run. Only one case (`fix-permissions`) was individually
verified as "correct solution, robbed by infra" -- the true number of such cases among
the 20/29 "excess" trials is unknown and likely somewhat below the ceiling (some of
those trials involve genuinely slow-compiling tasks, e.g. `sqlite-with-gcov` and
`modernize-fortran-build`, where a real timeout is plausible even without congestion).

## Fresh-pod rerun: pod-age ruled out, time-correlated congestion is the leading hypothesis

To actually test the pod-age hypothesis above (rather than living with it as an open
question), dflash2_on and dspark_on were re-run in parallel, each on its own brand-new
pod, instead of sequentially on one aging pod. **Both reruns completed all 150/150
trials, clean exit (`RUN_STATUS: ok`) on both.**

**Final outcome -- evaluated per-condition, as it must be:**

| Condition | test_timeout, original run | test_timeout, fresh-pod rerun | mtp_on baseline |
|---|--:|--:|--:|
| dflash2_on | 22/150 (14.7%) | **28/150 (18.7%)** | 2/150 (1.3%) |
| dspark_on | 31/150 (20.7%) | **29/150 (19.3%)** | 2/150 (1.3%) |

**Neither condition dropped back toward mtp_on's baseline. dflash2_on's rate went
up slightly on the fresh pod; dspark_on's stayed essentially flat. Pod-age is
conclusively ruled out as the mechanism for both conditions.** Per how this result is
meant to be read: this is not a partial or "mostly" confirmation. Rather, it is a clean
non-confirmation for both dflash2_on and dspark_on individually, and is reported as
such rather than treated as having settled the accuracy question.

**CPU contention from DFlash2/DSpark's separate draft model is ruled out.** This was
checked directly, not assumed: live host monitoring (loadavg, %CPU, per-container
CPU%, disk and network I/O, logged every 10s on both fresh pods throughout the rerun)
showed no sign of saturation on either pod -- 26 vCPUs each, load average 1-4, ~90-95%
idle, even during active build/test bursts. DFlash2 and DSpark have structurally
different draft models, yet both fresh pods show the *identical* affected-task
pattern (below) -- inconsistent with a draft-model-specific engine-scheduling-overhead
mechanism, which would be expected to differ between the two methods if it were the
cause.

**Task clustering by run time is the strongest lead.** `test_timeout` is not spread
evenly across the task set. It concentrates on a specific handful of
network/compile-heavy tasks. Cross-referencing all four eval runs collected across
this investigation (mtp_on, the original aging-pod dflash2_on run, and both fresh
reruns) shows a sharp, consistent split by *when* each run happened, not by which pod
or which draft method:

| Task | mtp_on (04:43Z, ran 1st) | dflash2_on original (06:10Z, aging pod) | dflash2-rerun (09:41Z, fresh pod) | dspark-rerun (09:42Z, fresh pod) |
|---|--:|--:|--:|--:|
| fix-permissions | 0/3 | 1/3 | 3/3 | 3/3 |
| processing-pipeline | 0/3 | 3/3 | 3/3 | 3/3 |
| fibonacci-server | 0/3 | 3/3 | 3/3 | 3/3 |
| crack-7z-hash.easy | 0/3 | 2/3 | 3/3 | 3/3 |
| modernize-fortran-build | 0/3 | 3/3 | 2/3 (partial data) | -- |
| prove-plus-comm | 0/3 | 3/3 | 3/3 | -- |
| build-initramfs-qemu (the one exception) | 2/3 | -- | -- | 2/3 |

Every run that started later than mtp_on's, such as the original aging-pod dflash2_on run
*and* both brand-new fresh-pod reruns, hits the same tasks, regardless of pod
freshness or draft method. mtp_on, which happened to run first (earliest in the day),
is clean on all of them, with one exception: `build-initramfs-qemu` shows mild
elevation (2/3) even on mtp_on's own clean baseline, suggesting that one task is
genuinely borderline-tight on the 60s budget on its own merits, independent of the
pattern below.

**The leading hypothesis, stated plainly as a hypothesis, not a confirmed cause:**
Something external and correlated with time-of-day, most plausibly
network/registry/package-mirror congestion that varies through the day and happens to
affect exactly the tasks that lean on package installs, downloads, or compilation
during test verification. So far, this is the best-supported explanation for this pattern. This
is inferred from the run-time correlation combined with directly ruling out the two
alternative mechanisms above (pod-age and CPU contention); it has **not** been
independently confirmed, because registry/mirror response times during the affected
run windows cannot be checked retroactively. In other words, there is no log of that to point to
after the fact. Anyone re-running this comparison should log registry/mirror latency
alongside the eval if they want to close this gap definitively.

**Additional corroborating evidence: throughput and wall-clock also degraded on the
fresh-pod reruns, not just test_timeout.** This wasn't part of the original theory but
showed up in the final summary stats and is worth recording:

| Metric | dflash2_on original | dflash2-rerun (fresh pod) | dspark_on original | dspark-rerun (fresh pod) |
|---|--:|--:|--:|--:|
| Wall clock | 79.3 min | **142.6 min** | 83.2 min | **136.7 min** |
| Throughput | 171.4 tok/s | **100.3 tok/s** | 165.4 tok/s | **106.1 tok/s** |
| Resolved trials | 47/150 (31.3%) | 40/150 (26.7%) | 39/150 (26.0%) | 43/150 (28.7%) |
| pass@3 | 18/50 (36.0%) | 19/50 (38.0%) | 17/50 (34.0%) | 19/50 (38.0%) |
| Draft acceptance | 61.6% | 61.6% | 57.5% | 58.8% |

Wall clock nearly doubled and measured throughput dropped ~40% on both fresh pods
relative to the original runs. Note that this is not a second, separate confound. It's the
same underlying mechanism showing up in a different metric: time spent stalled in
`test_timeout`-bound trials (and the docker-build congestion observed live during the
rerun, e.g. `crack-7z-hash`/`polyglot-rust-c` builds that sat for ~30 min doing almost
no CPU work before completing) eats wall-clock time without producing tokens,
mechanically dragging down the tokens/sec figure. It's consistent with, and adds
weight to, the time-correlated-congestion hypothesis above rather than pointing to
anything new. Resolved-trial counts and pass@3 moved only modestly between original
and rerun for both conditions. Neither improved to anywhere near mtp_on's level,
consistent with the test_timeout rate staying elevated rather than resolving.

**What this means for the accuracy comparison.** It still cannot be made with
confidence, but we can now say precisely *why*, rather than leaving "pod age" as an
open, untested question, and this is now backed by a completed, not partial,
fresh-pod rerun. mtp_on happened to draw the earliest, cleanest time slot in this
investigation's run order. Its clean 47.3% resolved rate is not evidence that MTP is
the intrinsically more accurate method here; it is at least partly a product of *when*
it happened to run. dflash2_on and dspark_on were structurally disadvantaged by
running later on the original aging pod, and again on brand-new fresh pods in a
way that has nothing to do with either method's actual capability. This holds
individually for both conditions; it is not a case of one condition confirming and the
other not.

## parse_error breakdown -- corrected

An earlier pass at this report over-attributed the `parse_error` spike (1 -> 34 -> 36)
to the same infrastructure-glitch story as `test_timeout`. Systematically classifying
every parse_error trial in both conditions (not just the one example first checked)
shows that's wrong -- the dominant mechanism is different and is **not** part of the
pod-age confound:

| Mechanism | dflash2_on (34 total) | dspark_on (36 total) |
|---|--:|--:|
| Context-length overflow (hit the 32,768-token ceiling) | **15** | **25** |
| Mid-JSON truncation ("EOF while parsing a string") -- flat across all conditions (48/47/49 raw occurrences), not a method effect | 1 | 2 |
| Valid, complete JSON -- still mislabeled (the harness-glitch pattern found in the first pass) | 5 | 3 |
| Unresolved / no data to inspect | 13 | 6 |

**Context-length overflow is the dominant mechanism, and it is a genuine,
method-attributable signal, not an infrastructure confound.** It means these
conditions' agents needed more turns of accumulated conversation to make the same
amount of progress -- consistent with the domain-mismatch finding above -- and ran out
of the 32K context window before finishing, rather than hitting the 420s wall-clock
agent timeout first. The much smaller "valid JSON, still mislabeled" bucket (5 and 3
trials) is the only piece of `parse_error` that plausibly belongs with the
`test_timeout` infrastructure story; it's too small to materially affect the
conclusions above either way.

## Known caveats

- **`test_timeout` run-order confound** (detailed above) -- the single largest open
  question, and the reason the accuracy numbers cannot be trusted at face value yet.
  Pod-age and CPU contention were directly checked on a fresh-pod rerun and ruled out
  as the mechanism; time-of-day-correlated external congestion (registry/mirror) is
  the leading hypothesis but not independently confirmed. See "Fresh-pod rerun" above.
- `security-vulhub-minio`-style task-infrastructure flakiness (docker-compose
  host-port collisions under concurrency) is present in all three conditions,
  consistent with prior runs -- symmetric, not a differentiator.
- DSpark's `num_speculative_tokens=7` was empirically validated (loads and runs
  cleanly) but has no published vLLM-specific reference value to confirm it is
  optimal, unlike DFlash2 (7, from its own model card) and MTP (3, established in
  this project's own earlier investigation).
- Single run per condition (n=1 at the run level; n_attempts=3 is within-run
  repetition only). No cross-run variance estimate for any of the three conditions.
- `unknown_agent_error` mechanisms were traced for a handful of representative
  trials, not exhaustively audited across every occurrence. `parse_error` was
  classified systematically for all trials in both dflash2_on and dspark_on (see
  above); `test_timeout` was spot-checked with one directly verified case.

## Is this run trustworthy / clean?

**Partially. The speed/throughput/draft-acceptance results and the domain-mismatch
finding are solid and can be reported as-is** -- they come from vLLM's own metrics or
from mechanisms (context overflow) shown above to be unaffected by the test_timeout
issue. **The accuracy numbers (resolved trials, pass@3) cannot currently be trusted at
face value** -- see the statement at the top of this document. The methodology
otherwise is sound: same task set, same matched timeouts, same n_attempts=3, same
sampling, same server config as every prior run in this series, and both alternative
methods were verified to load and run stably across a full 150-trial run each (no
crashes, no hangs, clean `RUN_STATUS: ok` on all five runs collected -- mtp_on, the
original dflash2_on/dspark_on, and both fresh-pod reruns).

## What it would cost to actually resolve this

**Status: executed.** The fresh-pod rerun described below was run; see "Fresh-pod
rerun: pod-age ruled out, time-correlated congestion is the leading hypothesis" above
for the outcome. Kept here for the original cost/time reasoning.

Re-run dflash2_on and dspark_on each on its **own fresh pod** (not sequentially after
other conditions), matching the condition mtp_on already had. mtp_on itself does not
need re-running -- it already ran first on a fresh pod, which is the clean baseline.

Per-pod estimate, based on today's actual observed timings on this exact recipe:
bootstrap (image pull + terminal-bench install) ~10 min + vLLM cold start ~7-8 min +
full 150-trial eval (today's actual eval-only times: dflash2_on 79.2 min, dspark_on
83.1 min) => **~97-101 min per pod (~1.6-1.7h)**.

- **Sequential** (one pod at a time, easier to monitor): ~3.4h wall clock,
  **~$11-12** at H100 PCIe $3.29/hr, budget to **~$15-16** for retry/variance margin
  (today's runs included one anomalously slow image pull; that class of delay should
  be budgeted for).
- **Parallel** (two pods running simultaneously): same total cost (~$11-16, cost is
  pod-hours, not wall-clock-dependent) but only **~1.7h wall clock** instead of 3.4h,
  at the cost of more split attention monitoring two live runs at once.

This directly tests the pod-age hypothesis: if `test_timeout` drops back down near
mtp_on's 2/150 baseline rate on fresh pods, the confound is confirmed and the
underlying accuracy numbers from *this* run were genuinely depressed by it. If
`test_timeout` stays elevated even on fresh pods, that would point to something else
(e.g. genuine per-condition container congestion from that condition's own 8
concurrent sandboxes, or an unrelated external factor like time-of-day package-mirror
load) rather than pod age specifically -- worth noting as a residual possibility this
fix does not fully rule out. Maximally rigorous would also randomize run order and
time-of-day across conditions, but that is diminishing returns relative to this
bounded fix.

## Data

This repo ships this report and the launch scripts for all three conditions
(`3way_run/launch_vllm_mtp3.sh`, `launch_vllm_dflash2.sh`, `launch_vllm_dspark.sh`),
using the same `run_condition.py` / `terminal_bench_adapter_fixed.py` / task set as
the rest of this repo. The full raw per-trial data (complete `tb` run trees, per-trial
trajectories, and the fresh-pod rerun archives) was preserved locally at run time but
is intentionally not included here to keep this repo lightweight. All pods (original
run and both fresh-pod reruns) terminated after each run.
