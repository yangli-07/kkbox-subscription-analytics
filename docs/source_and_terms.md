# 数据来源与使用限制

## 来源

本地来源是用户已下载并放入 `data/raw` 的 `kkbox-churn-prediction-challenge.zip`。项目手册指定的官方核实入口为：

<https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/data>

本阶段记录来源入口，但没有把 Kaggle 条款文字复制到仓库。正式公开展示、上传 Tableau Public 或分享数据前，必须由项目负责人登录并确认竞赛数据使用条款、第三方数据限制及允许的展示范围。

## 已核对的 Kaggle 规则

根据项目负责人登录 Kaggle 后查看的官方 Data 和 Rules 页面：

- 规则 7A 明确允许在竞赛目的之外用于 Kaggle 网站论坛、学术研究和教育用途。
- 规则 7B 要求采取合理的数据安全措施，不得把 Competition Data 传输、复制、公开发布、重新分发或提供给尚未正式同意规则的非参与者。
- 规则 8B 在满足条件时允许公开代码；代码公开许可不等于原始数据、用户级记录或数据副本可以公开。
- 汇总数据、图表、衍生表以及公开 Tableau/Power BI 页面的发布许可，目前仍未明确确认，不能记录为“全部允许”。

因此本项目只进行本地学习分析，不公开原始数据或用户级数据；公开演示版另行使用独立模拟数据模式。

## 使用边界

- 原始压缩包只放在 `data/raw`，不提交 GitHub。
- 不在代码中写入账号、密码、API 密钥或数据库凭证。
- 报告和本地 BI 仅展示必要的聚合结果或小型合规导出，不展示可识别的原始用户记录；未经进一步许可，不发布公开 BI 页面或截图。
- `train`/`train_v2` 的竞赛标签与自定义业务流失指标分开命名。
- v1 与 v2 先分别审查；没有证据前不纵向合并。
- 公开发布前由项目负责人再次核对当前条款和数据展示权限。

## 仍需保守处理的事项

1. 是否允许将处理后的聚合结果、图表、截图或公开 BI 用于公开作品集；当前不假定允许。
2. 最终版本选择要以本地月份分布、用户覆盖、重叠和标签窗口核查为依据。

## Kaggle 登录核对清单

请使用项目数据页和规则页登录 Kaggle 后逐项确认：

1. 数据页的 `License`、Dataset Description、File Descriptions，以及是否要求接受 Competition Rules 才能访问或使用数据：
   <https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/data>
2. 规则页中 Competition Data 的允许用途，尤其是竞赛、Kaggle 论坛、学术研究和教育用途的范围：
   <https://www.kaggle.com/c/kkbox-churn-prediction-challenge/rules>
3. 数据安全、不得传输/复制/公开发布/再分发给未同意规则者的条款；确认是否允许将聚合截图、衍生表、代码或 Tableau Public 内容公开。
4. Competition Specific Rules、第三方数据、外部数据和提交文件的限制；确认已结束的竞赛是否改变公开发布条件。
5. KKBOX/数据提供方的署名、隐私和去标识化要求；确认 `msno`、用户属性和行为明细不得公开。

在本人完成登录核对前，项目默认：不上传原始数据、不公开用户级记录、不发布 Tableau Public 或其他公开 BI 内容，只在本地使用聚合结果。
