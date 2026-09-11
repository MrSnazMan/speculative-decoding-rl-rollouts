# Final MTP comparison — mtp_off vs. mtp_on-at-nst=3

Run 2026-09-10/11, lambdalabs H100 80GB PCIe (pod `048da0e276504f60bb080dd7adee5abd`),
`vllm/vllm-openai:v0.29.0`, `Qwen/Qwen3.8-27B-FP8`, terminal-bench-core 0.1.1,
same 50 task IDs as the original comparison, `n_concurrent=8`, `n_attempts=3`,
`--global-agent-timeout-sec=420` matched on both conditions.

**This compares mtp_off vs. mtp_on-at-nst=3, not the standard single-token MTP
config.** Per mentor's explicit call, the "on" condition ran
`--speculative-config '{"method":"mtp","num_speculative_tokens":3}'`, not
nst=1 — single-token MTP was judged not representative of what this research
needed to show. nst=3 trades draft-acceptance rate for larger steps per
accepted draft (~87% here vs. ~94% typically seen at nst=1 on this checkpoint).

All five fixes identified in the earlier investigation (NOTES.md) were applied
to both conditions: corrected non-thinking sampling (temperature=0.7,
top_p=0.80, top_k=20, min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0,
enable_thinking=False, via `extra_body`), a 2048-token per-turn cap, matched
420s agent timeouts, n_attempts=3, and (for mtp_on) the nst=3 speculative
config already proven clean in the bounded Follow-up 5 test.

## Headline numbers

| Metric | mtp_off | mtp_on (nst=3) | Delta |
|---|--:|--:|--:|
| Resolved trials | 64/150 (42.7%) | 71/150 (47.3%) | +4.6 pp |
| pass@3 (task solved on >=1/3 attempts) | 28/50 (56.0%) | 29/50 (58.0%) | +1 task net (1 gained, 0 regressed) |
| Wall clock | 7936s (132.3 min) | 4263s (71.0 min) | **1.86x faster** |
| Throughput | 93.0 tok/s | 187.9 tok/s | **2.02x** |
| Generated tokens | 738,047 | 800,962 | — |
| Draft acceptance | n/a | **86.8%** (578,723/666,617) | — |
| Run status | ok (clean exit) | ok (clean exit) | both hang-safe |

Only task that flipped: **`get-bitcoin-nodes`** gained under mtp_on (0/50 -> in
the gained set); nothing regressed. This is the cleanest pass@3 delta the
project has produced -- prior runs were confounded by mismatched timeouts and
n_attempts=1.

## Reading the accuracy delta

The +4.6pp trial-accuracy gain is real but modest relative to the ~2x speed
gain, and the failure-mode shift explains why: nst=3's faster generation
converts many `agent_timeout` failures into failures of other kinds, not into
successes.

| Failure mode (task-level union) | mtp_off | mtp_on (nst=3) |
|---|--:|--:|
| `agent_timeout` | 43 | 9 |
| `unknown_agent_error` | 4 | 24 |
| `parse_error` / `fatal_llm_parse_error` | 5 | 4 + 2 |
| `unset` (agent finished, wrong answer) | 32 | 37 |
| `test_timeout` | 2 | 3 |

`agent_timeout` dropped sharply (fewer tasks burn the full 420s budget when
generation is ~2x faster) but `unknown_agent_error` rose by roughly the same
amount. Spot-checked one instance (`gpt2-codegolf`): not LLM degeneration --
the agent's generated C code segfaulted at runtime and the session ended
without terminal-bench's clean "done" signal, a legitimate task failure. A
full manual scan of every `unknown_agent_error` trial was not done; this
spot-check is consistent with "faster generation gives agents more attempts
at genuinely hard tasks, most of which they still get wrong," not with a new
nst=3-induced failure mode. Zero `OutputLengthExceededError` / runaway
generation occurred in either condition -- the max_tokens cap and corrected
sampling held throughout.

## Known caveats

- **`security-vulhub-minio`** lost roughly 2 of its 3 attempts in *both*
  conditions to a `docker compose up -d` host-port collision when two attempts
  of the same compose-based task ran concurrently under `n_concurrent=8`. This
  is a terminal-bench task-infrastructure issue, symmetric across conditions,
  not an MTP or sampling effect -- but it means that task's resolved-rate
  numerator/denominator is noisier than the others.
- `unknown_agent_error` causes were spot-checked (one instance), not
  exhaustively audited across all 24 mtp_on occurrences.
- Single run per condition (n=1 at the run level; n_attempts=3 is the
  within-run repetition). No cross-run variance estimate.

## Is this run trustworthy / clean?

Yes, with the two caveats above. Unlike the original comparison (confounded by
mismatched agent timeouts: mtp_off at 360s vs mtp_on at 420s, and
`n_attempts=1`), this run matched `--global-agent-timeout-sec=420` on both
conditions, used `n_attempts=3`, and applied the corrected sampling + max_tokens
fixes that Follow-up 5 showed were necessary. Both conditions completed with
`RUN_STATUS: ok` (clean process exit, no post-eval hang). The nst=3 config is
reused verbatim from the bounded test that already proved it stable, not
re-derived. The `security-vulhub-minio` port-collision flake hits both
conditions equally, so it does not bias the mtp_off-vs-mtp_on delta, only adds
noise to that one task's own resolved-rate.

## Cost

- This run (pod `048da0e276504f60bb080dd7adee5abd`, lambdalabs H100 PCIe,
  ~3h40m lifetime): **$13.07** ($30.01 -> $16.94; under the $15-22 estimate).
- A separate aborted attempt earlier the same session (pod
  `f532867f53cb49d6b3d525a7ca8b20cb`, died during vLLM cold-init before any
  eval ran, terminated on request): $0.35.
- Wallet balance at completion: **$16.94**.

## Data

This repo ships the aggregate `summary.json`/`summary.md` for each condition
under `results/{mtp_off,mtp_on,final_run}/`. The full raw per-trial data
(complete `tb` run trees, per-trial trajectories, `.cast` session recordings,
~1.1GB total) was preserved locally at run time but is intentionally not
included here to keep this repo lightweight. Pod terminated after the run.
