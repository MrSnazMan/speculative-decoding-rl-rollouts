# MTP on/off comparison — Qwen3.8-27B-FP8 on terminal-bench-core 0.1.1 (50 shortest tasks)

Single pod (`qwen38-mtp-compare`, lambdalabs H100 80GB), `vllm/vllm-openai:v0.29.0`,
`--enforce-eager --max-model-len 32768 --kv-cache-dtype fp8_e4m3
--gpu-memory-utilization 0.85`, terminal-bench Terminus agent via GEPA adapter,
`n_concurrent = 8`, `n_attempts = 1`.

- **mtp_off** run id `temp_gepa_run_20260910014445`, 2026-09-10 01:44–02:36 UTC
- **mtp_on**  run id `temp_gepa_run_20260910034358`, 2026-09-10 03:44–04:28 UTC,
  added `--speculative-config '{"method":"mtp","num_speculative_tokens":1}'`

## Headline

| | mtp_off | mtp_on |
|---|--:|--:|
| resolved / 50 | 21 | 24 |
| accuracy | 42% | 48% |
| eval wall clock | 51.6 min | 44.0 min |
| generation tokens (vLLM) | 437,315 | 452,589 |
| aggregate tok/s (gen ÷ wall) | 141 | 171 (+21%) |
| **agent cap per task** | **360 s** (tb default) | **420 s** (`--global-agent-timeout-sec`) |
| agent-timeout events | 27 | 16 |
| MTP draft-token acceptance | — | 93.8% (218,040 / 232,453) |

## Speed (the clean signal)

On the **21 tasks that genuinely ran to completion under both conditions** (real
token counts, not cap-bound), median `agent_time(mtp_on) / agent_time(mtp_off)` =
**0.56** (mean 0.61). MTP roughly **halved** agent wall-time on normal tasks, with
~94% draft acceptance. The aggregate throughput gain is smaller (+21%) because
cap-bound timeout tasks burn their full budget regardless and dominate the tail.

## Accuracy: the specific question — do the mtp_off timeout/parse_error tasks resolve?

Of the **22** mtp_off tasks that failed via `agent_timeout` (15) or `parse_error`
(7) — all cap-bound — **only 3 resolve under mtp_on**:

| task | mtp_off | mtp_on | mtp_on agent_s |
|---|---|---|--:|
| cartpole-rl-training | agent_timeout | **RESOLVED** | 661 |
| password-recovery | parse_error | **RESOLVED** | 203 |
| tmux-advanced-workflow | parse_error | **RESOLVED** | 267 |
| build-initramfs-qemu | parse_error | still fail (parse_error) | 522 |
| build-tcc-qemu | agent_timeout | still fail (unknown_agent_error) | 255 |
| chess-best-move | parse_error | still fail (agent_timeout) | 675 |
| configure-git-webserver | parse_error | still fail (unknown_agent_error) | 402 |
| extract-moves-from-video | agent_timeout | still fail (parse_error) | 720 |
| get-bitcoin-nodes | parse_error | still fail (parse_error) | 720 |
| gpt2-codegolf | agent_timeout | still fail (agent_timeout) | 720 |
| intrusion-detection | parse_error | still fail (unset) | 364 |
| jupyter-notebook-server | agent_timeout | still fail (agent_timeout) | 499 |
| path-tracing | agent_timeout | still fail (agent_timeout) | 501 |
| path-tracing-reverse | agent_timeout | still fail (unknown_agent_error) | 290 |
| polyglot-c-py | agent_timeout | still fail (agent_timeout) | 720 |
| polyglot-rust-c | agent_timeout | still fail (agent_timeout) | 720 |
| raman-fitting | agent_timeout | still fail (agent_timeout) | 720 |
| raman-fitting.easy | agent_timeout | still fail (agent_timeout) | 720 |
| reshard-c4-data | agent_timeout | still fail (unset) | 177 |
| sanitize-git-repo.hard | agent_timeout | still fail (unknown_agent_error) | 274 |
| security-vulhub-minio | agent_timeout | still fail (parse_error) | 720 |
| write-compressor | agent_timeout | still fail (agent_timeout) | 720 |

Full task-level movement: **+7 gained, −4 regressed, net +3** (21 → 24).

- **Gained** (fail→resolve): fix-git, tmux-advanced-workflow, sanitize-git-repo,
  decommissioning-service-with-sensitive-data, cartpole-rl-training,
  new-encrypt-command, password-recovery
- **Regressed** (resolve→fail): csv-to-parquet (test_timeout), organization-json-generator,
  sqlite-db-truncate (agent_timeout), fibonacci-server

## Caveats — read before trusting the +3

1. **Agent caps were not matched.** mtp_off ran at tb's default 360 s agent
   timeout; mtp_on ran at 420 s. mtp_on had 60 s more per task — this favours
   mtp_on on accuracy and partly explains fewer timeout events (16 vs 27). A
   fair rerun must set the same `--global-agent-timeout-sec` for both.
2. **n_attempts = 1.** With single-shot sampling over 50 tasks, a 7-gain/4-loss
   split is well within run-to-run noise. The +3 accuracy delta is not a
   reliable effect; the ~1.8× per-task speedup is.
3. Several mtp_on failures shifted failure mode (→ `unknown_agent_error`,
   `parse_error`) rather than resolving — MTP speed alone doesn't rescue tasks
   that need many more agent turns or hit tooling/harness errors.

## Bottom line

MTP (num_speculative_tokens=1) delivers a large, clean **per-task generation
speedup (~1.8×, 94% acceptance)** with no correctness regression attributable to
MTP itself. It does **not** meaningfully convert the cap-bound timeout failures
(3 of 22), and the small aggregate accuracy gain (+3/50) is confounded by the
mismatched agent timeout and single-attempt noise. To make an accuracy claim:
rerun both conditions with a matched `--global-agent-timeout-sec` and
`n_attempts >= 3`.
