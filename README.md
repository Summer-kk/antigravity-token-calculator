# Antigravity Token 统计仪表盘插件 (`token-calculator`)

[![Antigravity](https://img.shields.io/badge/Antigravity-2.0-blue?logo=google)](https://antigravity.google)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero-success)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个专为 **Google Antigravity** 打造的原生 HTML 侧边栏仪表盘插件（UI Sidecar）。

无需大模型推理（无 Skill），无需配置工具协议（无 MCP），**纯本地原生可视化展示双端（Antigravity + Codex）所有项目与对话的 Token 消耗分布**。

---

## ✨ 核心特性

- ⚡ **双端统一统计**：跨平台聚合 Antigravity 与 Codex 本地全量对话元数据与交互日志。
- 📅 **53 周自适应热力图**：完整排布 1 月至 12 月全年 53 周活动大盘，横纵坐标智能居中贴合，**物理无横向/纵向滑动条**。
- ⚖️ **双端消耗比例条**：动态直观对比 Antigravity 与 Codex 的消耗占比与会话数。
- 📁 **项目消耗排行**：智能归类统计各工程项目占比，支持点击卡片与明细实时联动下钻。
- 💬 **会话明细清单**：支持按平台、时间周期（全部/今天/7天/14天/30天）、项目及点击日期多重交叉过滤，内置毫秒级即时搜索。
- 📊 **一键导出 CSV**：随时导出包含 UTF-8 BOM 的完整结构化账单报表，方便 Excel / 飞书表格二次分析。
- 🔒 **100% 纯本地隐私安全**：完全基于 Python 标准库解析本地 SQLite 与 JSONL 日志，**零网络请求、零外部依赖（无需 `pip install`）、零隐私泄漏风险**。

---

## 📦 安装指南

### 方式 1：Git Clone 安装（推荐）

打开终端，直接将本项目克隆到 Antigravity 全局插件配置目录：

```bash
# Windows PowerShell
git clone https://github.com/Summer-kk/token-calculator.git "$HOME\.gemini\config\plugins\token-calculator"

# macOS / Linux
git clone https://github.com/Summer-kk/token-calculator.git ~/.gemini/config/plugins/token-calculator
```

克隆完成后重启 Antigravity，即可在插件管理器中识别并自动激活。

---

### 方式 2：手动下载 Release

1. 在 GitHub Releases 页面下载最新的 `token-calculator.zip`；
2. 解压并将文件夹重命名为 `token-calculator`；
3. 将该文件夹放置到您的用户配置目录下：
   - Windows: `%USERPROFILE%\.gemini\config\plugins\token-calculator`
   - macOS / Linux: `~/.gemini/config/plugins/token-calculator`
4. 重启 Antigravity。

---

## 🚀 使用方法

### 1. 在 Antigravity 原生界面中使用

插件激活后，支持以下方式随时呼出仪表盘：
- **原生侧窗快捷链接**：在任意对话中点击或发送 `sidecar://token-calculator/token-dashboard/`；
- **侧边栏挂载**：在 Antigravity 2.0 辅助侧窗（Auxiliary Pane）的视图列表中选择 **Token 统计**。

### 2. 独立浏览器预览（可选）

如需脱离 Antigravity 独立在浏览器中查看：
- **Windows**：双击运行根目录下的 `start_dashboard.bat` 或在 PowerShell 中执行 `.\start_dashboard.ps1`；
- **命令行启动**：
  ```bash
  python sidecars/token-dashboard/server.py
  ```
启动后在浏览器中访问：`http://127.0.0.1:5899/`。

---

## 📁 目录结构

```text
token-calculator/
├── .gitignore                      # Git 忽略配置 (忽略缓存、本地生成物等)
├── LICENSE                         # MIT 开源许可证
├── README.md                       # 项目说明文档
├── plugin.json                     # Antigravity 插件清单配置
├── collector.py                    # 跨端 Token 统计与元数据解析聚合引擎 (标准库实现)
├── start_dashboard.bat             # Windows 独立服务快速启动入口 (可选)
├── start_dashboard.ps1             # PowerShell 快速启动入口 (可选)
├── assets/
│   └── logo.svg                    # 插件矢量图标 (128x128)
├── rules/
│   └── AGENTS.md                   # 智能体工作规则 (定义侧窗呼出规范)
└── sidecars/
    └── token-dashboard/
        ├── sidecar.json            # Antigravity Sidecar 挂载配置 (AUX_PANE 入口)
        ├── server.py               # 轻量内置 HTTP API 服务 (端口与动态路由)
        └── index.html              # 纯响应式可视化大盘前端 (Tailwind CSS)
```

---

## 🛠️ 数据接口说明

`server.py` 内置轻量 API 服务：

| 接口路由 | 请求方式 | 功能描述 |
| :--- | :--- | :--- |
| `/` 或 `/index.html` | `GET` | 侧边栏仪表盘响应式 HTML 页面 |
| `/api/tokens` | `GET` | 实时解析本地元数据并返回双端聚合 JSON 数据 |
| `/api/export` | `GET` | 导出包含 UTF-8 BOM 的对话消耗明细 CSV |
| `/api/restart` | `GET` | 清除本地扫描缓存并触发强制全量重扫 |

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。
