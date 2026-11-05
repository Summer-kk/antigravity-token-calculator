import os
import sys
import glob
import json
import sqlite3
import argparse
import urllib.parse
from collections import defaultdict
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_conversation_metadata():
    db_path = os.path.expanduser(r"~/.gemini/antigravity/conversation_summaries.db")
    conv_info = {}
    if os.path.exists(db_path):
        try:
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
                            decoded = urllib.parse.unquote(uris[0])
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
            conn.close()
        except Exception as e:
            print(f"[警告] 无法读取元数据数据库: {e}")
    return conv_info

def parse_all_transcripts(conv_info):
    brain_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
    pattern = os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl")
    files = glob.glob(pattern)

    conv_stats = {}

    for fpath in files:
        cid = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(fpath))))
        c_meta = conv_info.get(cid, {
            "title": "未命名对话",
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
            "daily": defaultdict(lambda: {"input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0}),
            "first_time": None,
            "last_time": None
        }

        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"input_tokens"' not in line:
                        if st["title"] == "未命名对话":
                            if '"type":"USER_INPUT"' in line:
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
                                if not st["first_time"] or dt < st["first_time"]:
                                    st["first_time"] = dt
                                if not st["last_time"] or dt > st["last_time"]:
                                    st["last_time"] = dt
                            else:
                                date_str = "未知"

                            inp = int(data.get("input_tokens") or 0)
                            outp = int(data.get("output_tokens") or 0)
                            cache = int(data.get("cache_read_tokens") or 0)
                            tot = inp + outp + cache

                            st["input"] += inp
                            st["output"] += outp
                            st["cache"] += cache
                            st["total"] += tot
                            st["requests"] += 1

                            st["daily"][date_str]["input"] += inp
                            st["daily"][date_str]["output"] += outp
                            st["daily"][date_str]["cache"] += cache
                            st["daily"][date_str]["total"] += tot
                            st["daily"][date_str]["requests"] += 1
                    except Exception:
                        pass
        except Exception:
            pass

        if st["requests"] > 0:
            conv_stats[cid] = st

    return conv_stats

def main():
    parser = argparse.ArgumentParser(description="Antigravity 项目与对话 Token 消耗分析工具")
    parser.add_argument("--top-conv", type=int, default=10, help="展示消耗最高的前 N 个对话 (默认 10)")
    parser.add_argument("--project", type=str, default=None, help="仅筛选指定项目名称/关键字")
    parser.add_argument("--daily", nargs="?", const=14, type=int, default=None, help="展示最近 N 天的每日消耗 (默认 14 天)")
    parser.add_argument("--export-csv", type=str, default=None, help="导出对话明细为 CSV 文件路径")
    args = parser.parse_args()

    conv_info = load_conversation_metadata()
    conv_stats = parse_all_transcripts(conv_info)

    # 按项目分组
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
        if args.project and args.project.lower() not in st["project_name"].lower():
            continue
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

    if not project_stats:
        print(f"未找到与 '{args.project}' 匹配的项目。")
        return

    # 打印项目汇总表
    filter_label = f" (筛选项目: {args.project})" if args.project else ""
    print("=" * 110)
    print(f" 📊 各项目 Token 消耗汇总{filter_label} (按总 Token 降序)")
    print("=" * 110)
    header = f"{'项目名称':<22} | {'对话数':>6} | {'输入 (Input)':>14} | {'输出 (Output)':>12} | {'缓存读取 (Cache)':>16} | {'总消耗 (Total)':>16} | {'占比':>6}"
    print(header)
    print("-" * 110)

    grand_total = sum(p["total"] for p in project_stats.values()) or 1
    sorted_projects = sorted(project_stats.values(), key=lambda x: x["total"], reverse=True)

    for p in sorted_projects:
        pct = (p["total"] / grand_total) * 100
        p_name = (p["project_name"][:20] + "..") if len(p["project_name"]) > 22 else p["project_name"]
        print(f"{p_name:<22} | {len(p['conversations']):>6d} | {p['input']:>14,d} | {p['output']:>12,d} | {p['cache']:>16,d} | {p['total']:>16,d} | {pct:>5.1f}%")

    print("-" * 110)
    total_convs = sum(len(p['conversations']) for p in sorted_projects)
    total_inp = sum(p['input'] for p in sorted_projects)
    total_outp = sum(p['output'] for p in sorted_projects)
    total_cache = sum(p['cache'] for p in sorted_projects)
    print(f"{'合计':<22} | {total_convs:>6d} | {total_inp:>14,d} | {total_outp:>12,d} | {total_cache:>16,d} | {grand_total:>16,d} | 100.0%")
    print("=" * 110)

    # 打印对话明细
    all_convs = []
    for p in sorted_projects:
        all_convs.extend(p["conversations"])
    sorted_convs = sorted(all_convs, key=lambda x: x["total"], reverse=True)

    title_label = f"项目 [{args.project}] 下的全部对话" if args.project else f"消耗最高的前 {min(args.top_conv, len(sorted_convs))} 个对话"
    print(f"\n 🔥 {title_label} 明细")
    print("=" * 110)
    conv_hdr = f"{'最后活跃时间':<16} | {'所属项目':<16} | {'对话标题':<26} | {'输出':>10} | {'输入':>12} | {'缓存读取':>14} | {'总 Token':>14}"
    print(conv_hdr)
    print("-" * 110)
    display_convs = sorted_convs if args.project else sorted_convs[:args.top_conv]
    for c in display_convs:
        t_str = c["last_time"].strftime("%Y-%m-%d %H:%M") if c["last_time"] else "未知"
        p_disp = (c["project_name"][:14] + "..") if len(c["project_name"]) > 16 else c["project_name"]
        t_disp = (c["title"][:23] + "..") if len(c["title"]) > 25 else c["title"]
        print(f"{t_str:<16} | {p_disp:<16} | {t_disp:<26} | {c['output']:>10,d} | {c['input']:>12,d} | {c['cache']:>14,d} | {c['total']:>14,d}")
    print("=" * 110)

    # 打印每日消耗走势（如果指定了 --daily）
    if args.daily is not None:
        daily_stats = defaultdict(lambda: {"input": 0, "output": 0, "cache": 0, "total": 0, "requests": 0})
        for c in all_convs:
            for d_str, d_val in c["daily"].items():
                daily_stats[d_str]["input"] += d_val["input"]
                daily_stats[d_str]["output"] += d_val["output"]
                daily_stats[d_str]["cache"] += d_val["cache"]
                daily_stats[d_str]["total"] += d_val["total"]
                daily_stats[d_str]["requests"] += d_val["requests"]
        
        sorted_dates = sorted(daily_stats.keys())
        if args.daily > 0 and len(sorted_dates) > args.daily:
            sorted_dates = sorted_dates[-args.daily:]
            
        print(f"\n 📅 每日消耗汇总 (展示最近 {len(sorted_dates)} 天)")
        print("=" * 110)
        daily_hdr = f"{'日期 (本地)':<16} | {'输入 (Input)':>14} | {'输出 (Output)':>12} | {'缓存读取 (Cache)':>16} | {'总消耗 (Total)':>16} | {'请求次数':>8}"
        print(daily_hdr)
        print("-" * 110)
        for d in sorted_dates:
            s = daily_stats[d]
            print(f"{d:<16} | {s['input']:>14,d} | {s['output']:>12,d} | {s['cache']:>16,d} | {s['total']:>16,d} | {s['requests']:>8,d}")
        print("=" * 110)

    # 导出 CSV
    if args.export_csv:
        import csv
        with open(args.export_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Conversation ID", "项目名称", "项目路径", "对话标题", "最后活跃时间", "输入Tokens", "输出Tokens", "缓存读取Tokens", "总Tokens", "请求次数"])
            for c in sorted_convs:
                t_str = c["last_time"].strftime("%Y-%m-%d %H:%M:%S") if c["last_time"] else ""
                writer.writerow([c["cid"], c["project_name"], c["project_path"], c["title"], t_str, c["input"], c["output"], c["cache"], c["total"], c["requests"]])
        print(f"\n✅ 已将全部对话明细导出至: {args.export_csv}")

if __name__ == "__main__":
    main()
