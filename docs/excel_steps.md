# Excel 交易核对步骤

## 需要打开的文件

项目根目录：在项目根目录执行以下操作。

先打开以下文件：

1. `excel/input/sample_users.csv`
2. `excel/input/transactions_sample.csv`
3. `excel/input/monthly_reconciliation.csv`

第一步：打开 Excel，选择“数据 → 从文本/CSV”，先导入 `sample_users.csv`；将 `msno` 指定为“文本”，不要让 Excel 将用户编号转换为数字或科学计数法。随后对另外两个 CSV 重复导入，并把 `transaction_date`、`membership_expire_date` 作为文本或按 `YYYYMMDD` 转换为日期。

## 字段与金额说明

交易明细实际字段：

`source_version`, `msno`, `payment_method_id`, `payment_plan_days`, `plan_list_price`, `actual_amount_paid`, `is_auto_renew`, `transaction_date`, `membership_expire_date`, `is_cancel`, `transaction_month`

`actual_amount_paid` 在本工作簿中命名为“交易记录金额”。取消记录仍保留，不自动删除；该金额不是净收入，也不是 MRR。v1/v2 通过 `source_version` 分开核对。

## 建议工作表

- `README`：记录样本为 10,000 名用户、v1/v2 分开、日志暂不纳入。
- `Users`：`sample_users.csv`。
- `Transactions`：`transactions_sample.csv`，转换为 Excel 表格并命名 `Transactions`。
- `MonthlyReconciliation`：`monthly_reconciliation.csv`。
- `Checks`：公式核对和异常清单。
- `Summary`：只放已核对的交易记录金额、交易数和付款用户数。

## COUNTIFS 核对

在 `Checks` 中按月、按版本核对交易行数。假设 `Transactions` 表列名保持原样：

```excel
=COUNTIFS(Transactions[source_version],$A2,Transactions[transaction_month],$B2)
```

核对某个用户的交易行数：

```excel
=COUNTIF(Transactions[msno],A2)
```

不要把同一用户出现多次当成错误；交易表允许同一用户多行。

## SUMIFS 核对

按版本和月份核对交易记录金额：

```excel
=SUMIFS(Transactions[actual_amount_paid],Transactions[source_version],$A2,Transactions[transaction_month],$B2)
```

结果应与 `MonthlyReconciliation` 中对应 `source_version`、`transaction_month` 的 `transaction_record_amount` 一致。不要把 v1 和 v2 相同月份直接相加。

## 透视表

从 `Transactions` 表插入透视表：

- 行：`transaction_month`
- 列：`source_version`
- 值：`actual_amount_paid` 求和、`msno` 计数
- 筛选：`is_auto_renew`、`is_cancel`、`payment_method_id`

用户数需要用“不同用户计数”核对；如果当前 Excel 版本无法在普通透视表中使用不同计数，使用 `MonthlyReconciliation` 的 `paying_users` 作为参考，不要把交易行数误当付款用户数。

## 手工检查

至少检查：2 个完全重复行、同一用户同日多笔交易、2 个到期日早于交易日的记录、v1/v2 重叠用户，以及 v1 和 v2 各一个月份。记录预期值、Excel 值和差异。日志行为和未核实的流失标签不放入本工作簿。
