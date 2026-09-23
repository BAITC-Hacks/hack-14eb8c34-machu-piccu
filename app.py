"""WindAgent dashboard: run the forecast cycle, ask the LLM agent, inspect February and accuracy.

    streamlit run app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src import agent, config, llm, pipeline

st.set_page_config(page_title="WindAgent", page_icon="🌬️", layout="wide")

C = {"t1": "#1f77b4", "t2": "#e6851f", "band": "rgba(31,119,180,0.18)", "band2": "rgba(230,133,31,0.18)", "actual": "#333333"}
NAMES = {"t1": "Турбина 1", "t2": "Турбина 2"}
TZ = pd.Timedelta(hours=config.SITE_TZ_OFFSET_HOURS)


# ---------------------------------------------------------------- engine
@st.cache_resource(show_spinner=False)
def get_engine(policy: str):
    eng = pipeline.ForecastPipeline(mode="archive", policy=policy)
    return eng, agent.WindAgent(eng), set()


def ensure_warm(policy: str, date: pd.Timestamp, days: int = 30) -> None:
    eng, ag, done = get_engine(policy)
    need = [d for d in pd.date_range(date - pd.Timedelta(days=days), date - pd.Timedelta(days=1)) if d not in done]
    if need:
        bar = st.progress(0.0, text="Прогрев журнала верификации (детерминированные циклы)")
        for i, d in enumerate(need):
            eng.record(ag.run_cycle(d.strftime("%Y-%m-%d"), publish=False).run); done.add(d)
            bar.progress((i + 1) / len(need))
        bar.empty()


def load_json(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


# ---------------------------------------------------------------- sidebar
st.sidebar.title("WindAgent")
st.sidebar.caption("Шелекская ВЭС, 2 турбины · прогноз на 24–48 ч")
policy = st.sidebar.radio("Политика честности", ["rolling", "strict"], horizontal=True,
                          help="rolling: прогноз погоды 24-часовой давности, выпуск в конце дня D. strict: 48 ч, выпуск в начале дня D.")
date = pd.Timestamp(st.sidebar.date_input("Дата цикла (день D)", value=pd.Timestamp("2026-01-31").date(),
                                          min_value=pd.Timestamp("2025-10-01").date(), max_value=pd.Timestamp("2026-02-27").date()))
provider = llm.available_provider()
model_id = st.sidebar.selectbox("Модель LLM", ["gpt-5-mini", "gpt-5.4-mini", "gpt-4.1-mini", "gpt-5.5"], index=0)
run_det = st.sidebar.button("▶ Рассчитать прогноз", type="primary", use_container_width=True)
run_llm = st.sidebar.button("🤖 Спросить агента (LLM)", use_container_width=True, disabled=provider is None)
st.session_state.setdefault("spent", 0.0)
st.sidebar.caption(f"Провайдер LLM: {provider or 'нет ключа в .env'} · потрачено в сессии ${st.session_state['spent']:.3f}")

tab_cycle, tab_feb, tab_acc, tab_how = st.tabs(["Цикл агента", "Февраль 2026", "Точность", "Как это работает"])

# ---------------------------------------------------------------- cycle tab
with tab_cycle:
    if run_det or run_llm:
        eng, ag, _ = get_engine(policy)
        ensure_warm(policy, date)
        d = date.strftime("%Y-%m-%d")
        if run_llm:
            if st.session_state["spent"] > 0.5:
                st.error("Лимит расходов на сессию $0.50 достигнут.")
                st.stop()
            with st.spinner(f"Агент ({model_id}) проходит цикл через инструменты..."):
                res = ag.run_cycle_with_reasoning(d, provider=provider, model=model_id)
            st.session_state["spent"] += res.usage["estimated_cost_usd"]
        else:
            res = ag.run_cycle(d, publish=False)
        st.session_state["result"] = res
        st.session_state["result_meta"] = (policy, d)

    res = st.session_state.get("result")
    if res is None:
        st.info("Выбери дату и политику слева и нажми «Рассчитать прогноз». Кнопка «Спросить агента» отдаёт те же шаги LLM.")
    else:
        pol, d = st.session_state["result_meta"]
        run = res.run
        issue_local = run.issue_time + pd.Timedelta(days=1 if pol == "rolling" else 0)
        st.subheader(f"Цикл {d} · политика {pol} · сформирован {issue_local.date()} 00:00 местного · режим {res.reasoning_mode}")
        steps = ["1 погода: ECMWF+GFS+ICON", "2 признаки: 61", "3 модель: LightGBM + P10/P50/P90", "4 калибровка", "5 анализ", "6 публикация", "7 обновление входов"]
        st.markdown(" → ".join(f"✅ {s}" for s in steps))

        cols = st.columns(len(run.forecasts))
        for col, (t, a) in zip(cols, run.analysis.items()):
            rev = run.revisions.get(t, {})
            with col:
                st.markdown(f"**{NAMES[t]}**")
                m1, m2, m3 = st.columns(3)
                m1.metric("Энергия 48 ч, экв. часы", a["energy_48h_eflh"])
                m2.metric("День D+1", a["energy_day_ahead_24h_eflh"])
                m3.metric("Уверенность", a["confidence"], help=f"ширина P10–P90 {a['mean_band_width']}, разброс моделей {a['mean_ensemble_spread_ms']} м/с")
                if "mean_abs_change" in rev:
                    arrow = "↓" if rev["mean_signed_change"] < 0 else "↑"
                    st.caption(f"Обновление входов: новые запуски ({rev['current_nwp_lead_hours']} ч) сдвинули дневной прогноз {arrow} на {rev['mean_abs_change']:.3f} от номинала (макс {rev['max_abs_change']:.3f}) относительно вчерашнего ({rev['previous_nwp_lead_hours']} ч).")
                st.caption(f"Пик {a['max_output']:.0%} в {a['peak_hour_local'][:16]} · минимум {a['min_output']:.0%} в {a['trough_hour_local'][:16]} · рампы >25%: {len(a['ramp_events'])}")
                st.caption(f"Калибровка: {a['calibration']}")

        fig = make_subplots(rows=len(run.forecasts), cols=1, shared_xaxes=True, subplot_titles=[NAMES[t] for t in run.forecasts], vertical_spacing=0.09)
        for i, (t, f) in enumerate(run.forecasts.items(), start=1):
            x = f["time_local"]
            actual = eng_actual = None
            eng, _, _ = get_engine(pol)
            sc = eng.scada(t); sc_local = sc.assign(time_local=sc["time"] + TZ).set_index("time_local")["power"].reindex(x)
            fig.add_trace(go.Scatter(x=pd.concat([x, x[::-1]]), y=pd.concat([f["p90"], f["p10"][::-1]]), fill="toself", fillcolor=C["band"] if t == "t1" else C["band2"], line=dict(width=0), name="P10–P90", showlegend=(i == 1), hoverinfo="skip"), row=i, col=1)
            fig.add_trace(go.Scatter(x=x, y=f["forecast"], mode="lines", line=dict(color=C[t], width=2), name="прогноз", showlegend=(i == 1), hovertemplate="%{x|%d.%m %H:%M}<br>прогноз %{y:.2f}<extra></extra>"), row=i, col=1)
            if sc_local.notna().any():
                fig.add_trace(go.Scatter(x=x, y=sc_local.values, mode="lines", line=dict(color=C["actual"], width=1.2), name="факт", showlegend=(i == 1), hovertemplate="%{x|%d.%m %H:%M}<br>факт %{y:.2f}<extra></extra>"), row=i, col=1)
            boundary = f.loc[f["horizon_day"] == 2, "time_local"].min()
            fig.add_vline(x=boundary, line=dict(color="#999", dash="dot"), row=i, col=1)
        fig.update_yaxes(range=[0, 1.02], title_text="доля номинала")
        fig.update_layout(height=520, margin=dict(l=40, r=20, t=50, b=30), legend=dict(orientation="h", y=1.08), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Разбор для диспетчера")
        st.markdown(res.briefing if res.reasoning_mode != "autonomous" else f"```\n{res.briefing}\n```")
        if res.transcript:
            with st.expander(f"Ход рассуждений агента · {res.usage['steps']} шагов · {res.usage['prompt_tokens']} вх. / {res.usage['completion_tokens']} исх. токенов · ~${res.usage['estimated_cost_usd']:.4f}"):
                for e in res.transcript:
                    if e["role"] == "assistant":
                        for c in e.get("tool_calls", []):
                            st.markdown(f"🔧 `{c['name']}` {json.dumps(c['input'], ensure_ascii=False)}")
                        if e.get("content"):
                            st.markdown(e["content"])
                    elif e["role"] == "tool":
                        for r in e["results"]:
                            st.code(r["content"][:1500], language="json")
        saved = config.OUTPUT_DIR / "agent_transcripts" / f"briefing_{pd.Timestamp(d).strftime('%Y%m%d')}_{pol}.md"
        if res.reasoning_mode == "autonomous" and saved.exists():
            with st.expander("Сохранённый разбор LLM-агента для этой даты (из репозитория, без затрат)"):
                st.markdown(saved.read_text())

# ---------------------------------------------------------------- february tab
with tab_feb:
    sub_path = config.OUTPUT_DIR / f"february_2026_{policy}_submission_local.csv"
    rep = load_json(config.OUTPUT_DIR / f"february_2026_{policy}_report.json")
    if sub_path.exists():
        sub = pd.read_csv(sub_path, parse_dates=["time_local"])
        daily = sub.groupby([sub["time_local"].dt.date, "turbine"])["forecast"].sum().unstack()
        st.subheader(f"Сдача: 1–28 февраля 2026, политика {policy}, {len(sub)} строк")
        fig = go.Figure()
        for t in daily.columns:
            fig.add_trace(go.Bar(x=daily.index, y=daily[t], name=NAMES[t], marker_color=C[t], hovertemplate="%{x}<br>%{y:.1f} экв. часов<extra>" + NAMES[t] + "</extra>"))
        fig.update_layout(barmode="group", height=360, margin=dict(l=40, r=20, t=30, b=30), yaxis_title="энергия за сутки, экв. часы полной нагрузки", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Средний КИУМ февраля", f"{sub['forecast'].mean():.0%}")
        if rep:
            iu = rep["input_updates"]
            c2.metric("Циклов с существенной ревизией", f"{iu['cycles_with_material_change']} из {iu['cycles_checked']}", help="новые запуски погоды сдвинули дневной прогноз больше чем на 0.02 от номинала")
            c3.metric("Упреждение NWP, ч", f"{rep['nwp_lead_hours']['day_ahead']} / {rep['nwp_lead_hours']['day_2']}")
        d1, d2 = st.columns(2)
        for col, pol in ((d1, "rolling"), (d2, "strict")):
            p = config.OUTPUT_DIR / f"february_2026_{pol}_submission_local.csv"
            if p.exists():
                col.download_button(f"Скачать сдачу {pol}", p.read_bytes(), file_name=p.name, mime="text/csv", use_container_width=True)
        st.dataframe(sub.head(48), use_container_width=True, height=300)
    else:
        st.warning("Файл сдачи не найден: запусти `python -m src.backtest --policy " + policy + "`")

# ---------------------------------------------------------------- accuracy tab
with tab_acc:
    rep = load_json(config.OUTPUT_DIR / f"verified_{policy}_report.json")
    val = load_json(config.ARTIFACT_DIR / "validation_summary.json")
    da_path = config.OUTPUT_DIR / f"verified_{policy}_hourly_day_ahead.csv"
    if rep and val and da_path.exists():
        st.subheader(f"122-дневный проверочный реплей · {rep['verified_hours']:,} проверенных часов · политика {policy}".replace(",", " "))
        ct = val["comparison_table"]
        rows = [("WindAgent, день D+1", rep["day_ahead"]["mae"], rep["day_ahead"]["rmse"], rep["day_ahead"]["r2"]),
                ("Кривая мощности по ветру NWP, без ML", ct["mae"]["power_curve"], ct["rmse"]["power_curve"], ct["r2"]["power_curve"]),
                ("Климатология", ct["mae"]["climatology"], ct["rmse"]["climatology"], ct["r2"]["climatology"]),
                ("Персистентность", ct["mae"]["persistence"], ct["rmse"]["persistence"], ct["r2"]["persistence"])]
        st.dataframe(pd.DataFrame(rows, columns=["прогноз", "MAE", "RMSE", "R²"]).round(4), use_container_width=True, hide_index=True)
        k1, k2, k3 = st.columns(3)
        k1.metric("Покрытие P10–P90 (цель 80%)", f"{rep['coverage']['coverage']:.1%}")
        rg = rep["revision_gain"]; k2.metric("Выигрыш ежедневного пересчёта", f"{rg['improvement_pct']:.1f}%", help=f"MAE {rg['mae_day_2']} → {rg['mae_day_ahead']} на {rg['hours']} часах")
        k3.metric("Выигрыш к персистентности", f"{100 * (1 - rep['day_ahead']['mae'] / ct['mae']['persistence']):.0f}%")
        da = pd.read_csv(da_path, parse_dates=["time_local"])
        weeks = sorted(da["time_local"].dt.to_period("W").unique())
        week = st.select_slider("Неделя", options=[str(w) for w in weeks], value=str(weeks[-2]))
        w = da[da["time_local"].dt.to_period("W").astype(str) == week]
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=[NAMES["t1"], NAMES["t2"]], vertical_spacing=0.09)
        for i, t in enumerate(("t1", "t2"), start=1):
            g = w[w["turbine"] == t]; x = g["time_local"]
            fig.add_trace(go.Scatter(x=pd.concat([x, x[::-1]]), y=pd.concat([g["p90"], g["p10"][::-1]]), fill="toself", fillcolor=C["band"] if t == "t1" else C["band2"], line=dict(width=0), name="P10–P90", showlegend=(i == 1), hoverinfo="skip"), row=i, col=1)
            fig.add_trace(go.Scatter(x=x, y=g["forecast"], mode="lines", line=dict(color=C[t], width=2), name="прогноз D+1", showlegend=(i == 1)), row=i, col=1)
            fig.add_trace(go.Scatter(x=x, y=g["power"], mode="lines", line=dict(color=C["actual"], width=1.2), name="факт", showlegend=(i == 1)), row=i, col=1)
        fig.update_yaxes(range=[0, 1.02]); fig.update_layout(height=480, margin=dict(l=40, r=20, t=50, b=30), legend=dict(orientation="h", y=1.08), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        st.image(str(config.REPORT_DIR / "error_vs_lead.png"), caption="Ошибка растёт с упреждением; обе политики лучше базовых прогнозов")
    else:
        st.warning("Нет проверочного реплея: `python -m src.backtest --start 2025-10-01 --end 2026-01-30 --label verified --policy " + policy + "`")

# ---------------------------------------------------------------- how tab
with tab_how:
    st.markdown("""
#### Цикл агента, раз в сутки
1. **Погода**: три независимые модели (ECMWF IFS, GFS, ICON) из архива Open-Meteo на честном упреждении, или live-прогноз.
2. **Признаки**: блок на местные сутки D+1 и D+2, 61 признак: физика ветра, рампы, разброс ансамбля, кривая мощности площадки.
3. **Модель**: LightGBM, точечный прогноз и квантили P10/P50/P90, обучена на упреждении 24 ч.
4. **Калибровка**: поправка смещения и ширины интервала по собственным проверенным ошибкам за 14–21 день.
5. **Анализ**: энергия, пик и минимум, рампы, разброс моделей, уверенность.
6. **Публикация**: почасовой CSV и JSON-разбор.
7. **Обновление входов**: насколько новые запуски погоды сдвинули вчерашний прогноз на те же часы; в live-режиме прогноз запрашивается заново.

#### Две политики честности
- **rolling**: прогноз «на день D» сформирован к концу дня D, каждый час дня D+1 опирается на прогноз погоды 24-часовой давности.
- **strict**: сформирован в начале дня D, упреждение 48 ч; ничего, выпущенного в сам день D, не используется. Цена строгости на 122 днях: +11% MAE.

#### Два режима
Автономный: детерминированная политика, без ключей, воспроизводимо байт-в-байт. Рассуждающий: те же шаги отданы LLM
как пять инструментов; LLM не выдумывает ни одного числа, каждая цифра приходит из инструмента; транскрипты сохраняются,
28 февральских циклов проходят автоматическую сверку (`python -m src.audit_transcripts`).

Подробности и все команды: `README.md`. Тесты честности: `python -m pytest -q` (14 тестов, офлайн).
""")
