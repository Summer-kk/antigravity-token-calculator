import os
import re
import sys
import glob
import json
import sqlite3
import tempfile
import shutil
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime

CACHE_FILE = os.path.expanduser(r"~/.gemini/token_tracker_cache.json")

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"files": {}}

def save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass

# ----------------- 1. Antigravity 数据采集 -----------------

def load_agy_metadata():
    db_path = os.path.expanduser(r"~/.gemini/antigravity/conversation_summaries.db")
    conv_info = {}
    if os.path.exists(db_path):
        conn = None
        temp_db = None
        try:
            try:
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                cur = conn.cursor()
                cur.execute("SELECT 1")
            except Exception:
                t_dir = tempfile.gettempdir()
                temp_db = os.path.join(t_dir, f"conv_meta_{os.getpid()}.db")
                shutil.copy2(db_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cur = conn.cursor()

            cur.execute("SELECT conversation_id, title, preview, workspace_uris, project_id, last_modified_time FROM conversation_summaries")
            for row in cur.fetchall():
                cid, title, preview, workspace_uris, project_id, last_mod = row
                project_name = "未绑定项目"
                project_path = ""
                if workspace_uris:
                    try:
                        uris = json.loads(workspace_uris)
                        if uris and isinstance(uris, list) and len(uris) > 0:
                            decoded = urllib.parse.unquote(uris[0])
                            if decoded.startswith("file://"):
                                parsed_path = urllib.parse.urlparse(decoded).path
                                project_path = urllib.request.url2pathname(parsed_path)
                            else:
                                project_path = decoded.replace("/", os.sep)
                            project_name = os.path.basename(project_path.rstrip(r"\/")) or project_path
                    except Exception:
                        pass
                
                display_title = title.strip()
                if not display_title and preview:
                    display_title = preview.strip().split("\n")[0][:45]
                if not display_title:
                    display_title = "未命名对话"

                conv_info[cid] = {
                    "title": display_title,
                    "project_name": project_name,
                    "project_path": project_path,
                    "project_id": project_id,
                    "last_modified": last_mod
                }
        except Exception:
            pass
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
            if temp_db and os.path.exists(temp_db):
                try: os.remove(temp_db)
                except Exception: pass
    return conv_info

def collect_agy_conversations(cache):
    conv_info = load_agy_metadata()
    brain_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
    pattern = os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl")
    files = glob.glob(pattern)

    conversations = []
    for fpath in files:
        cid = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(fpath))))
        c_meta = conv_info.get(cid, {
            "title": "未命名对话", "project_name": "未绑定项目", "project_path": "", "last_modified": 0
        })

        try:
            mtime = os.path.getmtime(fpath)
            fsize = os.path.getsize(fpath)
        except OSError:
            continue

        c_key = f"agy_{fpath}"
        if c_key in cache["files"] and cache["files"][c_key].get("mtime") == mtime and cache["files"][c_key].get("size") == fsize:
            cached_st = cache["files"][c_key]["data"]
            # 允许更新动态标题
            if c_meta["title"] != "未命名对话":
                cached_st["title"] = c_meta["title"]
                cached_st["project_name"] = c_meta["project_name"]
            conversations.append(cached_st)
            continue

        st = {
            "cid": cid,
            "platform": "Antigravity",
            "title": c_meta["title"],
            "project_name": c_meta["project_name"],
            "project_path": c_meta["project_path"],
            "input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0,
            "last_time": "",
            "daily": {}
        }
        latest_dt = None

        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"input_tokens"' not in line:
                        if st["title"] == "未命名对话" and '"type":"USER_INPUT"' in line:
                            try:
                                u_data = json.loads(line)
                                u_content = u_data.get("content", "").replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
                                if u_content:
                                    st["title"] = u_content.split("\n")[0][:45]
                            except Exception:
                                pass
                        continue
                    try:
                        data = json.loads(line)
                        if "input_tokens" in data:
                            created_at = data.get("created_at")
                            if created_at:
                                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone()
                                date_str = dt.strftime("%Y-%m-%d")
                                if not latest_dt or dt > latest_dt:
                                    latest_dt = dt
                            else:
                                date_str = "未知"

                            inp = int(data.get("input_tokens") or 0)
                            outp = int(data.get("output_tokens") or 0)
                            cache_r = int(data.get("cache_read_tokens") or 0)
                            tot = inp + outp + cache_r

                            st["input"] += inp
                            st["output"] += outp
                            st["cache"] += cache_r
                            st["total"] += tot
                            st["requests"] += 1

                            if date_str not in st["daily"]:
                                st["daily"][date_str] = {"input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0}
                            st["daily"][date_str]["input"] += inp
                            st["daily"][date_str]["output"] += outp
                            st["daily"][date_str]["cache"] += cache_r
                            st["daily"][date_str]["total"] += tot
                            st["daily"][date_str]["requests"] += 1
                    except Exception:
                        pass
        except Exception:
            pass

        if st["requests"] > 0:
            st["last_time"] = latest_dt.strftime("%Y-%m-%d %H:%M") if latest_dt else ""
            cache["files"][c_key] = {"mtime": mtime, "size": fsize, "data": st}
            conversations.append(st)

    return conversations

# ----------------- 2. Codex 数据采集 -----------------

def load_codex_titles():
    index_path = os.path.expanduser(r"~/.codex/session_index.jsonl")
    titles = {}
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        d = json.loads(line)
                        sid = d.get("id")
                        tname = d.get("thread_name")
                        if sid and tname:
                            titles[sid] = tname
                    except Exception:
                        pass
        except Exception:
            pass
    return titles

def resolve_codex_project_name(project_path, raw_name):
    if not project_path and not raw_name:
        return "未绑定项目"
    if not raw_name and project_path:
        raw_name = os.path.basename(project_path.rstrip(r"\/")) or project_path

    # 如果是 ChatGPT 项目 (路径包含 .chatgpt-projects 或 名称形如 g-p-xxx)
    if "chatgpt-projects" in (project_path or "") or (raw_name and raw_name.startswith("g-p-")):
        # 尝试从 AGENTS.md 读取真实项目名称
        if project_path:
            agents_md = os.path.join(project_path, "AGENTS.md")
            if os.path.exists(agents_md):
                try:
                    with open(agents_md, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if "mirror of the ChatGPT project" in line:
                                m = re.search(r'mirror of the ChatGPT project [“\"]([^”\"]+)[”\"]', line)
                                if m:
                                    return f"{m.group(1)} (ChatGPT)"
                except Exception:
                    pass
        return f"ChatGPT 项目 ({raw_name[:12]})"
    return raw_name

def collect_codex_conversations(cache):
    codex_dir = os.path.expanduser("~/.codex")
    if not os.path.exists(codex_dir):
        return []

    titles = load_codex_titles()
    sessions_pattern = os.path.join(codex_dir, "sessions", "*", "*", "*", "*.jsonl")
    files = glob.glob(sessions_pattern)

    conversations = []
    for fpath in files:
        try:
            mtime = os.path.getmtime(fpath)
            fsize = os.path.getsize(fpath)
        except OSError:
            continue

        c_key = f"codex_{fpath}"
        if c_key in cache["files"] and cache["files"][c_key].get("mtime") == mtime and cache["files"][c_key].get("size") == fsize:
            conversations.append(cache["files"][c_key]["data"])
            continue

        file_stem = os.path.basename(fpath).replace(".jsonl", "")
        # 从文件名提取 UUID 会话 ID (形如 rollout-YYYY-MM-DDTHH-mm-ss-UUID_...)
        cid = file_stem
        uuid_match = re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", file_stem)
        if uuid_match:
            cid = uuid_match.group(0)

        st = {
            "cid": cid,
            "platform": "Codex",
            "title": titles.get(cid, ""),
            "project_name": "未绑定项目",
            "project_path": "",
            "input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0,
            "last_time": "",
            "daily": {}
        }
        latest_dt = None

        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"session_meta"' in line:
                        try:
                            d = json.loads(line)
                            if d.get("type") == "session_meta":
                                p = d.get("payload", {})
                                p_cwd = p.get("cwd") or ""
                                if p_cwd:
                                    st["project_path"] = p_cwd.replace("/", os.sep)
                                    raw_pname = os.path.basename(st["project_path"].rstrip(r"\/")) or st["project_path"]
                                    st["project_name"] = resolve_codex_project_name(st["project_path"], raw_pname)
                                sid = p.get("session_id") or p.get("parent_thread_id") or p.get("id")
                                if sid and sid in titles and not st["title"]:
                                    st["title"] = titles[sid]
                        except Exception:
                            pass
                    elif '"token_usage_record"' in line:
                        try:
                            d = json.loads(line)
                            if d.get("type") == "token_usage_record":
                                p = d.get("payload", {})
                                u = p.get("turn_token_usage") or p.get("usage", {})
                                inp = int(u.get("input_tokens") or 0)
                                outp = int(u.get("output_tokens") or 0)
                                cache_r = int(u.get("cached_input_tokens") or 0)
                                tot = int(u.get("total_tokens") or (inp + outp))

                                ts = d.get("timestamp")
                                if ts:
                                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
                                    date_str = dt.strftime("%Y-%m-%d")
                                    if not latest_dt or dt > latest_dt:
                                        latest_dt = dt
                                else:
                                    date_str = "未知"

                                st["input"] += inp
                                st["output"] += outp
                                st["cache"] += cache_r
                                st["total"] += tot
                                st["requests"] += 1

                                if date_str not in st["daily"]:
                                    st["daily"][date_str] = {"input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0}
                                st["daily"][date_str]["input"] += inp
                                st["daily"][date_str]["output"] += outp
                                st["daily"][date_str]["cache"] += cache_r
                                st["daily"][date_str]["total"] += tot
                                st["daily"][date_str]["requests"] += 1
                        except Exception:
                            pass
        except Exception:
            pass

        if st["requests"] > 0:
            if not st["title"]:
                st["title"] = f"Codex 对话 ({st['project_name']})"
            st["last_time"] = latest_dt.strftime("%Y-%m-%d %H:%M") if latest_dt else ""
            cache["files"][c_key] = {"mtime": mtime, "size": fsize, "data": st}
            conversations.append(st)

    return conversations

# ----------------- 3. 双端统一聚合引擎 -----------------

def get_unified_token_data():
    cache = load_cache()
    
    agy_convs = collect_agy_conversations(cache)
    codex_convs = collect_codex_conversations(cache)

    all_convs = agy_convs + codex_convs
    codex_titles = load_codex_titles()

    for c in all_convs:
        if c.get("platform") == "Codex":
            c["project_name"] = resolve_codex_project_name(c.get("project_path", ""), c.get("project_name", ""))
            if c.get("cid") in codex_titles and (not c.get("title") or c.get("title", "").startswith("Codex 对话")):
                c["title"] = codex_titles[c["cid"]]
            elif not c.get("title"):
                c["title"] = f"Codex 对话 ({c['project_name']})"

    save_cache(cache)

    # 聚合项目统计 (支持跨平台同名项目自动归并)
    project_map = defaultdict(lambda: {
        "project_name": "", "project_path": "", "conversations_count": 0,
        "input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0,
        "agy_tokens": 0, "codex_tokens": 0
    })

    # 每日统计
    daily_map = defaultdict(lambda: {
        "input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0,
        "agy_total": 0, "codex_total": 0
    })

    summary = {
        "total_tokens": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "total_requests": 0,
        "total_conversations": len(all_convs),
        "agy_tokens": 0,
        "codex_tokens": 0,
        "agy_conversations": len(agy_convs),
        "codex_conversations": len(codex_convs),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    for c in all_convs:
        p_name = c["project_name"]
        p = project_map[p_name]
        p["project_name"] = p_name
        if not p["project_path"] and c["project_path"]:
            p["project_path"] = c["project_path"]
        p["conversations_count"] += 1
        p["input"] += c["input"]
        p["output"] += c["output"]
        p["cache"] += c["cache"]
        p["total"] += c["total"]
        p["requests"] += c["requests"]

        if c["platform"] == "Antigravity":
            p["agy_tokens"] += c["total"]
            summary["agy_tokens"] += c["total"]
        else:
            p["codex_tokens"] += c["total"]
            summary["codex_tokens"] += c["total"]

        summary["total_tokens"] += c["total"]
        summary["input_tokens"] += c["input"]
        summary["output_tokens"] += c["output"]
        summary["cache_tokens"] += c["cache"]
        summary["total_requests"] += c["requests"]

        for d_str, d_val in c["daily"].items():
            if d_str == "未知": continue
            dm = daily_map[d_str]
            dm["input"] += d_val["input"]
            dm["output"] += d_val["output"]
            dm["cache"] += d_val["cache"]
            dm["total"] += d_val["total"]
            dm["requests"] += d_val["requests"]
            if c["platform"] == "Antigravity":
                dm["agy_total"] += d_val["total"]
            else:
                dm["codex_total"] += d_val["total"]

    grand_total = summary["total_tokens"] or 1
    summary["cache_ratio"] = round((summary["cache_tokens"] / grand_total) * 100, 1)
    summary["agy_ratio"] = round((summary["agy_tokens"] / grand_total) * 100, 1)
    summary["codex_ratio"] = round((summary["codex_tokens"] / grand_total) * 100, 1)

    sorted_projects = sorted(project_map.values(), key=lambda x: x["total"], reverse=True)
    for p in sorted_projects:
        p["pct"] = round((p["total"] / grand_total) * 100, 1)

    sorted_dates = sorted(daily_map.keys())
    daily_list = []
    for d in sorted_dates:
        item = daily_map[d]
        item["date"] = d
        daily_list.append(item)

    sorted_convs = sorted(all_convs, key=lambda x: x["total"], reverse=True)

    return {
        "summary": summary,
        "projects": sorted_projects,
        "daily": daily_list,
        "conversations": sorted_convs
    }

if __name__ == "__main__":
    data = get_unified_token_data()
    s = data["summary"]
    print("=" * 60)
    print(f"📊 统一双端统计数据概览:")
    print(f" - 总消耗 Token: {s['total_tokens']:,} (100%)")
    print(f"   ├─ Antigravity: {s['agy_tokens']:,} ({s['agy_ratio']}%) | {s['agy_conversations']} 对话")
    print(f"   └─ Codex:       {s['codex_tokens']:,} ({s['codex_ratio']}%) | {s['codex_conversations']} 对话")
    print(f" - 缓存读取 Token: {s['cache_tokens']:,} (命中率 {s['cache_ratio']}%)")
    print(f" - 总归并项目数:   {len(data['projects'])} 个")
    print(f" - 总历史对话数:   {len(data['conversations'])} 个")
    print("=" * 60)
