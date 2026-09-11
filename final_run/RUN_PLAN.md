# Final MTP off-vs-on comparison — run plan (as corrected 2026-09-10)

Trustworthy, reportable comparison. Every known bug from the investigation
(NOTES.md, Follow-ups 1-5) fixed and combined into one clean run.

## Conditions

- **mtp_off**: vLLM launched with NO `--speculative-config`.
- **mtp_on**: vLLM launched with
  `--speculative-config '{"method":"mtp","num_speculative_tokens":3}'`

  **nst=3, NOT nst=1** — mentor's explicit call. Single-token MTP "isn't
  representative of what this research needs to show for this type of
  comparison." nst=3 trades acceptance rate (~87% vs ~94% at nst=1) for larger
  steps per accepted draft. Same config proven clean in NOTES.md Follow-up 5
  (no crash, no degeneration once sampling was corrected).

  Report writeup MUST say explicitly "mtp_off vs. mtp_on-at-nst=3" and name the
  acceptance/step-size tradeoff — not generic "MTP on".

## Fixes applied to both conditions

1. `max_tokens` ~2048/turn  — `train_terminus.py` `TunedLiteLLM._OPENAI_SAMPLING`
   + `OutputLengthExceededError` catch.
2. Corrected sampling — `enable_thinking=False, temperature=0.7, top_p=0.80,
   top_k=20, min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0`
   (top_k / min_p / repetition_penalty / chat_template_kwargs via `extra_body`;
   `LiteLLM.call()` hardcodes `drop_params=True`).
3. Matched `--global-agent-timeout-sec=420` on both — `run_condition.py`
   `GLOBAL_AGENT_TIMEOUT_SEC` default 420.
4. `n_attempts=3` per task on both — 4th positional arg to `run_condition.py`.

## Server config (matches every prior working run — do not deviate)

`vllm/vllm-openai:v0.29.0`, `Qwen/Qwen3.8-27B-FP8`,
`--enforce-eager --max-model-len 32768 --kv-cache-dtype fp8_e4m3
--gpu-memory-utilization 0.85`. No `VLLM_ENABLE_CUDA_COMPATIBILITY`.
Fresh lambdalabs H100 80GB pod.

## Sequence

1. mtp_off first: `launch_vllm.sh ''`, wait for `/health` 200,
   `run_condition.py mtp_off task_ids.txt 8 3` inside tmux.
2. Checkpoint-pull `runs_mtp_off/` + tb `runs/` tree periodically (not only at end).
3. Swap vLLM: `docker rm -f vllm_server; launch_vllm.sh '{"method":"mtp","num_speculative_tokens":3}'`,
   wait for `/health` 200.
4. mtp_on: `run_condition.py mtp_on task_ids.txt 8 3` inside tmux.
5. Final pull, then `prime pods terminate`.

## Safeguards (non-negotiable)

- `run_condition.py` launched inside tmux / with nohup — never a plain
  foreground SSH command. A local disconnect must not kill the remote run.
- Checkpoint-pull partial results periodically during each condition.
- Reuse the saved `task_ids.txt` (50 tasks) — do not re-run task selection.

## Report back

- resolved/50 for each condition, wall-clock, tok/s, draft acceptance rate for mtp_on.
- State plainly whether the run is clean/trustworthy given all fixes, or flag
  anything still confounded.
- Final cost and remaining wallet balance.
