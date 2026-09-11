# Qwen3.8-27B MTP Rollout Speed Comparison

An experiment measuring the effect of MTP (multi-token prediction / speculative decoding) on RL rollout speed and accuracy, run against Qwen3.8-27B-FP8 on a single H100 via vLLM. Done as part of a broader RL training learning project, see [cuda-kernel-rl-env](https://github.com/MrSnazMan/cuda-kernel-rl-env) for the related environment-design work.

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

**Key finding**: the speedup mostly converts `agent_timeout` failures (43→9) into `unknown_agent_error` failures (4→24) rather than into successes. Faster generation gives the agent more time to attempt genuinely hard tasks, most of which it still gets wrong for unrelated reasons. Full methodology, caveats, and failure-mode breakdown in `results/final_run/COMPARISON.md`.

## Acknowledgments

- [vLLM](https://github.com/vllm-project/vllm) — inference serving
- [terminal-bench](https://github.com/laude-institute/terminal-bench) — the benchmark harness
- [GEPA](https://github.com/gepa-ai/gepa) — the `TerminusAdapter` used to wire the agent to vLLM
- Qwen / Alibaba — the base model
- [Prime Intellect](https://primeintellect.ai) — GPU pod infrastructure
- [Claude Code](https://claude.com/claude-code) (Anthropic) — used extensively for infrastructure setup/debugging and the terminal-bench integration

## License

MIT
