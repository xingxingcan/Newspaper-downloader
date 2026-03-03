# 报纸下载器

面向 Windows 系统的报纸电子版批量下载桌面应用，采用 Python + PyQt6 开发，界面简洁美观，支持多报纸多日期批量下载。

## 功能特性

- **多报纸支持**：人民日报、新华每日电讯、环球时报、光明日报、经济日报（人民日报已完整实现，其余为占位可扩展）
- **日期选择**：日历控件选择日期，支持近一年内的报纸
- **批量下载**：支持多选报纸同时下载
- **进度显示**：实时显示当前下载报纸、进度条、日志输出
- **断点续传**：已下载过的日期会自动跳过
- **配置记忆**：自动记住上次选择的保存目录和报纸
- **取消支持**：可随时取消正在进行的下载

## 运行环境

- **Python**：3.9 及以上
- **操作系统**：Windows 10/11
- **依赖**：PyQt6、requests、PyPDF2

## 安装与运行

### 1. 安装依赖

```bash
cd "Newspaper downloader"
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python main.py
```

或直接双击 `main.py`（若已配置 Python 关联）。

## 项目结构

```
Newspaper downloader/
├── main.py              # 程序入口
├── requirements.txt     # 依赖列表
├── config/              # 配置模块
│   ├── config_manager.py   # 配置读写（保存目录、窗口大小等）
│   └── newspaper_sources.py # 报纸源定义
├── downloader/          # 下载逻辑
│   ├── base.py             # 适配器基类
│   ├── worker.py           # Qt 工作线程（线程安全）
│   ├── task_manager.py     # 任务调度（可选）
│   └── adapters/           # 各报纸适配器
│       ├── people_daily.py  # 人民日报（已实现）
│       └── stub.py          # 占位适配器
└── ui/                 # 界面
    └── main_window.py     # 主窗口
```

## 打包为 Windows 可执行文件

使用 PyInstaller 打包为 `.exe`：

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 打包命令（推荐：目录模式，启动更快）

```bash
pyinstaller --name="报纸下载器" --windowed --noconfirm ^
    --add-data "config;config" ^
    main.py
```

> 注意：`--add-data` 在 Windows 上使用分号 `;` 分隔路径对，格式为 `源路径;目标路径`。若在 Unix 下用 `:`。

### 3. 单文件模式（可选）

```bash
pyinstaller --name="报纸下载器" --windowed -F --noconfirm main.py
```

单文件模式启动较慢（需解压），若遇到 Qt 插件问题可改用目录模式。

### 4. 使用 spec 文件（推荐）

项目提供 `newspaper_downloader.spec`，可自定义打包选项：

```bash
pyinstaller newspaper_downloader.spec
```

### 5. 输出位置

- 目录模式：`dist/报纸下载器/` 文件夹，内含 `报纸下载器.exe` 和依赖
- 单文件：`dist/报纸下载器.exe`

将整个 `dist/报纸下载器` 文件夹复制到目标机器即可运行，无需安装 Python。

## 界面美化参数

在 `ui/main_window.py` 中可调整 `COLORS` 字典：

| 键名 | 说明 | 默认值 |
|------|------|--------|
| `bg_primary` | 主背景色 | `#F5F7FA` |
| `bg_card` | 卡片背景 | `#FFFFFF` |
| `accent` | 主按钮/进度条色 | `#2563EB` |
| `accent_hover` | 按钮悬停色 | `#1D4ED8` |
| `text_primary` | 主文字色 | `#1E293B` |
| `text_secondary` | 次要文字色 | `#64748B` |
| `border` | 边框色 | `#E2E8F0` |
| `success` | 成功色 | `#22C55E` |
| `error` | 错误色 | `#EF4444` |

修改后保存并重新运行即可生效。

## 扩展新报纸

1. 在 `config/newspaper_sources.py` 中添加新报纸条目
2. 在 `downloader/adapters/` 下新建适配器类，继承 `BaseAdapter`，实现 `download()` 方法
3. 在 `downloader/adapters/__init__.py` 的 `ADAPTER_MAP` 中注册新适配器

参考 `people_daily.py` 的实现。

## 注意事项

- 报纸电子版版权归原出版方所有，本工具仅供个人学习与非盈利使用
- 若人民日报官网改版导致无法下载，请关注相关项目更新或自行适配

## 许可

MIT License
