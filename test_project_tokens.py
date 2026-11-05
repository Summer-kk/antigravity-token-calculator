import os
import glob
import json
import sqlite3
import urllib.parse
from collections import defaultdict
from datetime import datetime

db_path = os.path.expanduser(r"~/.gemini/antigravity/conversation_summaries.db")
conv_info = {}

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT conversation_id, title, preview, workspace_uris, project_id, last_modified_time FROM conversation_summaries")
    for row in cur.fetchall():
        cid, title, preview, workspace_uris, project_id, last_mod = row
        project_name = "未绑定项目 (无Workspace)"
        project_path = ""
        if workspace_uris:
            try:
                uris = json.loads(workspace_uris)
                if uris and isinstance(uris, list) and len(uris) > 0:
                    raw_uri = uris[0]
                    # unquote file:///c%3A/... -> C:/...
                    decoded = urllib.parse.unquote(raw_uri)
                    if decoded.startswith("file:///"):
                        project_path = decoded[8:]
                    elif decoded.startswith("file://"):
                        project_path = decoded[7:]
                    else:
                        project_path = decoded
                    
                    project_path = project_path.replace("/", os.sep)
                    project_name = os.path.basename(project_path.rstrip(r"\/")) or project_path
            except Exception:
                pass
        
        display_title = title.strip()
        if not display_title and preview:
            display_title = preview.strip().split("\n")[0][:40]
        if not display_title:
            display_title = "未命名对话"

        conv_info[cid] = {
            "title": display_title,
            "project_name": project_name,
            "project_path": project_path,
            "project_id": project_id,
            "last_modified": last_mod
        }
    conn.close()

print(f"Loaded {len(conv_info)} conversations from DB.")

# Now parse transcripts
brain_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
pattern = os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl")
files = glob.glob(pattern)

conv_stats = {}

for fpath in files:
    cid = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(fpath))))
    c_meta = conv_info.get(cid, {
        "title": "未知会话",
        "project_name": "未绑定项目 (无Workspace)",
        "project_path": "",
        "project_id": "unknown",
        "last_modified": 0
    })
    
    st = {
        "cid": cid,
        "title": c_meta["title"],
        "project_name": c_meta["project_name"],
        "project_path": c_meta["project_path"],
        "input": 0,
        "output": 0,
        "cache": 0,
        "total": 0,
        "requests": 0,
        "first_time": None,
        "last_time": None
    }
    
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if '"input_tokens"' not in line:
                    if st["title"] == "未命名对话" or st["title"] == "未知会话":
                        # Try to extract first user input
                        if '"type":"USER_INPUT"' in line:
                            try:
                                u_data = json.loads(line)
                                u_content = u_data.get("content", "").replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
                                if u_content:
                                    st["title"] = u_content.split("\n")[0][:40]
                            except Exception:
                                pass
                    continue
                try:
                    data = json.loads(line)
                    if "input_tokens" in data:
                        created_at = data.get("created_at")
                        if created_at:
                            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone()
                            if not st["first_time"] or dt < st["first_time"]:
                                st["first_time"] = dt
                            if not st["last_time"] or dt > st["last_time"]:
                                st["last_time"] = dt
                        inp = int(data.get("input_tokens") or 0)
                        outp = int(data.get("output_tokens") or 0)
                        cache = int(data.get("cache_read_tokens") or 0)
                        st["input"] += inp
                        st["output"] += outp
                        st["cache"] += cache
                        st["total"] += (inp + outp + cache)
                        st["requests"] += 1
                except Exception:
                    pass
    except Exception:
        pass

    if st["requests"] > 0:
        conv_stats[cid] = st

# Group by project
project_stats = defaultdict(lambda: {
    "project_name": "",
    "project_path": "",
    "conversations": [],
    "input": 0,
    "output": 0,
    "cache": 0,
    "total": 0,
    "requests": 0
})

for cid, st in conv_stats.items():
    p_name = st["project_name"]
    p = project_stats[p_name]
    p["project_name"] = p_name
    p["project_path"] = st["project_path"]
    p["conversations"].append(st)
    p["input"] += st["input"]
    p["output"] += st["output"]
    p["cache"] += st["cache"]
    p["total"] += st["total"]
    p["requests"] += st["requests"]

print("\n================== 项目级别消耗统计 (按总 Token 降序) ==================")
sorted_projects = sorted(project_stats.values(), key=lambda x: x["total"], reverse=True)
for p in sorted_projects:
    print(f"\n📂 项目: {p['project_name']} (对话数: {len(p['conversations'])})")
    if p['project_path']:
        print(f"   路径: {p['project_path']}")
    print(f"   输入: {p['input']:,} | 输出: {p['output']:,} | 缓存: {p['cache']:,} | 总计: {p['total']:,} | 请求: {p['requests']:,}")
    
    print("   --- 对话明细 (Top 5 对话) ---")
    sorted_convs = sorted(p["conversations"], key=lambda x: x["total"], reverse=True)
    for c in sorted_convs[:5]:
        time_str = c["last_time"].strftime("%Y-%m-%d %H:%M") if c["last_time"] else "未知"
        title_disp = c["title"][:28]
        print(f"     • [{time_str}] {title_disp:<30} | 总计: {c['total']:>12,d} (出: {c['output']:>8,d}, 进: {c['input']:>10,d}, 缓存: {c['cache']:>12,d})")
