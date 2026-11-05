import os
import re
import sys
import json
import shutil
from collector import get_unified_token_data

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def build_html(data):
    json_str = json.dumps(data, ensure_ascii=False)
    template_path = os.path.join(os.path.dirname(__file__), "sidecars", "token-dashboard", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 将双端全量数据直接注入到 window.INITIAL_TOKEN_DATA 中，支持初始占位符或已填充旧数据的持续热更新
    # 使用 lambda 避免 Python re.sub 将 replacement 中的反斜杠（如 Windows 路径 C:\Users）转义成转义序列
    pattern = r'window\.INITIAL_TOKEN_DATA\s*=\s*[\s\S]*?;\s*</script>'
    new_html, count = re.subn(pattern, lambda m: f'window.INITIAL_TOKEN_DATA = {json_str};\n  </script>', html, count=1)
    if count == 0:
        new_html = html.replace("/* DATA_PLACEHOLDER */ null", json_str)
    return new_html

def main():
    print("正在聚合 Antigravity + Codex 全量 Token 统计...")
    data = get_unified_token_data()
    rendered = build_html(data)

    base_dir = os.path.dirname(__file__)

    # 1. 写入本地工程的 token_dashboard.html
    local_out = os.path.join(base_dir, "token_dashboard.html")
    with open(local_out, "w", encoding="utf-8") as f:
        f.write(rendered)
    print(f"✅ 已生成本地统一仪表盘: {local_out}")

    # 2. 写入 sidecars/token-dashboard/index.html (保证 Sidecar 视图开箱自带完整数据)
    sidecar_html = os.path.join(base_dir, "sidecars", "token-dashboard", "index.html")
    with open(sidecar_html, "w", encoding="utf-8") as f:
        f.write(rendered)
    print(f"✅ 已同步至 Sidecar 原生视图: {sidecar_html}")

    # 3. 写入指定会话 Artifact 目录 (若提供会话 ID 参数)
    conv_id = sys.argv[1] if len(sys.argv) > 1 else None
    if conv_id:
        art_dir = os.path.expanduser(rf"~/.gemini/antigravity/brain/{conv_id}")
        if os.path.exists(art_dir):
            try:
                art_out = os.path.join(art_dir, "token_dashboard.html")
                with open(art_out, "w", encoding="utf-8") as f:
                    f.write(rendered)
                print(f"✅ 已同步至当前会话侧窗视图: {art_out}")
            except Exception:
                pass

    # 4. 同步至全局插件目录
    global_plugin_dir = os.path.expanduser(r"~/.gemini/config/plugins/token-calculator")
    if os.path.exists(global_plugin_dir):
        try:
            g_sidecar_html = os.path.join(global_plugin_dir, "sidecars", "token-dashboard", "index.html")
            if os.path.exists(os.path.dirname(g_sidecar_html)):
                shutil.copy2(sidecar_html, g_sidecar_html)
                print(f"✅ 已同步至全局插件 Sidecar 视图: {g_sidecar_html}")
            g_token_dash = os.path.join(global_plugin_dir, "token_dashboard.html")
            shutil.copy2(local_out, g_token_dash)
        except Exception:
            pass

if __name__ == "__main__":
    main()
