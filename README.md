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
| Draft acceptance | n/a | 86.8% | n/a |

**Main Results**: the speedup mostly converts `agent_timeout` failures (43→9) into `unknown_agent_error` failures (4→24) rather than into successes. Faster generation gives the agent more time to attempt the more difficult tasks, most of which it still ends up getting wrong for unrelated reasons. Full methodology, caveats, and failure-mode breakdown in `results/final_run/COMPARISON.md`.

## 3-way comparison: MTP vs. DFlash2 vs. DSpark

Extended the above to compare MTP against two third-party speculative-decoding methods with larger draft blocks: [DFlash2](https://huggingface.co/incoai/Qwen3.8-27B-DFlash2) and [DSpark](https://huggingface.co/RadixArk/Qwen3.8-27B-DSpark) (`num_speculative_tokens=7` each, vs. MTP's 3), same task set, same matched timeouts and sampling.

**Main finding**: this looks like a domain mismatch more than a sampling-mode difference. DFlash2 and DSpark's published benchmarks (the DFlash paper, arxiv 2602.06036, and the DFlash2 model card) only report acceptance rate on GSM8K, MATH, HumanEval, MBPP, and MT-Bench: short, single or few-turn completions. Neither covers agentic, tool-use, or terminal/shell-command workloads, and there's no published benchmark for DSpark at all. The rollouts tested here are long multi-turn agent sessions full of shell commands, file paths, and strict tool-call JSON, a token distribution these draft models were never trained or tuned on. Draft acceptance came in well below MTP's: 86.3% for MTP, 61.6% for DFlash2, 57.5% for DSpark. If a speculative-decoding method's published gains come from math or single-function-code benchmarks, check its acceptance rate on your actual workload, instead of immediately taking them at face value.

| Metric | mtp_on (nst=3) | dflash2_on (nst=7) | dspark_on (nst=7) |
|---|--:|--:|--:|
| Draft acceptance | 86.3% | 61.6% | 57.5% |
| Throughput | 183.9 tok/s | 171.4 tok/s | 165.4 tok/s |
| Wall clock | 74.4 min | 79.3 min | 83.2 min |

These come straight from vLLM's own request metrics, so they hold up regardless of the caveat below. DFlash2 and DSpark had similar or higher peak per-token generation rates on their own, but their lower acceptance meant more verification rounds went to waste, so both ended up slower end-to-end than MTP. Bigger draft blocks didn't win on speed in this case.

The accuracy comparison was less conclusive. dflash2_on and dspark_on hit a sandbox test-infrastructure failure (`test_timeout`, unrelated to the LLM itself) far more often than mtp_on, and in the worst case that closes most of the measured resolved-trials/pass@3 gap. This got checked thoroughly, including a fresh-pod rerun of both conditions to rule out pod age as the cause. It wasn't pod age, and it wasn't CPU contention from the draft models either. The best explanation right now is congestion tied to time of day, backed by solid evidence but not independently confirmed. Don't read the resolved-trials/pass@3 numbers for dflash2_on or dspark_on as a confident accuracy comparison against mtp_on yet. Full writeup, including the rerun, is in `results/3way_run/COMPARISON.md`.

## Acknowledgments

- [vLLM](https://github.com/vllm-project/vllm): inference serving
- [terminal-bench](https://github.com/laude-institute/terminal-bench): the benchmark harness
- [GEPA](https://github.com/gepa-ai/gepa): the `TerminusAdapter` used to wire the agent to vLLM
- Qwen / Alibaba: the base model
- [Prime Intellect](https://primeintellect.ai): GPU pod infrastructure
- [Claude Code](https://claude.com/claude-code) (Anthropic): used extensively for infrastructure setup and debugging, plus the terminal-bench integration

## License

MIT
