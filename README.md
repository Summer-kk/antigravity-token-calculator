# Antigravity Token Calculator (Token 消耗统计插件)

<p align="center">
  <img src="assets/logo.svg" alt="Token Calculator Logo" width="100" height="100" />
</p>

<p align="center">
  <b>Google Antigravity 2.0 原生可视化侧边栏仪表盘 · 双端 Token 消耗分析与项目账单</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Antigravity-2.0+-blue?style=flat-square" alt="Antigravity 2.0+">
  <img src="https://img.shields.io/badge/Dependencies-0%20(Pure%20Stdlib)-emerald?style=flat-square" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Platform-Windows%20(10%2F11)-sky?style=flat-square" alt="Windows Platform">
  <img src="https://img.shields.io/badge/Python-3.8+%20(py)-purple?style=flat-square" alt="Python py launcher">
  <img src="https://img.shields.io/badge/License-MIT-amber?style=flat-square" alt="License">
</p>

<p align="center">
  <img src="assets/preview.png" alt="Antigravity Token Calculator Preview" width="480" />
</p>

---

## 🌟 为什么需要本插件？

在使用 Google Antigravity 与 Codex 进行日常多项目编程时，**Tokens 的实际消耗分布**（各项目占比、高频活跃日、缓存命中收益等）往往分散在各端本地的日志与数据库深处，缺乏统一透明的可视化视图。

**Antigravity Token Calculator** 专为解决这一痛点而生：
- 零侵入对话上下文，不消耗任何对话 Token；
- 依托 Antigravity 原生 **UI Sidecar** 体系，在侧边栏提供独立的可视化大盘；
- 纯本地原生解析双端（Antigravity + Codex）日志与元数据，无任何外部网络请求与隐私泄漏风险。

---

## ✨ 核心特性

- ⚡ **双端统一聚合**：自动整合 Antigravity 与 Codex 本地全量对话元数据与用量日志，支持「全部汇总 / Antigravity / Codex」一键无感切换。
- 📅 **53 周自适应热力图**：
  - 完整呈现 1 月至 12 月全年 53 周活动轨迹；
  - 采用 CSS Grid 弹性自适应渲染，**严格居中贴合，物理杜绝横向滚动条**；
  - 智能感知点击日期，一键快速下钻筛选当日全部对话。
- 📊 **四大核心指标与双端配比**：
  - 实时统计全平台总消耗、总请求轮次、缓存读取收益与总会话数；
  - 动态双端消耗比例条，直观对比两大平台 Token 占比与对话分布。
- 📁 **项目消耗排行与双向联动下钻**：
  - 自动汇总各项目工程用量排行与占比进度条；
  - 支持点击项目卡片进行下钻，顶部 Chip 即时显示过滤状态，随时一键清除。
- 💬 **会话明细与毫秒级即时检索**：
  - 支持按时间周期（全部 / 今天 / 7天 / 14天 / 30天）多维过滤；
  - 内置客户端毫秒级实时搜索，标题、项目名称瞬间触达。
- 📥 **双通道 CSV 导出**：
  - 支持一键导出包含 UTF-8 BOM 的完整结构化账单；
  - 后端直接保存至系统「下载」目录（`~/Downloads`），同时前端触发下载与状态提示，双重保障。
- 🔒 **零第三方依赖 (Zero Dependencies)**：
  - 后端仅依赖 Python 原生标准库（`sqlite3`、`json`、`http.server`），**无需 `pip install` 任何额外库**；
  - 前端纯原生 HTML5/Tailwind，轻巧敏捷，秒级加载。

---

## 🚀 一键安装方法 (Windows)

在 PowerShell 中执行以下一行命令，即可将插件克隆至 Antigravity 插件目录，开箱即用：

```powershell
git clone https://github.com/Summer-kk/token-calculator.git "$HOME\.gemini\config\plugins\token-calculator"
```

> **提示**：克隆完成后，在 Antigravity 侧边栏即可直接点击开启。默认直接使用 Windows 官方 Python 启动器 `py`，零外部依赖，无需 `pip install` 任何库。

---

## 💡 使用方式

1. **直接点击原生侧边栏链接**：
   在任何对话中点击：
   `sidecar://token-calculator/token-dashboard/`
   即可立即在侧边辅助窗格打开专属统计大盘。

2. **与 Agent 自然交互**：
   在聊天窗口中直接向 Agent 发送：
   - *“打开 Token 统计侧边栏仪表盘”*
   - *“查看最近各项目 Token 消耗”*
   - *“导出全量 Token 消耗明细为 CSV”*
   
   Agent 将自动引导您打开原生侧边栏。

---

## 📁 项目结构

```text
token-calculator/
├── .gitignore               # 规范的 Git 忽略清单
├── LICENSE                  # MIT 开源许可证
├── README.md                # 项目文档
├── plugin.json              # 插件核心清单
├── assets/
│   ├── logo.svg             # 插件矢量图标
│   ├── preview.html         # 脱敏预览大盘页面
│   └── preview.png          # 大盘预览截图
├── rules/
│   └── AGENTS.md            # Agent 行为规范与侧窗入口指引
└── sidecars/
    └── token-dashboard/
        ├── sidecar.json     # Sidecar 启动与挂载配置
        ├── server.py        # 极简 HTTP 路由服务 (含进程重启与导出)
        ├── collector.py     # 双端 Token 数据统一采集引擎
        └── index.html       # 原生前端可视化仪表盘
```

---

## 🛠️ 数据接口说明

`server.py` 内置轻量 API 服务：

| 接口路由 | 请求方式 | 功能描述 |
| :--- | :--- | :--- |
| `/` 或 `/index.html` | `GET` | 侧边栏仪表盘响应式 HTML 页面 |
| `/api/tokens` | `GET` | 实时解析本地元数据并返回双端聚合 JSON 数据 |
| `/api/export` | `GET` | 下载包含 UTF-8 BOM 的对话消耗明细 CSV |
| `/api/export_save` | `GET` | 直存 CSV 至系统「下载」文件夹并返回绝对路径 |
| `/api/restart` | `GET` | 清除本地扫描缓存并触发强制全量重扫 |

---

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request 共同改进！
如果您觉得这个插件对您有帮助，欢迎点亮右上角的 ⭐️ **Star**！

---

## 📄 开源许可

本项目遵循 [MIT License](LICENSE) 开源协议。
