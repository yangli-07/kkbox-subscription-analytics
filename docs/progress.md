# 项目进度

## 第 1 阶段 数据审查与环境准备

- 输入版本：`data/raw/kkbox-churn-prediction-challenge.zip`，外层文件约 8.3 GiB，内部包含 v1/v2 7z 数据成员。
- 已完成：项目目录与 Git 检查；手册全文阅读；外层 ZIP 清单；主要 CSV 表头与少量流式样本；环境、磁盘和工具记录；初版字段字典、来源条款、setup、忽略规则。
- 已完成补充：确认系统无 `7z`/`7zz`，但 `bsdtar` 可读取 7z；已用临时压缩成员和管道完成 members、transactions、train 的完整扫描。
- 检查证据：`docs/data_inventory.md`、`docs/data_dictionary.md`、`docs/source_and_terms.md`、`docs/setup.md`、`docs/phase1_audit_results.md`。
- 当前限制：大型 `user_logs` v1/v2 的完整扫描、全量用户交集和精确版本重叠尚未完成；不得把这些项目标记为已通过。
- 原始数据：未修改、未解压到项目目录、未加入 Git。
- 下一步：安装或提供可用的 7z 读取工具；阶段 2 以分块方式完成全量审查并冻结 v1/v2 选择和分析范围。
- 版本判断已修正：v2 日志全量扫描仅有 2017-03，不能视为完整历史；暂定保留 v1 历史与 v2 补充月份的独立分支，待 v1 日志和用户重叠完成后再决定组合方式，绝不直接拼接。
- 第 2 阶段开发样本已开始：从完整 `members_v3` 用户总体以固定种子 `20261019` 蓄水池抽样 10,000 名用户；交易 v1/v2 已按用户完成一次流式筛选。v1 日志筛选因本机解压/扫描耗时过长中止，损坏的临时输出已删除，未作为成果使用。
- 已生成：`data/processed/sample_users.csv`、`transactions_sample_v1.csv.gz`、`transactions_sample_v2.csv.gz`。两份交易样本分别保留 26,956 行和 1,848 行，并在脚本中保留来源版本标记。
- 交易分支最小验收已完成：v1 交易用户 2,794、v2 交易用户 1,558、并集 2,870；覆盖率分母为 10,000 名抽样会员。v1/v2 重叠交易用户 1,482。完全重复行与同日多笔交易已分开统计。
- 已生成 Excel 输入：`excel/input/sample_users.csv`、`transactions_sample.csv`、`transactions_sample_v1.csv`、`transactions_sample_v2.csv`、`monthly_reconciliation.csv`；金额标为交易记录金额，不称为净收入或 MRR。
- 已生成：`docs/transaction_min_acceptance.md`、`docs/excel_steps.md`、`data/processed/transaction_min_acceptance.json`。
- 未完成：v1/v2 日志样本、样本日志质量统计、train 标签月份核实、样本内 v1/v2 用户重叠。未完成项不标为通过。
- 用户反馈的官方规则已记录：7A 包含教育/学术研究；7B 限制向非参与者传播/重新发布；8B 有条件允许公开代码但不代表允许公开数据；汇总数据、图表和公开 BI 许可仍未明确。
- 口径初稿：`docs/metric_definitions.md`。`is_cancel` 不等于流失；流失需检查到期后 30 天内有效续订；train 与 train_v2 标签月份分开核实；members_v3 替代旧 members 且不补造 `expiration_date`。

## 个人总结待填写

- 我亲自操作了什么：
- 最重要的三个概念：
- 我能独立解释的代码或公式：
- 发现并修复的错误：

## 第 1 阶段验收

- [x] 已知 members、transactions、train 的真实粒度和字段。
- [x] 已记录这些表的完整日期范围、行数、缺失和明显数值异常。
- [x] 已识别 v1/v2 不同覆盖和更新用途，并给出不拼接的版本建议。
- [ ] user_logs v1 的完整日期/缺失/异常扫描；user_logs v2 已完成（仅 2017-03、18,396,362 行、1,103,894 用户）。
- [ ] 全量用户交集和 v1/v2 精确重叠。
- [ ] Kaggle 许可与公开展示条款由本人登录确认。
- 验收结论：交易分支可推进 Excel；日志分支未完成，行为分析和未核实流失标签不进入 Excel。当前不进入 BI 或 AI。
