import streamlit as st
import numpy as np
import pandas as pd
import json
import altair as alt
from pathlib import Path
import requests
from datetime import datetime
import hirlite


from utils import get_bj_day_time, get_yestoday_bj, get_bj_day, safe_div
from data import Database

experiments_file = "docs/experiments.json"
model_type_file = "docs/modeltypes.json"
cache_store = hirlite.Rlite("db/cache.db", encoding="utf8")

import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp


class Dashboard:
    class Model:
        pageTitle = "Dashboard"

        paysTitle = "今日/昨日总付费 $"

        inferenceTimeTitle = "data update cnt(all)"

        altPaysTitle = "model/control总付费 $"

        dailyInferenceTitle = "model/control Lift ＄"

        accuracyTitle = "query cnt(all)"

        titleModelTypeAvgPays = "## Model Type Avg Pays"
        titleModelTypePays = "## Model Type Pays"
        ModelTypePaysHeader = "Algorithms/Strategies Pays"
        DiffRPaysHeader = "Pay_type Pays"
        titleMidR = "## Mid R"
        titleBigR = "## Big R"
        titleSmallR = "## Small R"
        titleAllPlayers = "## All Players"

        status_file = "docs/status.json"
        annotation_files_dir = "docs/json"

        def set_data_update_status(self):
            st.session_state["data_update_status"] = ["no", "yes"]

        def get_data_update_status(self):
            if "data_update_status" not in st.session_state:
                return None
            return st.session_state["data_update_status"]

    def view(self, model):
        # st.title(model.pageTitle)

        with st.container():
            with open(experiments_file, "r") as f:
                experiments_json = json.load(f)

            experiments = experiments_json["experiments"]
            experiment_ids = [ab_id_json["name"] for ab_id_json in experiments]
            _dt_now = cache_store.get("latest_time")
            if _dt_now is None:
                dt_now = get_bj_day_time()
            else:
                dt_now = _dt_now

            # dt_day = dt_now.strftime('%A')
            _, colT2 = st.columns([3, 7])
            with colT2:
                st.title("Real-Time / RL 模型实验")
                # st.write(f"### Data updated time: `{dt_now}`")
                st.caption(f"### Data updated time: `{dt_now}`")

            # with open('style.css') as f:
            #    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            st.sidebar.header("Modelpayboard `v.1.0`")
            st.sidebar.subheader("Experiments")
            update_status = model.get_data_update_status()
            if update_status is None:
                update_status = ["no", "yes"]

            process_data = st.sidebar.selectbox(
                "Update Real-Time Data",
                update_status,
            )

            ab_id_name = st.sidebar.selectbox(
                "Display by experiment",
                experiment_ids,
            )
            ## 数据更新次数
            ## 查询次数
            today = get_bj_day()
            yestoday = get_yestoday_bj()
            data_update_key = f"data_update:{today}"
            data_update_all_key = f"data_update:all"
            data_query_key = f"query:{today}:{ab_id_name}"
            data_query_all_key = f"query:all:{ab_id_name}"
            cache_store.incr(data_query_key)
            cache_store.incr(data_query_all_key)
            filyer_pays = st.sidebar.slider("Filter user pays", 0, 20000, 0)
            db = Database(filter_big_user=filyer_pays)

            if process_data == "yes":
                db.get_realdata_frombq()
                db.get_model_type_frombq(ab_name_list=experiment_ids)
                dt_now = get_bj_day_time()
                cache_store.set("latest_time", dt_now)
                cache_store.set("filter_pays", str(filyer_pays))
                cache_store.incr(data_update_key)
                cache_store.incr(data_update_all_key)
                model.set_data_update_status()

            today_all_pays, yes_today_all_pays = db.get_allpays(ab_id_name)
            _filter_pays = cache_store.get("filter_pays")
            if _filter_pays is None:
                filter_pays_selected = filyer_pays
            else:
                filter_pays_selected = str(_filter_pays)

            if float(filter_pays_selected) > 0:
                st.caption(f"剔除当日总付费超过`{filter_pays_selected}美金`的玩家，实验: `{ab_id_name}`")
                # st.write(f"剔除当日总付费超过`{filter_pays_selected}美金`的玩家，实验: `{ab_id_name}`")
            else:
                st.caption(f"全量玩家，实验: `{ab_id_name}`")
                # st.write(f"全量玩家，实验: `{ab_id_name}`")
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                _today_all_pays = round(today_all_pays / 10000, 2)
                _yesday_all_pays = round(yes_today_all_pays / 10000, 2)
                delta_pays = round((today_all_pays / yes_today_all_pays - 1) * 100, 2)

                st.metric(
                    label=model.paysTitle,
                    value=str(_today_all_pays) + "W",
                    delta=f"{delta_pays}% ({_yesday_all_pays}W)",
                )
            _model_val, _control_val = db.cal_model_control_pays(ab_name=ab_id_name)
            try:
                delta_alt_pays = round((_model_val / _control_val - 1) * 100, 2)
            except:
                delta_alt_pays = 0.0
            with col2:
                model_val = round(_model_val / 10000, 2)
                try:
                    control_val = round(_control_val / 10000, 2)
                except:
                    control_val = 0.0
                # delta_alt_pays = round((model_val / control_val - 1) * 100, 2)

                st.metric(
                    label=model.altPaysTitle,
                    value=str(model_val) + "W",
                    delta=f"{delta_alt_pays}% ({control_val}W)",
                )

            with col3:
                try:
                    model_gap = round((_model_val - _control_val) / 10000, 3)
                except:
                    model_gap = 0.0
                    st.error("请更新数据")
                st.metric(
                    label=model.dailyInferenceTitle,
                    value=str(model_gap) + "W",
                    delta=str(delta_alt_pays) + "%",
                )

            with col4:
                delta_time = 0
                data_update_yestoday_cnt = 0
                all_data_update_cnt = 0
                # calculate inference time average
                all_data_update_cnt = cache_store.get(data_update_all_key)
                data_update_yestoday_key = f"data_update:{yestoday}"
                data_update_yestoday_cnt = cache_store.get(data_update_yestoday_key)
                if data_update_yestoday_cnt is None:
                    data_update_yestoday_cnt = 0
                else:
                    data_update_yestoday_cnt = int(data_update_yestoday_cnt)
                data_update_today_cnt = cache_store.get(data_update_key)
                if data_update_today_cnt is None:
                    data_update_today_cnt = 0
                else:
                    data_update_today_cnt = int(data_update_today_cnt)
                delta_time = (
                    safe_div(data_update_today_cnt, data_update_yestoday_cnt) - 1
                )
                if int(all_data_update_cnt) > 1000:
                    all_data_update_cnt = int(all_data_update_cnt)
                    updata_all = f"{round(all_data_update_cnt/1000,2)}K"
                else:
                    updata_all = str(all_data_update_cnt)

                if int(data_update_today_cnt) > 1000:
                    data_update_today_cnt = int(data_update_today_cnt)
                    data_update_today_cnt = f"{round(data_update_today_cnt/1000,1)}K"
                if int(data_update_yestoday_cnt) > 1000:
                    data_update_yestoday_cnt = int(data_update_yestoday_cnt)
                    data_update_yestoday_cnt = (
                        f"{round(data_update_yestoday_cnt/1000,1)}K"
                    )
                st.metric(
                    label=model.inferenceTimeTitle,
                    value=updata_all,
                    delta=f"{round(delta_time*100,2)}"
                    + "%"
                    + f"({data_update_today_cnt}/{data_update_yestoday_cnt})",
                    delta_color="inverse",
                )

            with col5:
                avg_accuracy = 0.98
                delta_accuracy = 0
                data_query_yestoday_cnt = 0

                all_query_cnt = cache_store.get(data_query_all_key)
                data_query_yestoday_key = f"query:{yestoday}:{ab_id_name}"
                data_query_yestoday_cnt = cache_store.get(data_query_yestoday_key)
                if data_query_yestoday_cnt is None:
                    data_query_yestoday_cnt = 0
                else:
                    data_query_yestoday_cnt = int(data_query_yestoday_cnt)

                data_query_today_cnt = cache_store.get(data_query_key)
                if data_query_today_cnt is None:
                    data_query_today_cnt = 0
                else:
                    data_query_today_cnt = int(data_query_today_cnt)
                delta_accuracy = (
                    safe_div(data_query_today_cnt, data_query_yestoday_cnt) - 1
                )

                if int(all_query_cnt) > 1000:
                    all_query_cnt = int(all_query_cnt)
                    query_all = f"{round(all_query_cnt/1000,2)}K"
                else:
                    query_all = str(all_query_cnt)

                if int(data_query_today_cnt) > 1000:
                    data_query_today_cnt = int(data_query_today_cnt)
                    data_query_today_cnt = f"{round(data_query_today_cnt/1000,1)}K"
                if int(data_query_yestoday_cnt) > 1000:
                    data_query_yestoday_cnt = int(data_query_yestoday_cnt)
                    data_query_yestoday_cnt = (
                        f"{round(data_query_yestoday_cnt/1000,1)}K"
                    )

                st.metric(
                    label=model.accuracyTitle,
                    value=query_all,
                    delta=f"{round(delta_accuracy*100,2)}"
                    + "%"
                    + f"({data_query_today_cnt}/{data_query_yestoday_cnt})",
                    delta_color="inverse",
                )

            st.markdown("---")

        with st.container():
            # col1, col2 = st.columns(2)
            st.subheader(model.ModelTypePaysHeader)

            with open(model_type_file, "r") as f:
                modeltypes_json = json.load(f)

            modeltypes = modeltypes_json["modeltypes"]
            model_type_names = [
                model_type_json["description"]
                for model_type_json in modeltypes
                if model_type_json["name"] == ab_id_name
            ]
            model_type_list = []
            for mt in model_type_names:
                try:
                    mt_l = eval(mt)
                except:
                    mt_l = []
                if isinstance(mt_l, list):
                    model_type_list = mt_l

            df_avg_user_usd, df_usd = db.get_model_type_pays(
                ab_name=ab_id_name, model_type_list=model_type_list
            )

            df_usd.dropna(inplace=True)
            self.plot_line_chart(df=df_usd)

            # avg pays
            df_avg_user_usd.dropna(inplace=True)
            self.plot_line_chart(
                df=df_avg_user_usd,
                y="avg_user_usd",
                title="Model Type Avg Pays",
                yaxis_title="avg user usd",
            )

        st.markdown("---")

        with st.container():
            st.subheader(model.DiffRPaysHeader)
            col1, col2 = st.columns(2)

            with col1:
                all_data = {}
                with st.container():
                    df_bigR, df2 = db.classify_by_paytype(["big_R"], ab_name=ab_id_name)
                    df_list = df_bigR.to_dict(orient="records")  # ["pays"]
                    alternatives_list = []
                    values_list = []
                    for dict_df in df_list:
                        values_list.append(dict_df["pays"])
                        alternatives_list.append(dict_df["alternatives"])

                    # 根据 list1 进行排序，并重新生成已排序的 list2
                    sorted_lists_b = sorted(zip(alternatives_list, values_list))
                    alternatives_list_b, values_list_b = zip(*sorted_lists_b)

                    all_data["bigr_alt"] = alternatives_list_b
                    all_data["bigr_pays"] = values_list_b
                    data_bigr = pd.DataFrame(
                        {
                            "alternatives": alternatives_list,
                            "Pays": values_list,
                        }
                    )
                    self.plot_bar_chart(df=data_bigr, title="Big R")

                    df_midR, df2 = db.classify_by_paytype(["mid_R"], ab_name=ab_id_name)
                    df_list = df_midR.to_dict(orient="records")  # ["pays"]
                    alternatives_list = []
                    values_list = []
                    for dict_df in df_list:
                        values_list.append(dict_df["pays"])
                        alternatives_list.append(dict_df["alternatives"])

                    # 根据 list1 进行排序，并重新生成已排序的 list2
                    sorted_lists_m = sorted(zip(alternatives_list, values_list))
                    alternatives_list_m, values_list_m = zip(*sorted_lists_m)

                    all_data["midr_alt"] = alternatives_list_m
                    all_data["midr_pays"] = values_list_m
                    data_midr = pd.DataFrame(
                        {
                            "alternatives": alternatives_list,
                            "Pays": values_list,
                        }
                    )
                    self.plot_bar_chart(df=data_midr, title="Mid R")

                    # small
                    df_smallR, df2 = db.classify_by_paytype(
                        ["small_R"], ab_name=ab_id_name
                    )
                    df_list = df_smallR.to_dict(orient="records")  # ["pays"]
                    alternatives_list = []
                    values_list = []
                    for dict_df in df_list:
                        values_list.append(dict_df["pays"])
                        alternatives_list.append(dict_df["alternatives"])

                    # 根据 list1 进行排序，并重新生成已排序的 list2
                    sorted_lists_s = sorted(zip(alternatives_list, values_list))
                    alternatives_list_s, values_list_s = zip(*sorted_lists_s)

                    all_data["smallr_alt"] = alternatives_list_s
                    all_data["smallr_pays"] = values_list_s

                    data_smallr = pd.DataFrame(
                        {
                            "alternatives": alternatives_list,
                            "Pays": values_list,
                        }
                    )
                    self.plot_bar_chart(df=data_smallr, title="Small R")

            with col2:
                with st.container():
                    df_allR, df2 = db.classify_by_paytype([], ab_name=ab_id_name)
                    df_list = df2.to_dict(orient="records")  # ["pays"]
                    alternatives_list = []
                    values_list = []
                    for dict_df in df_list:
                        values_list.append(dict_df["all_pays"])
                        alternatives_list.append(dict_df["alternatives"])

                    data_all = pd.DataFrame(
                        {
                            "alternatives": alternatives_list,
                            "Pays": values_list,
                        }
                    )
                    fig = px.bar(
                        data_all,
                        x="alternatives",
                        y="Pays",
                        color="alternatives",
                        title="All",
                        log_y=False,
                    )
                    fig.update_layout(
                        showlegend=True,
                        xaxis_title=None,
                        yaxis_title="Pays",
                        xaxis={"categoryorder": "total ascending"},
                        hovermode="x unified",
                    )
                    fig.update_traces(hovertemplate="%{y:,.0f}<extra></extra>")
                    theme_plotly = None
                    st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

                with st.container():
                    x = all_data["bigr_alt"]
                    fig = go.Figure(go.Bar(x=x, y=all_data["bigr_pays"], name="BigR"))
                    fig.add_trace(go.Bar(x=x, y=all_data["midr_pays"], name="MidR"))
                    fig.add_trace(go.Bar(x=x, y=all_data["smallr_pays"], name="SmallR"))

                    fig.update_layout(barmode="stack", title_text="All Pay_type Pays")
                    fig.update_xaxes(categoryorder="total ascending")
                    # fig.show()
                    st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

    def plot_line_chart(
        self,
        df,
        x="date",
        y="usd",
        color="tag",
        custom_data=["tag"],
        title="Model Type Pays",
        yaxis_title="usd",
        log_y=False,
    ):
        theme_plotly = None  # None or streamlit
        # df = transactions_daily.query('Blockchain == @options').sort_values(['Date', 'Transactions'], ascending=[False, False])
        fig = px.line(
            df,
            x=x,
            y=y,
            color=color,
            custom_data=custom_data,
            title=title,
            log_y=log_y,
        )
        fig.update_layout(
            legend_title=None,
            xaxis_title=None,
            yaxis_title=yaxis_title,
            hovermode="x unified",
        )
        fig.update_traces(hovertemplate="%{customdata}: %{y:,.0f}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

    def plot_bar_chart(
        self,
        df,
        x="alternatives",
        y="Pays",
        color="alternatives",
        title="All",
        yaxis_title="Pays",
        log_y=False,
    ):
        theme_plotly = None  # None or streamlit
        fig = px.bar(
            df,
            x=x,
            y=y,
            color=color,
            title=title,
            log_y=log_y,
        )
        fig.update_layout(
            showlegend=True,
            xaxis_title=None,
            yaxis_title=yaxis_title,
            xaxis={"categoryorder": "total ascending"},
            hovermode="x unified",
        )
        fig.update_traces(hovertemplate="%{y:,.0f}<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, theme=theme_plotly)

    def calculate_annotation_stats(self, model):
        completed = 0
        in_progress = 0
        data_dir_path = Path(model.annotation_files_dir)

        for file_name in data_dir_path.glob("*.json"):
            with open(file_name, "r") as f:
                data = json.load(f)
                v = data["meta"]["version"]
                if v == "v0.1":
                    in_progress += 1
                else:
                    completed += 1
        total = completed + in_progress

        status_json = {
            "annotations": [
                {"completed": completed, "in_progress": in_progress, "total": total}
            ]
        }

        with open(model.status_file, "w") as f:
            json.dump(status_json, f, indent=2)

        return total, completed, in_progress
