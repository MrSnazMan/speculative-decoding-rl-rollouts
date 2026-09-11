"""Select the 50 shortest-duration tasks from terminal-bench-core==0.1.1.

`Dataset.sort_by_duration()` sorts longest-first (per GEPA's own example,
which reverses the list to get shortest-first). We take the tail of the
sorted list to approximate shortest-50, to keep the 50x2-condition run
within a reasonable time/cost budget rather than including known-long
tasks (e.g. build-linux-kernel-qemu, cartpole-rl-training).

Writes one task-id per line to task_ids.txt (relative to cwd).
"""

from terminal_bench.dataset.dataset import Dataset

ds = Dataset(name="terminal-bench-core", version="0.1.1")
ds.sort_by_duration()
names = [t.name for t in ds._tasks]

n = 50
selected = names[-n:]  # shortest n, since sort_by_duration() is longest-first

with open("task_ids.txt", "w") as f:
    f.write("\n".join(selected))

print("TOTAL_TASKS_IN_DATASET:", len(names))
print("SELECTED:", len(selected))
print("TASK_IDS:", selected)
print("SELECT_TASKS_DONE")
