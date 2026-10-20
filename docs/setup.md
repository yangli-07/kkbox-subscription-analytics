# 第 1 阶段环境与检查说明

## 已记录环境

- 操作系统：macOS Darwin arm64，内核 `25.3.0`
- Python：`3.9.6`
- 已发现：`pandas 2.3.3`、`psql`、`git`
- 未发现：`7z`、`7zz`、`p7zip`
- 项目文件系统可用空间：约 94 GiB
- 原始外层 ZIP：约 8.3 GiB

## 建议的最小环境

阶段 2 需要使用现有 Python，优先以虚拟环境隔离。当前阶段没有安装依赖，也没有解压原始数据。

```text
cd 项目根目录
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

后续需要一个能读取 7z 的工具。安装方式由项目负责人决定；安装后先执行：

```text
7z l data/raw/kkbox-churn-prediction-challenge.zip
```

预期输出：列出外层 ZIP 成员。失败处理：确认命令名是 `7z`、`7zz` 或其他工具，并把实际命令记录到 `docs/progress.md`；不要改动原始 ZIP。

## 本阶段已运行的检查

工作目录为项目根目录。检查包括：`pwd`、`git status --short --branch`、`git log -1 --oneline`、文件清单、外层 ZIP 清单、文件大小、可用空间、系统和工具探测，以及主要 7z 成员的表头和前 3 行流式样本。

## 后续全量审查命令要求

由阶段 2 生成正式脚本，必须分块读取并输出：文件行数、全量日期最小/最大值、字段缺失计数、用户键空值/重复情况、表间用户交集、v1/v2 的覆盖范围。命令必须给出工作目录、预期输出和失败处理；不能将“前 N 行”当作随机样本。
