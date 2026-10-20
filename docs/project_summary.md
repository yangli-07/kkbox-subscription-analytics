# KKBOX 数据分析项目总结

## 项目目标

本项目使用 KKBOX 竞赛数据，建立一条可复现的订阅交易分析流程：先审查数据和使用限制，再以固定用户样本完成交易核对，随后通过 Excel 和 PostgreSQL 形成可检查的汇总结果，并为 Tableau、Power BI 和 Streamlit 应用准备一致的数据基础。

当前重点是本地学习分析。原始压缩包保留在 `data/raw`，不进入 Git；日志行为分支尚未完成，也不进入当前 Excel 和应用汇总。

数据以样本为基础：从 `members_v3` 用户总体中用固定种子 `20261019` 抽取约 10,000 名用户，再保留这些用户的可用交易记录。样本结果不能直接外推全平台收入、用户规模或留存。

v1 和 v2 始终分开统计。当前交易样本中，v1 覆盖 2015-01 至 2017-02，v2 覆盖 2015-01 至 2017-03；v2 日志已知只覆盖 2017-03，因此不能把 v2 当作完整历史，也不能仅按文件名覆盖 v1。

## 工作流程

### 数据审查与样本准备

项目首先检查了外层压缩包、内部文件、实际字段、日期边界、缺失和明显异常。由于日志文件很大，全量唯一用户排序和精确 v1/v2 用户重叠被延期；这些延期项没有标记为通过。

开发样本使用用户级抽样，而不是随机抽交易行或只取文件前若干行。交易样本按 v1/v2 分开保存，并保留 `source_version`。当前交易分支已完成最小验收；日志行为分支仍未完成。

### Excel

Excel 用于人工核对小型样本，不把大型原始日志放入工作表。主要输入包括：

- `excel/input/sample_users.csv`
- `excel/input/transactions_sample.csv`
- `excel/input/transactions_sample_v1.csv`
- `excel/input/transactions_sample_v2.csv`
- `excel/input/monthly_reconciliation.csv`

建议工作表包括 Users、Transactions、MonthlyReconciliation、Checks 和 Summary。使用 `COUNTIFS` 核对交易行数，使用 `SUMIFS` 核对交易记录金额，并用透视表按月份和 `source_version` 检查交易结构。完全重复记录与同一用户同日多笔交易要分开检查；同日多笔交易不能仅因为用户编号重复就删除。

操作说明见 [excel_steps.md](excel_steps.md)。

### PostgreSQL SQL

SQL 流程分为：

1. `sql/01_create_tables.sql`：创建 `sample_users`、`transactions_v1`、`transactions_v2` 和 `monthly_reconciliation` 表，不设置可能阻止样本导入的主键或唯一约束。
2. `sql/02_transaction_profile.sql`：分别统计 v1/v2 的交易记录、不同用户、自动续费记录、取消标记记录和交易记录金额，并按付款方式和计划天数分组。
3. `sql/03_export_bi_tables.sql`：从 `kkbox_analytics` 导出供 BI 使用的月度、付款计划和版本概览聚合表。

导出的汇总文件位于 `data/processed`：

- `sql_monthly_summary.csv`
- `sql_payment_plan_summary.csv`
- `sql_version_profile.csv`

这些文件只包含汇总数据，不包含用户编号或交易明细。

### Tableau 与 Power BI

手册规划 Tableau 用于留存探索和流失/使用探索，Power BI 用于经营概览和续费运营。当前项目中已存在 Tableau 和 Power BI 文件：`tableau/KKBOX_Monthly_Overview.twbx`、`powerbi/KKBOX_Monthly_Overview.pbix`。人工检查已完成，但项目中没有单独归档的验收记录。后续操作应继续使用已核对的汇总表，保持 v1/v2 分开，并在页面标题或说明中标明样本和观察范围。

### Streamlit

Streamlit 应用入口为 `app/streamlit_app.py`。应用只读取 `data/processed` 下的三个聚合 CSV，提供：

- v1/v2 筛选和月份范围筛选；
- 每月交易笔数、每月去重用户数和交易记录金额趋势图；
- 付款计划汇总；
- 自动续费和取消标记的版本级概览；
- 自然语言问答区域。

目前默认使用基于规则的确定性问答。代码支持可选 OpenAI 接口，但当前未配置密钥、未启用，应用默认不会调用 AI 模型。没有 API 密钥时应用仍可正常显示仪表板并使用确定性回答。应用对真实留存、真实用户流失、净收入、MRR 和用户级行为等问题明确说明数据不支持。独立模拟数据模式计划中，尚未实现；公开演示前仍需单独完成，不公开原始或用户级数据。

## 运行应用

在项目根目录执行：

```bash
cd 项目根目录
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

详细说明见 [app_demo.md](app_demo.md)。

## 主要指标定义与限制

### 交易记录数

按交易表行数统计。相同用户可以有多笔交易；同日多笔交易不自动视为错误。完全重复行进入质量问题检查，不在未核实规则前静默删除。

### 不同用户数

在指定版本和指定月份内，对 `msno` 去重计数。月度不同用户数是各月独立统计值；月度去重用户数之和不等于整个时期的去重用户数。

### 自动续费记录

按 `is_auto_renew` 标记统计记录数及其占交易记录数的比例。这是交易记录层面的结构指标，不等于用户最终续订或持续订阅。

### 取消标记

按 `is_cancel` 标记统计记录数及其比例。取消标记不能直接代表真实用户流失。真实流失需要结合会员到期日，并核查到期后 30 天内是否有有效续订；观察窗口不足时应保留右删失或空值。

### 交易记录金额

按 `actual_amount_paid` 汇总，名称统一为 `transaction_record_amount`。取消记录目前保留，不自动扣除。交易记录金额不等于净收入或 MRR，也不代表会计收入。

### 留存与流失

当前三个汇总 CSV 不包含同期群状态、完整有效订阅区间或用户级到期后续订历史，因此不能据此计算用户级留存或真实用户流失。`train` 和 `train_v2` 的竞赛标签也不能未经月份和观察窗口核实就当作所有月份的业务流失指标。用户级留存、真实流失和日志行为分析属于当前数据不支持的后续范围。

### 版本和样本限制

v1/v2 分开统计，不能直接纵向拼接或因 v2 日期更晚就覆盖历史。所有交易结论都应注明版本、样本规模、月份范围和观察窗口。日志行为分析、全量用户精确重叠和未核实标签月份仍是未完成事项。

## Excel 工作簿状态

排除 `data/raw` 后，项目中实际找到的 Excel 工作簿为：

- `excel/KKBOX_Excel_Analysis.xlsx`

另外发现 `excel/~$KKBOX_Excel_Analysis.xlsx`，这是 Excel 临时锁定文件，不作为交付工作簿记录。没有找到 `.xlsm` 文件。除上述实际搜索结果外，不对 Excel 工作簿作“已生成”或“已丢失”的推断。
