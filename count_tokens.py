import os
import sys
import glob
import json
from collections import defaultdict
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def count_antigravity_tokens(days=None):
    brain_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
    pattern = os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl")
    files = glob.glob(pattern)

    stats = defaultdict(lambda: {
        "input": 0,
        "output": 0,
        "cache": 0,
        "total": 0,
        "requests": 0
    })

    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"input_tokens"' not in line:
                        continue
                    try:
                        data = json.loads(line)
                        if "input_tokens" in data:
                            created_at = data.get("created_at")
                            if created_at:
                                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone()
                                date_str = dt.strftime("%Y-%m-%d")
                                inp = int(data.get("input_tokens") or 0)
                                outp = int(data.get("output_tokens") or 0)
                                cache = int(data.get("cache_read_tokens") or 0)
                                
                                stats[date_str]["input"] += inp
                                stats[date_str]["output"] += outp
                                stats[date_str]["cache"] += cache
                                stats[date_str]["total"] += (inp + outp + cache)
                                stats[date_str]["requests"] += 1
                    except Exception:
                        pass
        except Exception:
            pass

    sorted_dates = sorted(stats.keys())
    if days and len(sorted_dates) > days:
        sorted_dates = sorted_dates[-days:]

    header = f"{'日期 (本地)':<12} | {'输入 (Input)':>14} | {'输出 (Output)':>12} | {'缓存读取 (Cache)':>16} | {'总消耗 (Total)':>16} | {'请求次数':>8}"
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)

    total_all = {"input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0}

    for d in sorted_dates:
        s = stats[d]
        for k in total_all:
            total_all[k] += s[k]
        print(f"{d:<12} | {s['input']:>14,d} | {s['output']:>12,d} | {s['cache']:>16,d} | {s['total']:>16,d} | {s['requests']:>8,d}")

    print(sep)
    print(f"{'合计':<12} | {total_all['input']:>14,d} | {total_all['output']:>12,d} | {total_all['cache']:>16,d} | {total_all['total']:>16,d} | {total_all['requests']:>8,d}")
    print(sep)

if __name__ == "__main__":
    count_antigravity_tokens()
