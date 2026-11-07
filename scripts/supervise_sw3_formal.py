"""External one-shot resource guard. Never retries the formal child."""
import json
import subprocess
import sys
import time
from pathlib import Path
import psutil


def main():
    report=Path(sys.argv[1]).resolve()
    config=json.loads((report/"LAUNCH.json").read_bytes())
    started=time.time()
    reason=None
    samples=report/"RESOURCE_SAMPLES.jsonl"
    with (report/"stdout.log").open("xb") as out,(report/"stderr.log").open("xb") as err:
        child=subprocess.Popen(config["command"],cwd=config["cwd"],stdout=out,stderr=err)
        peak=0
        with samples.open("x",encoding="utf-8") as log:
            while True:
                processes=[]
                try:
                    parent=psutil.Process(child.pid)
                    processes=[parent]+parent.children(recursive=True)
                except psutil.NoSuchProcess:
                    pass
                rows=[]
                for p in processes:
                    try:
                        t=p.cpu_times();m=p.memory_info()
                        rows.append(dict(pid=p.pid,rss=m.rss,cpu=t.user+t.system))
                    except psutil.NoSuchProcess:
                        pass
                total=sum(r["rss"] for r in rows);peak=max(peak,total)
                free=psutil.disk_usage(config["cwd"]).free
                elapsed=time.time()-started
                events=Path(config["output"])/"events"
                log.write(json.dumps(dict(elapsed=elapsed,processes=rows,total_rss=total,
                    disk_free=free,gates=len(list(events.glob("*.json"))) if events.exists() else 0))+"\n")
                log.flush()
                code=child.poll()
                if code is not None:
                    break
                if elapsed>config["wall_limit_seconds"]:reason="WALL_LIMIT"
                elif total>config["tree_rss_limit_bytes"]:reason="MEMORY_LIMIT"
                elif free<config["minimum_disk_free_bytes"]:reason="DISK_LIMIT"
                if reason:
                    for p in reversed(processes):
                        try:p.kill()
                        except psutil.NoSuchProcess:pass
                    child.wait(timeout=30)
                    code=child.returncode
                    break
                time.sleep(2)
    (report/"TIMING.json").write_text(json.dumps(dict(pid=child.pid,exit_code=code,
        stop_reason=reason,wall_seconds=time.time()-started,peak_tree_rss=peak),indent=2))
    return 0 if code==0 and reason is None else 1

if __name__=="__main__":
    raise SystemExit(main())
