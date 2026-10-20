from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:  # The app still runs without optional .env loading.
    load_dotenv = None


APP_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = APP_ROOT / "data" / "processed"

MONTHLY_FILE = PROCESSED / "sql_monthly_summary.csv"
PLAN_FILE = PROCESSED / "sql_payment_plan_summary.csv"
PROFILE_FILE = PROCESSED / "sql_version_profile.csv"
DEMO_DATA = APP_ROOT / "app" / "demo_data"

if load_dotenv is not None:
    load_dotenv(APP_ROOT / ".env")


st.set_page_config(page_title="KKBOX 交易汇总分析", page_icon="📊", layout="wide")


@st.cache_data
def load_data(data_mode: str):
    """Load only the three approved aggregate CSVs."""
    if data_mode == "模拟演示数据":
        monthly_file = DEMO_DATA / "sql_monthly_summary.csv"
        plan_file = DEMO_DATA / "sql_payment_plan_summary.csv"
        profile_file = DEMO_DATA / "sql_version_profile.csv"
    else:
        monthly_file = MONTHLY_FILE
        plan_file = PLAN_FILE
        profile_file = PROFILE_FILE
    monthly = pd.read_csv(monthly_file, dtype={"source_version": "string", "transaction_month": "string"})
    plans = pd.read_csv(plan_file, dtype={"source_version": "string"})
    profile = pd.read_csv(profile_file, dtype={"source_version": "string"})
    monthly["transaction_month_date"] = pd.to_datetime(monthly["transaction_month"], format="%Y-%m")
    return monthly, plans, profile


def money(value: float) -> str:
    return f"{value:,.0f}"


def unsupported_answer(question: str) -> str | None:
    q = question.strip().lower()
    unsupported = [
        ("留存", "这三个汇总 CSV 不包含同期群或有效订阅状态，无法判断真实留存率。"),
        ("流失", "这三个汇总 CSV 不包含用户级到期后续订观察，无法判断真实用户流失。"),
        ("净收入", "文件中的金额是交易记录金额，无法判断净收入。"),
        ("mrr", "文件中的金额是交易记录金额，无法判断 MRR。"),
        ("行为", "这三个汇总 CSV 不包含 user_logs 行为数据，无法判断用户级行为。"),
        ("用户级", "应用只读取聚合数据，不包含用户级记录，无法回答该问题。"),
    ]
    for key, message in unsupported:
        if key in q:
            return message
    return None


def answer_question(question: str, monthly: pd.DataFrame, plans: pd.DataFrame, profile: pd.DataFrame) -> str:
    unsupported = unsupported_answer(question)
    if unsupported:
        return unsupported
    q = question.strip().lower()

    if any(key in q for key in ["自动续费", "续费"]):
        rows = profile.copy()
        return "\n\n".join(
            f"{r.source_version}: 自动续费记录 {int(r.auto_renew_record_count):,} 条，占交易记录 {r.auto_renew_record_share:.2%}。"
            for r in rows.itertuples()
        )
    if any(key in q for key in ["取消标记", "取消"]):
        rows = profile.copy()
        return "\n\n".join(
            f"{r.source_version}: 带取消标记记录 {int(r.cancel_flag_record_count):,} 条，占交易记录 {r.cancel_flag_record_share:.2%}；这不等于已流失用户。"
            for r in rows.itertuples()
        )
    if any(key in q for key in ["付款方式", "支付方式", "计划"]):
        rows = plans.sort_values("transaction_record_amount", ascending=False).head(5)
        return "前 5 个交易记录金额分组：\n\n" + "\n".join(
            f"{r.source_version} / payment_method_id={r.payment_method_id} / {r.payment_plan_days} 天：{int(r.transaction_count):,} 条，交易记录金额 {money(r.transaction_record_amount)}。"
            for r in rows.itertuples()
        )
    if any(key in q for key in ["金额", "支付", "交易"]):
        rows = monthly.groupby("source_version", as_index=False).agg(
            transaction_count=("transaction_count", "sum"),
            distinct_user_count=("distinct_user_count", "sum"),
            transaction_record_amount=("transaction_record_amount", "sum"),
        )
        return "\n\n".join(
            f"{r.source_version}: 汇总交易记录 {int(r.transaction_count):,} 条，月份去重用户数之和 {int(r.distinct_user_count):,}，交易记录金额 {money(r.transaction_record_amount)}。月份去重用户数之和不是全期去重用户数。"
            for r in rows.itertuples()
        )
    return "目前只能根据这三个汇总 CSV 回答：月度交易趋势、交易记录金额、付款计划分组、自动续费记录和取消标记记录。请换一种问法。"


def openai_answer(question: str, monthly: pd.DataFrame, plans: pd.DataFrame, profile: pd.DataFrame) -> str:
    """Ask OpenAI using only the currently filtered aggregate rows."""
    unsupported = unsupported_answer(question)
    if unsupported:
        return unsupported

    from openai import OpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {
        "monthly_summary": monthly.drop(columns=["transaction_month_date"], errors="ignore").to_dict(orient="records"),
        "payment_plan_summary": plans.to_dict(orient="records"),
        "version_profile": profile.to_dict(orient="records"),
    }
    instructions = (
        "你是 KKBOX 交易汇总分析助手。只能使用用户提供的三个聚合 CSV 数据和当前筛选范围。"
        "v1 与 v2 必须分开解释。只能讨论月度交易笔数、月份去重用户数、交易记录金额、付款计划、"
        "自动续费记录和取消标记记录。明确说明 transaction_record_amount 是交易记录金额，"
        "不是净收入或 MRR；取消标记记录不等于真实流失。不要推断真实留存、真实流失、用户级行为或因果关系。"
        "如果数据不支持问题，直接说明无法判断。不要声称访问了其他文件或外部数据。"
    )
    response = OpenAI(api_key=os.environ["OPENAI_API_KEY"]).responses.create(
        model=model,
        instructions=instructions,
        input=("当前聚合数据 JSON：\n" + json.dumps(payload, ensure_ascii=False) + "\n\n用户问题：" + question),
        max_output_tokens=800,
    )
    return response.output_text


st.title("KKBOX 交易汇总分析")
local_available = all(path.exists() for path in [MONTHLY_FILE, PLAN_FILE, PROFILE_FILE])
mode_options = ["本机 SQL 汇总数据", "模拟演示数据"]
default_mode = "本机 SQL 汇总数据" if local_available else "模拟演示数据"
st.sidebar.subheader("数据模式")
data_mode = st.sidebar.radio(
    "选择应用读取的数据",
    mode_options,
    index=mode_options.index(default_mode),
    key="data_mode",
)
if data_mode == "模拟演示数据":
    st.success("当前数据模式：模拟演示数据（独立生成，仅用于公开演示）")
else:
    st.info("当前数据模式：本机 SQL 汇总数据（data/processed）")
st.caption("v1 与 v2 始终分开；应用不会读取 data/raw。")

try:
    monthly, plans, profile = load_data(data_mode)
except FileNotFoundError as exc:
    st.error(f"缺少汇总文件：{exc.filename}")
    st.stop()

versions = sorted(monthly["source_version"].dropna().unique().tolist())
selected_versions = st.sidebar.multiselect("版本", versions, default=versions)
available_months = sorted(monthly["transaction_month"].dropna().unique().tolist())
start_month, end_month = st.sidebar.select_slider(
    "月份范围", options=available_months, value=(available_months[0], available_months[-1])
)

filtered_monthly = monthly[
    monthly["source_version"].isin(selected_versions)
    & monthly["transaction_month"].between(start_month, end_month)
].copy()
filtered_plans = plans[plans["source_version"].isin(selected_versions)].copy()
filtered_profile = profile[profile["source_version"].isin(selected_versions)].copy()

st.subheader("月度趋势")
if filtered_monthly.empty:
    st.info("当前筛选没有数据。")
else:
    chart_data = filtered_monthly.pivot(index="transaction_month", columns="source_version")
    chart_data = chart_data.sort_index()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**每月交易笔数**")
        st.line_chart(filtered_monthly.pivot(index="transaction_month", columns="source_version", values="transaction_count"))
    with c2:
        st.markdown("**每月去重用户数**")
        st.line_chart(filtered_monthly.pivot(index="transaction_month", columns="source_version", values="distinct_user_count"))
    with c3:
        st.markdown("**交易记录金额**")
        st.line_chart(filtered_monthly.pivot(index="transaction_month", columns="source_version", values="transaction_record_amount"))

st.subheader("付款计划汇总")
st.dataframe(
    filtered_plans.sort_values(["source_version", "transaction_record_amount"], ascending=[True, False]),
    use_container_width=True,
    hide_index=True,
)

st.subheader("版本级概览")
if filtered_profile.empty:
    st.info("当前筛选没有版本概览数据。")
else:
    display_profile = filtered_profile.rename(
        columns={
            "transaction_count": "交易记录数",
            "distinct_user_count": "不同用户数",
            "auto_renew_record_count": "自动续费记录数",
            "auto_renew_record_share": "自动续费记录占比",
            "cancel_flag_record_count": "取消标记记录数",
            "cancel_flag_record_share": "取消标记记录占比",
            "transaction_record_amount": "交易记录金额",
        }
    )
    st.dataframe(display_profile, use_container_width=True, hide_index=True)
    st.caption("取消标记记录不等于已流失用户；交易记录金额不等于净收入或 MRR。")

st.subheader("自然语言问答")
api_configured = bool(os.getenv("OPENAI_API_KEY"))
if api_configured:
    st.caption("已检测到 OpenAI 配置；默认仍使用确定性回答。勾选后才会发起 API 请求。")
else:
    st.caption("AI 尚未连接；当前使用确定性问答，不需要 API 密钥。")
question = st.text_input("例如：v1 和 v2 哪个月份交易记录金额较高？")
use_openai = st.checkbox("使用 OpenAI 回答（需要本机配置 OPENAI_API_KEY）", disabled=not api_configured)
if question:
    if use_openai:
        try:
            st.info(openai_answer(question, filtered_monthly, filtered_plans, filtered_profile))
        except Exception:
            st.warning("OpenAI 请求未完成，已切换到确定性问答；未显示请求细节或密钥。")
            st.info(answer_question(question, filtered_monthly, filtered_plans, filtered_profile))
    else:
        st.info(answer_question(question, filtered_monthly, filtered_plans, filtered_profile))

st.divider()
st.caption("公开演示时请使用独立模拟数据模式；本应用不读取 data/raw，也不包含用户级数据。")
