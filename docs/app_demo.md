# Streamlit 应用运行说明

## 文件

- 应用入口：`app/streamlit_app.py`
- 数据目录：`data/processed`
- 读取文件：`sql_monthly_summary.csv`、`sql_payment_plan_summary.csv`、`sql_version_profile.csv`
- 独立模拟数据：`app/demo_data/sql_monthly_summary.csv`、`app/demo_data/sql_payment_plan_summary.csv`、`app/demo_data/sql_version_profile.csv`

应用不会读取 `data/raw`、ZIP、交易明细或用户级记录。v1/v2 始终分开显示。

页面左侧的“数据模式”可以选择：

- `本机 SQL 汇总数据`：读取 `data/processed` 下由 PostgreSQL 导出的三个汇总 CSV；只有三个文件都存在时才显示此选项。
- `模拟演示数据`：读取 `app/demo_data` 下独立生成的少量模拟 CSV，不包含真实数据数值。公开演示时应选择此模式。

如果本机汇总 CSV 不存在，应用会自动使用模拟演示数据模式，并在页面顶部显著标明当前模式。

## 安装与启动

```bash
cd 项目根目录
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

浏览器打开 Streamlit 显示的本地地址即可。

## 问答能力

当前问答默认使用当前数据模式下三个汇总 CSV 的确定性回答，不需要 API 密钥。OpenAI 接口是可选代码路径；本次公开演示准备不配置密钥、不调用 OpenAI。对于真实留存率、真实用户流失、净收入、MRR、用户级行为等问题，应用会明确说明数据不支持。

安全配置示例：

```bash
cp .env.example .env
# 只在本机编辑 .env，填入 OPENAI_API_KEY 和可选的 OPENAI_MODEL
streamlit run app/streamlit_app.py
```

`.env` 已被 `.gitignore` 忽略；不要把密钥写入代码、提交 Git、输出到日志，或发送用户级原始数据。公开演示版应切换到独立模拟数据模式。
