#!/usr/bin/env bash
# LazyFS power-cut test for the Database API. Runs inside the image from ./Dockerfile:
#
#   docker build -t kestrel-lazyfs benchmarks/lazyfs
#   docker run --rm --privileged -v "$PWD:/src:ro" kestrel-lazyfs bash /src/benchmarks/lazyfs/run.sh [RUNS]
#
# LazyFS keeps every byte that was not fsynced in its own cache, so it can throw exactly those
# bytes away, which is what a power cut does. Each run mounts LazyFS, starts the crash_writer
# example on it (one fsynced commit per batch, `ack N` printed after each commit returns) and
# cuts the power in one of three ways, taking turns:
#
#   clear+ckpt  random time, then lazyfs::clear-cache; the writer checkpoints every 64 KiB of log,
#               so cuts also land inside checkpoints
#   clear       the same with checkpoints off
#   torn        lazyfs::torn-op: the Nth write to the log is split in 3 parts, only some parts
#               reach the disk, and LazyFS stops at once (a torn write in the middle of a commit)
#
# Then it opens what really reached the disk and checks that every acknowledged row is there and
# nothing is half there. Before the runs, a control proves that clear-cache does drop unsynced
# data and keeps fsynced data, so a pass cannot come from a file system that writes everything
# through.
set -u
RUNS=${1:-300}
mkdir -p /work && cd /src && tar --exclude=./target --exclude=./.git --exclude=./.claude -cf - . | tar -xf - -C /work
cd /work && cargo build --release --locked --example crash_writer >/dev/null 2>&1 || { echo "BUILD_FAILED"; exit 2; }
W=/work/target/release/examples/crash_writer
CFG=/tmp/lazyfs.toml
cp /opt/lazyfs/lazyfs/config/default.toml "$CFG"
MNT=/tmp/lazyfs.mnt ROOT=/tmp/lazyfs.root FIFO=/tmp/faults.fifo
echo "lazyfs commit: $(cd /opt/lazyfs && git rev-parse HEAD)"

mount_lazyfs() {
  rm -rf "$MNT" "$ROOT"; mkdir -p "$MNT" "$ROOT"
  (cd /opt/lazyfs/lazyfs && exec ./scripts/mount-lazyfs.sh -c "$CFG" -m "$MNT" -r "$ROOT" -f >/tmp/lazyfs.out 2>&1) &
  disown
  for _ in $(seq 1 200); do mountpoint -q "$MNT" && [ -p "$FIFO" ] && return 0; sleep 0.05; done
  echo "LazyFS did not mount"; cat /tmp/lazyfs.out; exit 2
}
unmount_lazyfs() {
  fusermount3 -uz "$MNT" 2>/dev/null || fusermount -uz "$MNT" 2>/dev/null
  sleep 0.2; pkill -KILL -f "build/lazyfs" 2>/dev/null; sleep 0.1
}

# Control: an unsynced file must vanish, an fsynced one must stay.
mount_lazyfs
printf 'not synced\n' > "$MNT/unsynced"
printf 'synced\n' > "$MNT/synced"; sync "$MNT/synced"
echo "lazyfs::clear-cache" > "$FIFO"; sleep 0.3
unmount_lazyfs
unsynced_bytes=$(stat -c %s "$ROOT/unsynced" 2>/dev/null || echo missing)
synced_text=$(cat "$ROOT/synced" 2>/dev/null || echo missing)
echo "CONTROL unsynced_file_bytes_after_cut=$unsynced_bytes synced_file_after_cut=$synced_text"
if [ "$synced_text" != "synced" ] || { [ "$unsynced_bytes" != "0" ] && [ "$unsynced_bytes" != "missing" ]; }; then
  echo "CONTROL_FAILED: LazyFS is not dropping unsynced data, the runs below would prove nothing"; exit 2
fi

pass=0 fail=0 total_acked=0 total_tail=0 snapshots=0 torn_fired=0 torn_tail_runs=0
declare -A mode_pass
for run in $(seq 1 "$RUNS"); do
  mode=$(( run % 3 ))
  mount_lazyfs
  threshold=""; [ "$mode" -eq 0 ] && threshold=65536
  if [ "$mode" -eq 2 ]; then
    persists=(1 2 3 1,2 1,3 2,3)
    persist=${persists[$((RANDOM % 6))]}
    occurrence=$(( RANDOM % 3000 + 2 ))
    echo "lazyfs::torn-op::file=$ROOT/db/events.ksql::persist=$persist::parts=3::occurrence=$occurrence" > "$FIFO"
    name="torn(persist=$persist,occurrence=$occurrence)"
  else
    name=$([ "$mode" -eq 0 ] && echo "clear+ckpt" || echo "clear")
  fi
  "$W" write "$MNT/db" $threshold >/tmp/writer.out 2>/tmp/writer.err &
  wp=$!
  if [ "$mode" -eq 2 ]; then
    # LazyFS stops itself at the torn write; the writer then fails. Give it up to 5 s.
    for _ in $(seq 1 100); do kill -0 "$wp" 2>/dev/null || break; sleep 0.05; done
  else
    sleep "$(awk -v r="$RANDOM" 'BEGIN{printf "%.2f", 0.05 + (r % 150) / 100}')"
  fi
  kill -STOP "$wp" 2>/dev/null
  acked=$(grep -a '^ack ' /tmp/writer.out | tail -1 | cut -d' ' -f2); acked=${acked:-0}
  if [ "$mode" -eq 2 ]; then
    if [ -s /tmp/writer.err ]; then torn_fired=$((torn_fired + 1)); else
      name="$name-not-reached,clear"; echo "lazyfs::clear-cache" > "$FIFO" 2>/dev/null; sleep 0.2; fi
  else
    echo "lazyfs::clear-cache" > "$FIFO"; sleep 0.2
  fi
  kill -KILL "$wp" 2>/dev/null; wait "$wp" 2>/dev/null
  unmount_lazyfs
  result=$("$W" check "$ROOT/db" "$acked" 2>&1); code=$?
  if [ "$code" -eq 0 ]; then pass=$((pass + 1)); mode_pass[$mode]=$(( ${mode_pass[$mode]:-0} + 1 ))
  else fail=$((fail + 1)); echo "run $run FAILED [$name]: $result"; head -3 /tmp/writer.err; fi
  total_acked=$((total_acked + acked))
  tail=$(echo "$result" | sed -n 's/.*"recovered_tail_bytes":\([0-9]*\).*/\1/p'); tail=${tail:-0}
  total_tail=$((total_tail + tail)); [ "$mode" -eq 2 ] && [ "$tail" -gt 0 ] && torn_tail_runs=$((torn_tail_runs + 1))
  case "$result" in *snapshot-*) snapshots=$((snapshots + 1));; esac
  [ $((run % 30)) -eq 0 ] && echo "run $run [$name]: $result"
done
echo "RUNS=$RUNS PASS=$pass FAIL=$fail PASS_BY_MODE clear+ckpt=${mode_pass[0]:-0} clear=${mode_pass[1]:-0} torn=${mode_pass[2]:-0}"
echo "ACKED_ROWS_TOTAL=$total_acked RUNS_ENDING_WITH_A_SNAPSHOT=$snapshots TORN_WRITES_FIRED=$torn_fired TORN_RUNS_WITH_A_CUT_TAIL=$torn_tail_runs TAIL_BYTES_CUT_TOTAL=$total_tail"
[ "$fail" -eq 0 ]
