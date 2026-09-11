"""Run one condition (MTP off or MTP on) of the terminal-bench MTP comparison.

Usage: run_condition.py <condition_label> <task_ids_file> <n_concurrent> [<n_attempts>]
  e.g. run_condition.py mtp_off task_ids.txt 8 3
       run_condition.py mtp_on  task_ids.txt 8 3

Assumes:
  - vLLM server already up at http://localhost:8000/v1, serving Qwen/Qwen3.8-27B-FP8
    (with or without --speculative-config, matching the condition being run).
  - terminal_bench_adapter_fixed.py and train_terminus.py are in the same directory.

Writes, under runs_<condition_label>/:
  - summary.json   aggregate metrics + per-task attempt breakdown
  - summary.md     human-readable summary

The summary is computed from tb's own runs/<run_id>/results.json (every trial,
all attempts), not from the GEPA adapter's per-task parse -- that only sees
attempt 1 when n_attempts > 1.

Hang safety (from the first mtp_off run wedging ~1h post-eval): the adapter runs
`tb run` in its own process group with a hard wall-clock cap and SIGKILLs the
group on expiry; this script also arms a SIGALRM backstop and always writes the
summary from whatever landed in the tb tree.
"""

import glob
import json
import math
import os
import signal
import sys
import time
import urllib.request

os.environ.setdefault("OPENAI_API_BASE", "http://localhost:8000/v1")
os.environ.setdefault("OPENAI_BASE_URL", "http://localhost:8000/v1")
os.environ.setdefault("OPENAI_API_KEY", "sk-local-dummy")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from terminal_bench_adapter_fixed import TerminalBenchTask, TerminusAdapter  # noqa: E402

MODEL_NAME = "openai/Qwen/Qwen3.8-27B-FP8"
METRICS_URL = "http://localhost:8000/metrics"

GLOBAL_AGENT_TIMEOUT_SEC = float(os.environ.get("RUN_CONDITION_AGENT_TIMEOUT_SEC", "420"))
TB_HARD_CAP_PAD_SEC = float(os.environ.get("RUN_CONDITION_TB_HARD_CAP_PAD_SEC", "2400"))
SCRIPT_HARD_CAP_SEC = int(os.environ.get("RUN_CONDITION_HARD_CAP_SEC", "21600"))  # 6h


class _ScriptHardCap(Exception):
    pass


def _on_alarm(signum, frame):
    raise _ScriptHardCap()


def fetch_metric(text: str, name: str) -> float | None:
    for line in text.splitlines():
        if line.startswith(name + " ") or line.startswith(name + "{"):
            try:
                return float(line.rsplit(" ", 1)[-1])
            except ValueError:
                continue
    return None


def fetch_metrics_snapshot() -> dict:
    try:
        with urllib.request.urlopen(METRICS_URL, timeout=10) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return {"error": str(e)}
    return {
        "generation_tokens_total": fetch_metric(text, "vllm:generation_tokens_total"),
        "prompt_tokens_total": fetch_metric(text, "vllm:prompt_tokens_total"),
        "spec_decode_num_draft_tokens_total": fetch_metric(
            text, "vllm:spec_decode_num_draft_tokens_total"
        ),
        "spec_decode_num_accepted_tokens_total": fetch_metric(
            text, "vllm:spec_decode_num_accepted_tokens_total"
        ),
    }


def _estimate_tb_wall_sec(n_tasks: int, n_concurrent: int, n_attempts: int) -> float:
    # Most trials finish well under the agent cap; ~0.6x cap + build/test overhead
    # per wave is a realistic-but-safe estimate for the hard-kill ceiling.
    waves = math.ceil(max(n_tasks * n_attempts, 1) / max(n_concurrent, 1))
    return waves * (0.6 * GLOBAL_AGENT_TIMEOUT_SEC + 220.0)


def _newest_run_dir() -> str | None:
    dirs = sorted(glob.glob("runs/temp_gepa_run_*"), key=os.path.getmtime)
    return dirs[-1] if dirs else None


def _summarize_from_root(task_ids: list[str], n_attempts: int) -> dict:
    """Build the per-task / aggregate summary from tb's runs/<run_id>/results.json."""
    rd = _newest_run_dir()
    trials = []
    meta = {}
    if rd and os.path.exists(os.path.join(rd, "results.json")):
        try:
            trials = json.load(open(os.path.join(rd, "results.json"))).get("results", [])
        except Exception:
            trials = []
    if rd and os.path.exists(os.path.join(rd, "run_metadata.json")):
        try:
            meta = json.load(open(os.path.join(rd, "run_metadata.json")))
        except Exception:
            meta = {}

    by_task: dict[str, list[dict]] = {t: [] for t in task_ids}
    for r in trials:
        by_task.setdefault(r.get("task_id"), []).append(r)

    per_task = []
    n_trials = 0
    n_resolved = 0
    n_tasks_pass_any = 0
    for t in task_ids:
        rs = by_task.get(t, [])
        outcomes = [bool(x.get("is_resolved")) for x in rs]
        fmodes = [x.get("failure_mode") for x in rs if not x.get("is_resolved")]
        n_trials += len(rs)
        n_resolved += sum(outcomes)
        passed_any = any(outcomes)
        n_tasks_pass_any += int(passed_any)
        per_task.append(
            {
                "task_id": t,
                "attempts": len(rs),
                "n_resolved": sum(outcomes),
                "resolved_rate": (sum(outcomes) / len(rs)) if rs else 0.0,
                "pass_any": passed_any,
                "outcomes": outcomes,
                "failure_modes": fmodes,
            }
        )

    return {
        "run_dir": rd,
        "tb_reported_accuracy": meta.get("accuracy"),
        "tb_start": meta.get("start_time"),
        "tb_end": meta.get("end_time"),
        "n_tasks": len(task_ids),
        "n_attempts": n_attempts,
        "n_trials": n_trials,
        "n_resolved_trials": n_resolved,
        "mean_accuracy": (n_resolved / n_trials) if n_trials else 0.0,
        "pass_any_tasks": n_tasks_pass_any,
        "pass_any_rate": (n_tasks_pass_any / len(task_ids)) if task_ids else 0.0,
        "per_task": per_task,
    }


def main():
    condition = sys.argv[1]
    task_ids_file = sys.argv[2]
    n_concurrent = int(sys.argv[3])
    n_attempts = int(sys.argv[4]) if len(sys.argv) > 4 else 1

    with open(task_ids_file) as f:
        task_ids = [line.strip() for line in f if line.strip()]

    out_dir = f"runs_{condition}"
    os.makedirs(out_dir, exist_ok=True)

    batch = [TerminalBenchTask(task_id=t, model_name=MODEL_NAME) for t in task_ids]
    adapter = TerminusAdapter(
        n_concurrent=n_concurrent,
        instruction_prompt_path="prompt-templates/instruction_prompt.txt",
    )

    tb_hard_cap = _estimate_tb_wall_sec(len(batch), n_concurrent, n_attempts) + TB_HARD_CAP_PAD_SEC
    print(
        f"condition={condition} tasks={len(batch)} n_attempts={n_attempts} "
        f"n_concurrent={n_concurrent} agent_cap={GLOBAL_AGENT_TIMEOUT_SEC:.0f}s "
        f"tb_hard_cap={tb_hard_cap:.0f}s"
    )

    signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(SCRIPT_HARD_CAP_SEC)

    metrics_before = fetch_metrics_snapshot()
    t0 = time.time()

    run_status = "ok"
    try:
        adapter.evaluate(
            batch,
            {"instruction_prompt": ""},
            capture_traces=False,
            overall_timeout_sec=tb_hard_cap,
            global_agent_timeout_sec=GLOBAL_AGENT_TIMEOUT_SEC,
            n_attempts=n_attempts,
        )
    except _ScriptHardCap:
        run_status = "script_hard_cap"
        print(f"!! SIGALRM backstop fired at {SCRIPT_HARD_CAP_SEC}s -- summarizing from tb tree")
    except Exception as e:  # noqa: BLE001
        run_status = f"evaluate_exception: {type(e).__name__}: {e}"
        print(f"!! adapter.evaluate raised: {e} -- summarizing from tb tree")
    finally:
        signal.alarm(0)

    wall_clock_sec = time.time() - t0
    metrics_after = fetch_metrics_snapshot()

    core = _summarize_from_root(task_ids, n_attempts)

    def _delta(k):
        a, b = metrics_before.get(k), metrics_after.get(k)
        return (b - a) if (a is not None and b is not None) else None

    gen_tokens = _delta("generation_tokens_total")
    draft_tok = _delta("spec_decode_num_draft_tokens_total")
    accept_tok = _delta("spec_decode_num_accepted_tokens_total")
    draft_accept_rate = (accept_tok / draft_tok) if (draft_tok and draft_tok > 0) else None

    summary = {
        "condition": condition,
        "model": MODEL_NAME,
        "run_status": run_status,
        "n_concurrent": n_concurrent,
        "global_agent_timeout_sec": GLOBAL_AGENT_TIMEOUT_SEC,
        "tb_hard_cap_sec": tb_hard_cap,
        "wall_clock_sec": wall_clock_sec,
        "generated_tokens": gen_tokens,
        "tokens_per_sec": (gen_tokens / wall_clock_sec) if gen_tokens and wall_clock_sec > 0 else None,
        "draft_tokens": draft_tok,
        "accepted_draft_tokens": accept_tok,
        "draft_acceptance_rate": draft_accept_rate,
        "metrics_before": metrics_before,
        "metrics_after": metrics_after,
        **core,
    }

    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    toks_str = f"{summary['tokens_per_sec']:.1f}" if summary["tokens_per_sec"] else "n/a"
    if draft_accept_rate is not None:
        accept_str = f"{draft_accept_rate:.1%} ({accept_tok:.0f}/{draft_tok:.0f})"
    else:
        accept_str = "n/a (no speculation)"
    L = [
        f"# MTP Comparison — {condition}",
        "",
        f"**Model**: {MODEL_NAME}  ",
        f"**Run status**: {run_status}  ",
        f"**Tasks x attempts**: {core['n_tasks']} x {n_attempts} = {core['n_trials']} trials  ",
        f"**Resolved trials**: {core['n_resolved_trials']}/{core['n_trials']}  "
        f"**mean accuracy**: {core['mean_accuracy']:.1%}  ",
        f"**Tasks solved on >=1 attempt (pass@{n_attempts})**: {core['pass_any_tasks']}/{core['n_tasks']} "
        f"({core['pass_any_rate']:.1%})  ",
        f"**tb-reported accuracy**: {core['tb_reported_accuracy']}  ",
        f"**Wall clock**: {wall_clock_sec:.0f}s ({wall_clock_sec / 60:.1f} min)  ",
        f"**Generated tokens**: {gen_tokens}  **tok/s**: {toks_str}  ",
        f"**Draft acceptance**: {accept_str}  ",
        "",
        f"| Task | resolved/{n_attempts} | rate | pass@{n_attempts} | failure modes |",
        "|---|:--:|:--:|:--:|---|",
    ]
    for r in core["per_task"]:
        L.append(
            f"| {r['task_id']} | {r['n_resolved']}/{r['attempts']} | {r['resolved_rate']:.0%} | "
            f"{'Y' if r['pass_any'] else 'N'} | {', '.join(sorted(set(m for m in r['failure_modes'] if m))) or '-'} |"
        )
    with open(os.path.join(out_dir, "summary.md"), "w") as f:
        f.write("\n".join(L))

    print("CONDITION:", condition)
    print("RUN_STATUS:", run_status)
    print(
        f"MEAN_ACCURACY: {core['mean_accuracy']:.4f}  "
        f"({core['n_resolved_trials']}/{core['n_trials']} trials)"
    )
    print(f"PASS_ANY: {core['pass_any_tasks']}/{core['n_tasks']}")
    print("WALL_CLOCK_SEC:", wall_clock_sec)
    print("TOKENS_PER_SEC:", summary["tokens_per_sec"])
    print("DRAFT_ACCEPTANCE_RATE:", draft_accept_rate)
    print("CONDITION_DONE")


if __name__ == "__main__":
    main()
