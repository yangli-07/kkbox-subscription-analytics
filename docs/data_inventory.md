# KKBOX 数据文件审查

## 审查结论

本阶段只检查项目文件、外层 ZIP 清单、内部 7z 清单，以及各主要 CSV 的表头和少量流式样本；没有把全部日志加载进内存，也没有解压全部数据。

项目输入为 `data/raw/kkbox-churn-prediction-challenge.zip`，文件系统大小约 8.3 GiB。ZIP 内部未发现解压后的 CSV，只有多个 7z 成员和一个 Scala 文件。

| 内部成员 | 压缩后大小 | 观察到的内部 CSV | 当前判断 |
|---|---:|---|---|
| `members_v3.csv.7z` | 231 MiB | `members_v3.csv` | 可作为用户属性表 |
| `transactions.csv.7z` | 675 MiB | `transactions.csv` | 可作为交易事实表 |
| `transactions_v2.csv.7z` | 47 MiB | `data/churn_comp_refresh/transactions_v2.csv` | 独立 v2 版本，不能直接拼接 |
| `user_logs.csv.7z` | 6.7 GiB | `user_logs.csv` | 大型用户行为日志 |
| `user_logs_v2.csv.7z` | 655 MiB | `data/churn_comp_refresh/user_logs_v2.csv` | 独立 v2 版本，不能直接拼接 |
| `train.csv.7z` | 32 MiB | `train.csv` | 竞赛流失标签 |
| `train_v2.csv.7z` | 31 MiB | `data/churn_comp_refresh/train_v2.csv` | 独立 v2 标签版本 |
| `sample_submission_v2.csv.7z` | 29 MiB | 未展开 | 提交模板 |
| `sample_submission_zero.csv.7z` | 31 MiB | 未展开 | 提交模板 |
| `WSDMChurnLabeller.scala` | 7 KiB | Scala 源文件 | 参考文件，不是分析事实表 |

## 流式样本

抽样方式是从 7z 解压流中读取表头和前 3 行；这不是随机样本，也不代表全量统计。

### members_v3.csv

表头：`msno, city, bd, gender, registered_via, registration_init_time`

样本显示 `msno` 为字符串用户键，注册日期以 `YYYYMMDD` 整数形式保存；`gender` 可能为空。

### transactions.csv

表头：`msno, payment_method_id, payment_plan_days, plan_list_price, actual_amount_paid, is_auto_renew, transaction_date, membership_expire_date, is_cancel`

样本显示一行是一个用户交易记录，包含计划天数、标价、实际支付、自动续费、交易日期、会员到期日期和取消标志。

### user_logs.csv

表头：`msno, date, num_25, num_50, num_75, num_985, num_100, num_unq, total_secs`

样本显示一行是一个用户某日的行为汇总，适合按用户和日期分块读取；不能直接当作交易或订阅状态。

### train.csv

表头：`msno, is_churn`

样本显示一行是一个用户的竞赛标签。该标签不能未经定义直接表示每个月的流失。

## 日期与版本判断

当前仅从样本确认了日期字段格式和示例值：交易样本含 `20150930`，到期样本含 `20151101`、`20160427`；日志样本含 `20150513`、`20150709`；注册样本含 `20110911` 等。由于没有安装 7z 命令行工具，本阶段未扫描完整 CSV，因此全量最小/最大日期、完整缺失率和行数尚未确认。

v2 文件的内部路径为 `data/churn_comp_refresh/...`，且与非 v2 文件是不同版本。阶段 2 前必须选择一个版本体系并记录依据，不能按文件名把两个版本纵向拼接。

## 关联键与可开展范围

目前可确认的主要关联键是字符串用户键 `msno`：members、transactions、user_logs、train 都含有它。关联前仍需在阶段 2 以分块方式检查空键、重复键、覆盖范围和一对多关系。

| 问题 | 阶段 1 判断 | 依据与限制 |
|---|---|---|
| 月度实际支付、交易数、付款用户数 | 支持，待全量扫描确认 | transactions 有实际支付和交易日期 |
| 自动续费、取消交易与后续续订 | 附条件支持 | 有 `is_auto_renew`、`is_cancel` 和到期日，但状态规则需核对 |
| 首次观测付费同期群留存 | 附条件支持 | 有交易日期和用户键；历史完整性与观察窗口需确认 |
| 到期前行为与后续续订关联 | 附条件支持 | 有 user_logs 和交易到期字段，必须避免未来信息泄漏 |
| 月末有效订阅用户快照 | 附条件支持 | 需要可靠的有效区间规则，不能仅凭取消标志推断 |
| 月度标准化订阅金额 | 附条件支持 | 只有价格周期和有效区间可靠时才估算，不能称为会计收入或真实 MRR |
| 升级/降级、NRR、获客成本 | 不支持 | 当前样本没有足够证据确认必要字段和口径 |
| 自由生成 SQL | 不支持 | 手册明确要求第一版只使用已验证的预设查询 |

## 当前风险

- 8.3 GiB 外层压缩包中包含大型日志，必须采用流式/分块处理。
- 外层 ZIP 内嵌 7z；当前 macOS 环境缺少 `7z`/`7zz`，后续需安装或使用可用的解压工具后再做全量扫描。
- `train` 是竞赛标签，应与自定义月度流失指标分开命名。
- 交易取消不一定等于即时失效，交易退款/撤销也不能仅凭字段名称猜测。
- 当前日期范围、全量缺失率、完整用户交集和版本重叠尚未完成，不能提前宣布分析范围已冻结。
