import os
import glob
import json
from collections import defaultdict
from datetime import datetime

brain_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
files = glob.glob(os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl"))

print(f"Total transcript.jsonl files found: {len(files)}")

daily_stats = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "total_tokens": 0, "steps": 0})
total_parsed_steps = 0

for fpath in files:
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    # check if it has token information
                    if "input_tokens" in data or "output_tokens" in data:
                        created_at = data.get("created_at")
                        if created_at:
                            # format like "2026-11-04T06:45:08Z"
                            # parse to local date or UTC date
                            # Let's convert to local date
                            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                            local_dt = dt.astimezone() # convert to local timezone
                            date_str = local_dt.strftime("%Y-%m-%d")
                            
                            inp = data.get("input_tokens", 0) or 0
                            outp = data.get("output_tokens", 0) or 0
                            cache = data.get("cache_read_tokens", 0) or 0
                            total = inp + outp + cache
                            
                            daily_stats[date_str]["input_tokens"] += inp
                            daily_stats[date_str]["output_tokens"] += outp
                            daily_stats[date_str]["cache_read_tokens"] += cache
                            daily_stats[date_str]["total_tokens"] += total
                            daily_stats[date_str]["steps"] += 1
                            total_parsed_steps += 1
                except Exception:
                    pass
    except Exception as e:
        print(f"Error reading {fpath}: {e}")

print(f"Total parsed token steps: {total_parsed_steps}")
print("\n--- Daily Stats (Local Time) ---")
for date_key in sorted(daily_stats.keys()):
    st = daily_stats[date_key]
    print(f"{date_key}: input={st['input_tokens']:,}, output={st['output_tokens']:,}, cache={st['cache_read_tokens']:,}, total={st['total_tokens']:,} (requests={st['steps']})")
