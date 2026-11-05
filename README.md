# Antigravity Token 统计仪表盘插件 (UI Sidecar)

一个专为 Google Antigravity 打造的原生 HTML 侧边栏插件，**纯 UI 交互，无需 Skill，无需 MCP**。

实时聚合本地对话数据库与交互日志，直观可视化展现各项目消耗、Prompt 缓存命中率、每日消耗走势与对话明细。

---

## 插件特性

- **纯原生 HTML 侧边栏**：无需大模型参与推理（无 Skill），无需配置工具协议（无 MCP）。
- **极速响应与零外部依赖**：基于 Python 标准库 `http.server`，无需 `pip install` 任何第三方包。
- **现代化深色主题**：遵循 Antigravity 官方规范与 CSS 主题变量，自适应编辑器视觉。
- **动态图表与筛选**：内置纯原生 CSS/SVG 柱状走势图，支持按项目、标题实时搜索与排序。
- **一键导出 CSV**：随时下载结构化明细报表，方便 Excel 二次分析。

---

## 目录结构

```text
token-calculator/
├── plugin.json                     # 插件清单文件
├── assets/
│   └── logo.svg                    # 插件矢量图标 (128x128)
├── sidecars/
│   └── token-dashboard/
│       ├── sidecar.json            # 侧边栏视图声明 (AUX_PANE)
│       ├── server.py               # 轻量 HTTP 服务与数据接口 (5899 端口)
│       └── index.html              # 仪表盘前端界面 (Tailwind + 实时图表)
├── start_dashboard.bat             # 一键启动服务并在浏览器/侧窗打开
├── start_dashboard.ps1             # PowerShell 启动脚本
├── analyze_tokens_by_project.py    # 命令行独立分析脚本
└── run.bat                         # 命令行分析器快捷运行入口
```

---

## 🚀 启动与使用

### 方式 1：一键运行服务并打开仪表盘（最便捷）

在 Windows 资源管理器中**双击** `start_dashboard.bat`，或者在终端执行：

```powershell
.\start_dashboard.bat
```

服务启动后将自动监听 `http://127.0.0.1:5899/`，并自动调用默认浏览器或编辑器内置窗口打开仪表盘。

---

### 方式 2：作为 Antigravity 全局插件安装

如果希望将其注册为 Antigravity 的系统插件：

1. 直接双击运行 `sync.bat`，或者在终端执行：
   ```powershell
   Copy-Item -Path ".\token-calculator" -Destination "$HOME\.gemini\config\plugins\token-calculator" -Recurse -Force
   ```
2. 重启 Antigravity，即可在插件列表和侧边栏（Auxiliary Pane）中识别到 **Token 统计仪表盘**。

---

## 核心接口说明

| 路径 | 方法 | 功能说明 |
| :--- | :--- | :--- |
| `/` 或 `/index.html` | `GET` | 仪表盘可视化 HTML 前端页面 |
| `/api/tokens` | `GET` | 实时解析本地元数据与日志并返回聚合 JSON |
| `/api/export` | `GET` | 导出包含 UTF-8 BOM 的对话消耗 CSV 文件 |
