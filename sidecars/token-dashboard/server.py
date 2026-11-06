import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# 引入统一数据采集引擎
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from collector import get_unified_token_data

PORT = int(os.environ.get("ANTIGRAVITY_SIDECAR_WEB_PORT") or 5899)

class DashboardHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            html_path = os.path.join(os.path.dirname(__file__), "index.html")
            if os.path.exists(html_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(html_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"index.html not found")
        elif path == "/api/tokens":
            data = get_unified_token_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        elif path == "/api/export":
            data = get_unified_token_data()
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["所属平台", "Conversation ID", "所属项目", "项目路径", "对话标题", "最后活跃时间", "输入Tokens", "输出Tokens", "缓存读取Tokens", "总Tokens", "请求次数"])
            for c in data["conversations"]:
                writer.writerow([c.get("platform", "Antigravity"), c["cid"], c["project_name"], c["project_path"], c["title"], c["last_time"], c["input"], c["output"], c["cache"], c["total"], c["requests"]])
            
            content = "\ufeff" + output.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="antigravity_codex_tokens.csv"')
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        elif path == "/api/export_save":
            try:
                data = get_unified_token_data()
                import csv
                import io
                from datetime import datetime
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["所属平台", "Conversation ID", "所属项目", "项目路径", "对话标题", "最后活跃时间", "输入Tokens", "输出Tokens", "缓存读取Tokens", "总Tokens", "请求次数"])
                for c in data["conversations"]:
                    writer.writerow([c.get("platform", "Antigravity"), c["cid"], c["project_name"], c["project_path"], c["title"], c["last_time"], c["input"], c["output"], c["cache"], c["total"], c["requests"]])
                
                downloads_dir = os.path.expanduser("~/Downloads")
                if not os.path.exists(downloads_dir):
                    downloads_dir = os.path.expanduser("~")
                
                date_str = datetime.now().strftime("%Y-%m-%d")
                target_filename = f"token_usage_export_{date_str}.csv"
                target_path = os.path.join(downloads_dir, target_filename)
                
                with open(target_path, "w", encoding="utf-8-sig") as f:
                    f.write(output.getvalue())
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "ok",
                    "filename": target_filename,
                    "filepath": target_path
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))
        elif path == "/api/restart":
            # 触发后台重新更新与聚合
            hard = "hard=true" in (parsed.query or "")
            try:
                # 1. 清理本地缓存以保证全量重新发现
                cache_file = os.path.expanduser(r"~/.gemini/token_tracker_cache.json")
                if os.path.exists(cache_file):
                    try:
                        os.remove(cache_file)
                    except Exception:
                        pass

                # 2. 重新触发全量数据重新扫描
                pass
            except Exception as e:
                print(f"Restart error: {e}", flush=True)

            data = get_unified_token_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "restarted",
                "message": "服务已重新聚合全量数据并重置完毕",
                "summary": data.get("summary", {})
            }, ensure_ascii=False).encode("utf-8"))

            if hard:
                import threading
                threading.Timer(0.5, lambda: os._exit(0)).start()
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=PORT):
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        except Exception:
            pass
    HTTPServer.allow_reuse_address = True
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print("======================================================", flush=True)
    print(" Antigravity + Codex Token Service Started!", flush=True)
    print(f" Local URL: http://127.0.0.1:{port}/ (ENV PORT: {os.environ.get('ANTIGRAVITY_SIDECAR_WEB_PORT')})", flush=True)
    print("======================================================", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nService stopped.", flush=True)
        server.server_close()

if __name__ == "__main__":
    run_server()
