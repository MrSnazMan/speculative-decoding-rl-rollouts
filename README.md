# Qwen3.8-27B Speculative-Decoding Rollout Speed Comparison

Experiments measuring the effect of speculative decoding on RL rollout speed and accuracy, run against Qwen3.8-27B-FP8 on H100 GPUs via vLLM. Starts with MTP (multi-token prediction) on vs. off, then extends to a 3-way comparison against two third-party draft-model methods, DFlash2 and DSpark. Done as part of a broader RL training learning project, see [cuda-kernel-rl-env](https://github.com/MrSnazMan/cuda-kernel-rl-env) for the related environment-design work.

## Setup

terminal-bench-core 0.1.1 (50 tasks, 3 attempts each), matched 420s agent timeouts on both conditions, `vllm/vllm-openai:v0.29.0`, `--enforce-eager`, MTP at `num_speculative_tokens=3`.

## Results

| Metric | MTP off | MTP on (nst=3) | Delta |
|---|--:|--:|--:|
| Resolved trials | 64/150 (42.7%) | 71/150 (47.3%) | +4.6 pp |
| pass@3 | 28/50 (56.0%) | 29/50 (58.0%) | +1 net |
| Wall clock | 132.3 min | 71.0 min | **1.86x faster** |
| Throughput | 93.0 tok/s | 187.9 tok/s | **2.02x** |
| Draft acceptance | n/a | 86.8% | — |

**Main Results**: the speedup mostly converts `agent_timeout` failures (43→9) into `unknown_agent_error` failures (4→24) rather than into successes. Faster generation gives the agent more time to attempt the more difficult tasks, most of which it still ends up getting wrong for unrelated reasons. Full methodology, caveats, and failure-mode breakdown in `results/final_run/COMPARISON.md`.

## 3-way comparison: MTP vs. DFlash2 vs. DSpark

Extended the above to compare MTP against two third-party speculative-decoding methods with larger draft blocks: [DFlash2](https://huggingface.co/incoai/Qwen3.8-27B-DFlash2) and [DSpark](https://huggingface.co/RadixArk/Qwen3.8-27B-DSpark) (`num_speculative_tokens=7` each, vs. MTP's 3), same task set, same matched timeouts and sampling.

**Headline finding: domain mismatch, not just a sampling-mode difference.** DFlash2's and DSpark's published benchmarks (the DFlash paper, arxiv 2602.06036, and the DFlash2 model card) report acceptance rate exclusively on GSM8K, MATH, HumanEval, MBPP, and MT-Bench — short, templated, single-or-few-turn completions. Neither evaluates on any agentic, tool-use, or terminal/shell-command workload, and no equivalent published benchmark exists for DSpark at all. Measured here, on long multi-turn agentic rollouts dense with shell commands, file paths, and strict tool-call JSON — a token distribution these draft models were never trained or tuned against — draft acceptance came in well below MTP's: **86.3% (MTP) vs. 61.6% (DFlash2) vs. 57.5% (DSpark)**. Speculative-decoding methods whose published gains come from math/single-function-code benchmarks should not be assumed to transfer those gains to agentic RL rollout workloads; validate acceptance rate on the actual target workload before trusting the paper's numbers.

**Trustworthy metrics** (vLLM's own request metrics, independent of sandbox test execution — see caveat below for what *isn't* trustworthy):

| Metric | mtp_on (nst=3) | dflash2_on (nst=7) | dspark_on (nst=7) |
|---|--:|--:|--:|
| Draft acceptance | 86.3% | 61.6% | 57.5% |
| Throughput | 183.9 tok/s | 171.4 tok/s | 165.4 tok/s |
| Wall clock | 74.4 min | 79.3 min | 83.2 min |

Despite similar-or-higher peak per-token generation rates in isolation, DFlash2's and DSpark's much lower acceptance meant more verification rounds went to waste — both ended up with a *slower* end-to-end wall clock than MTP. Larger draft blocks did not translate into a speed win here.

**What's not (yet) trustworthy: the accuracy comparison.** A sandbox test-infrastructure failure mode (`test_timeout`, unrelated to the LLM) occurred far more often under dflash2_on and dspark_on than under mtp_on, closing most of the measured resolved-trials/pass@3 gap in the worst case. This was investigated in depth — including a fresh-pod rerun of both alternative conditions to rule out pod-age as the cause (it was ruled out, along with CPU contention from the draft models) — and the leading explanation is time-of-day-correlated external congestion (well-supported by task-clustering evidence, but not independently confirmed). **The resolved-trials and pass@3 numbers for dflash2_on and dspark_on should not be read as a confident accuracy comparison against mtp_on.** Full investigation, evidence, and the final fresh-pod-rerun results: `results/3way_run/COMPARISON.md`.

## Acknowledgments

- [vLLM](https://github.com/vllm-project/vllm) — inference serving
- [terminal-bench](https://github.com/laude-institute/terminal-bench) — the benchmark harness
- [GEPA](https://github.com/gepa-ai/gepa) — the `TerminusAdapter` used to wire the agent to vLLM
- Qwen / Alibaba — the base model
- [Prime Intellect](https://primeintellect.ai) — GPU pod infrastructure
- [Claude Code](https://claude.com/claude-code) (Anthropic) — used extensively for infrastructure setup/debugging and the terminal-bench integration

## License

MIT
