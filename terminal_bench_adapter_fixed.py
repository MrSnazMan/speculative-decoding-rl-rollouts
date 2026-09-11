"""Fork of gepa.adapters.terminal_bench_adapter.terminal_bench_adapter with two
fixes applied for terminal-bench==0.2.18 (see NOTES.md, Pod F entry):

1. `tb run` in this version takes `--model`, not `--model-name`.
2. `dataset_version="head"` throws a FileNotFoundError during registry
   download (never root-caused); pinned default to the known-good "0.1.1".

Forked instead of patching site-packages in place so a fresh pod/venv
doesn't need manual re-patching.
"""

import json
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from terminal_bench.agents.terminus_1 import CommandBatchResponse

from gepa import EvaluationBatch, GEPAAdapter


class TerminalBenchTask(BaseModel):
    task_id: str
    model_name: str


def _terminate_group(proc: subprocess.Popen, grace_sec: float = 20.0) -> None:
    """SIGTERM then SIGKILL the whole process group of `proc`.

    `tb run` spawns Terminus agent worker threads whose per-task timeout is
    cooperative, not a hard kill: tasks that time out can leave those threads
    looping on litellm retries (`RetryError[Future ... raised RuntimeError]`)
    after tb's event loop tears down, and the non-daemon threadpool then never
    joins, so the process never exits. A plain proc.kill() on the parent is not
    enough -- kill the session/group so every child dies too.
    """
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + grace_sec
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    if proc.poll() is None:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    # Belt-and-suspenders: sweep any tb/agent workers that escaped the group.
    subprocess.run(["pkill", "-9", "-f", "bin/tb run"], check=False)


def run_agent_tb(
    task_ids: str | list[str],
    run_id: str,
    model_name: str,
    instruction_prompt: str,
    dataset_name: str = "terminal-bench-core",
    dataset_version: str = "0.1.1",  # FIX: was "head" (registry download error)
    agent_import_path: str = "train_terminus:TerminusWrapper",
    n_concurrent: int = 6,
    prompt_template_path: str = "prompt-templates/instruction_prompt.txt",
    overall_timeout_sec: float | None = None,
    global_agent_timeout_sec: float | None = None,
    n_attempts: int = 1,
):
    """Run the replay agent for multiple task IDs using tb run command.

    `overall_timeout_sec`, when set, is a hard wall-clock cap: on expiry the
    entire `tb run` process group is force-killed and this returns 124, rather
    than blocking forever on a wedged post-eval retry loop. `get_results()`
    downstream still reads whatever per-task results.json files landed.
    """

    env = os.environ.copy()
    with open(prompt_template_path, "w") as f:
        f.write(instruction_prompt)

    cmd = [
        "tb",
        "run",
        "--dataset-name",
        dataset_name,
        "--dataset-version",
        dataset_version,
        "--agent-import-path",
        agent_import_path,
        "--model",  # FIX: was "--model-name" (not a valid flag in 0.2.18)
        model_name,
        "--run-id",
        run_id,
        "--n-concurrent",
        str(n_concurrent),
        "--output-path",
        str(Path(os.getcwd()) / "runs"),
    ]
    if global_agent_timeout_sec is not None:
        cmd.extend(["--global-agent-timeout-sec", str(global_agent_timeout_sec)])
    if n_attempts and n_attempts != 1:
        cmd.extend(["--n-attempts", str(n_attempts)])
    if isinstance(task_ids, list):
        for task_id in task_ids:
            cmd.extend(["--task-id", task_id])
    else:
        cmd.extend(["--task-id", task_ids])

    print(f"Running command: {' '.join(cmd)}")
    if overall_timeout_sec is not None:
        print(f"Hard wall-clock cap: {overall_timeout_sec:.0f}s")

    # start_new_session=True puts tb run (and its children) in their own process
    # group so _terminate_group can take the whole tree down on timeout / Ctrl-C.
    proc = subprocess.Popen(
        cmd, env=env, cwd=Path(prompt_template_path).parent.parent, start_new_session=True
    )
    try:
        rc = proc.wait(timeout=overall_timeout_sec)
        print(f"Command completed with return code: {rc}")
        return rc
    except subprocess.TimeoutExpired:
        print(f"Error: tb run exceeded {overall_timeout_sec:.0f}s hard cap -- killing process group")
        _terminate_group(proc)
        return 124
    except KeyboardInterrupt:
        print("KeyboardInterrupt -- killing tb run process group")
        _terminate_group(proc)
        raise
    except Exception as e:
        print(f"Error running command: {e}")
        _terminate_group(proc)
        return 1


def get_results(task_id: str, run_id: str) -> tuple[int, list]:
    def _read_episode_response(episode_dir: Path) -> CommandBatchResponse | None:
        response_file = episode_dir / "response.json"
        if response_file.exists():
            try:
                response_content = response_file.read_text()
                return CommandBatchResponse.model_validate_json(response_content)
            except Exception:
                pass
        return None

    def _get_logging_dir(task_id: str, run_id: str):
        logging_dir_base = Path("runs") / run_id / task_id
        for dir in logging_dir_base.iterdir():
            if dir.is_dir() and dir.name.startswith(task_id):
                return dir
        raise ValueError(f"No logging directory found for task {task_id} and run {run_id}")

    logging_dir = _get_logging_dir(task_id, run_id)
    result_json = logging_dir / "results.json"
    with open(result_json) as f:
        result = json.load(f)
    if result.get("parser_results", None):
        score = sum(x == "passed" for x in result["parser_results"].values())
    else:
        score = 0

    if result.get("is_resolved", None):
        success = True
    else:
        success = False

    failed_reason = result.get("failure_mode", "unknown")

    trajectory_path = logging_dir / "agent-logs"
    episode_dirs = []
    for dir in trajectory_path.iterdir():
        if dir.is_dir() and dir.name.startswith("episode-"):
            episode_dirs.append(dir)

    if episode_dirs:
        episode_dirs.sort(key=lambda x: int(x.name.split("-")[1]))
        last_episode_dir = episode_dirs[-1]

    last_episode_dir_trajectory = last_episode_dir / "debug.json"
    with open(last_episode_dir_trajectory) as f:
        trajectory = json.load(f)

        if "input" in trajectory and isinstance(trajectory["input"], list):
            messages = trajectory["input"]

        parsed_response = _read_episode_response(last_episode_dir)

        if parsed_response:
            assistant_message = {
                "role": "assistant",
                "content": parsed_response.model_dump_json(),
            }
            messages.append(assistant_message)

    return success, score, failed_reason, messages


class TerminusAdapter(GEPAAdapter):
    def __init__(
        self,
        n_concurrent: int = 6,
        instruction_prompt_path: str = "prompt-templates/instruction_prompt.txt",
    ):
        self.n_concurrent = n_concurrent
        self.instruction_prompt_path = instruction_prompt_path

    def evaluate(
        self,
        batch: list[TerminalBenchTask],
        candidate: dict[str, str],
        capture_traces: bool = False,
        overall_timeout_sec: float | None = None,
        global_agent_timeout_sec: float | None = None,
        n_attempts: int = 1,
    ) -> EvaluationBatch:
        outputs = []
        scores = []
        trajectories = []
        example_run_id = "temp_gepa_run" + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
        example_model_name = batch[0].model_name

        run_agent_tb(
            [task.task_id for task in batch],
            example_run_id,
            example_model_name,
            instruction_prompt=candidate["instruction_prompt"],
            n_concurrent=self.n_concurrent,
            prompt_template_path=self.instruction_prompt_path,
            overall_timeout_sec=overall_timeout_sec,
            global_agent_timeout_sec=global_agent_timeout_sec,
            n_attempts=n_attempts,
        )

        # With n_attempts > 1, tb writes k trial dirs per task and get_results()
        # (which grabs the first) only sees attempt 1. run_condition.py computes
        # the real summary from runs/<run_id>/results.json instead; the per-task
        # parse below stays best-effort for the single-attempt path.

        for example in batch:
            try:
                success, score, failed_reason, messages = get_results(example.task_id, example_run_id)
            except Exception as e:
                print(f"Error running example {example.task_id} {example_run_id}: {e}")
                success = False
                score = 0
                failed_reason = str(e)
                messages = []

            outputs.append(
                f"Terminal Bench outputs are omitted. Please see runs/{example_run_id}/{example.task_id}/ for detailed logging."
            )
            scores.append(score)
            trajectories.append(
                {
                    "messages": messages,
                    "instruction_prompt": candidate["instruction_prompt"],
                    "failed_reason": failed_reason,
                    "success": success,
                }
            )
        return EvaluationBatch(
            outputs=outputs,
            scores=scores,
            trajectories=trajectories,
        )

    def make_reflective_dataset(
        self,
        candidate: dict[str, str],
        eval_batch: EvaluationBatch,
        components_to_update: list[str],
    ):
        reflective_dataset = {"instruction_prompt": []}
        for _score, trajectory in zip(eval_batch.scores, eval_batch.trajectories, strict=False):
            if trajectory["success"]:
                feedback = "Successfully solved the task!"
            else:
                feedback = f"Failed to solve the task. Reason: {trajectory['failed_reason']}"
            reflective_dataset["instruction_prompt"].append(
                {
                    "Message History": trajectory["messages"],
                    "Instruction Prompt": candidate["instruction_prompt"],
                    "Feedback": feedback,
                }
            )
        return reflective_dataset
