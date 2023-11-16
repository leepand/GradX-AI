import streamlit as st
import numpy as np
import pandas as pd
import json
import altair as alt
from pathlib import Path
import requests
from datetime import datetime
import hirlite


from utils import get_bj_day_time, get_yestoday_bj
from data import Database

experiments_file = "docs/experiments.json"
model_type_file = "docs/modeltypes.json"
cache_store = hirlite.Rlite("db/cache.db", encoding="utf8")


class Dashboard:
    class Model:
        pageTitle = "Dashboard"

        paysTitle = "今日/昨日总付费 $"

        inferenceTimeTitle = "Inference Time"

        altPaysTitle = "model/control总付费 $"

        dailyInferenceTitle = "model/control Lift ＄"

        accuracyTitle = "Mean Accuracy"

        titleModelTypeAvgPays = "## Model Type Avg Pays"
        titleModelTypePays = "## Model Type Pays"
        titleMidR = "## Mid R"
        titleBigR = "## Big R"
        titleSmallR = "## Small R"
        titleAllPlayers = "## All Players"

        status_file = "docs/status.json"
        annotation_files_dir = "docs/json"

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
                st.write(f"### Data updated time: `{dt_now}`")

            # with open('style.css') as f:
            #    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            st.sidebar.header("Modelpayboard `v.1.0`")
            st.sidebar.subheader("Experiments")
            process_data = st.sidebar.selectbox(
                "Update Real-Time Data",
                ("no", "yes"),
            )
            ab_id_name = st.sidebar.selectbox(
                "Display by experiment",
                experiment_ids,
            )
            filyer_pays = st.sidebar.slider("Filter user pays", 0, 20000, 0)
            db = Database(filter_big_user=filyer_pays)
            if process_data == "yes":
                db.get_realdata_frombq()
                db.get_model_type_frombq(ab_name_list=experiment_ids)
                dt_now = get_bj_day_time()
                cache_store.set("latest_time", dt_now)
                cache_store.set("filter_pays", str(filyer_pays))

            today_all_pays, yes_today_all_pays = db.get_allpays(ab_id_name)
            _filter_pays = cache_store.get("filter_pays")
            if _filter_pays is None:
                filter_pays_selected = filyer_pays
            else:
                filter_pays_selected = str(_filter_pays)

            if float(filter_pays_selected) > 0:
                st.write(f"剔除当日总付费超过`{filter_pays_selected}美金`的玩家，实验: `{ab_id_name}`")
            else:
                st.write(f"全量玩家，实验: `{ab_id_name}`")
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
            delta_alt_pays = round((_model_val / _control_val - 1) * 100, 2)
            with col2:
                model_val = round(_model_val / 10000, 2)
                control_val = round(_control_val / 10000, 2)
                # delta_alt_pays = round((model_val / control_val - 1) * 100, 2)

                st.metric(
                    label=model.altPaysTitle,
                    value=str(model_val) + "W",
                    delta=f"{delta_alt_pays}% ({control_val}W)",
                )

            with col3:
                model_gap = round((_model_val - _control_val) / 10000, 3)
                st.metric(
                    label=model.dailyInferenceTitle,
                    value=str(model_gap) + "W",
                    delta=str(delta_alt_pays) + "%",
                )

            with col4:
                inference_time_avg = 0
                delta_time = 0
                # calculate inference time average

                st.metric(
                    label=model.inferenceTimeTitle,
                    value=str(inference_time_avg) + " s",
                    delta=str(delta_time) + "%",
                    delta_color="inverse",
                )

            with col5:
                avg_accuracy = 0.98
                delta_accuracy = 0

                st.metric(
                    label=model.accuracyTitle,
                    value=avg_accuracy,
                    delta=str(delta_accuracy) + "%",
                    delta_color="inverse",
                )

            st.markdown("---")

        with st.container():
            col1, col2 = st.columns(2)

            with col1:
                st.write(model.titleModelTypePays)
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
                # st.write(model_type_list)
                # st.dataframe(df_usd)
                df_transposed = df_usd.pivot(index="date", columns="tag", values="usd")
                st.line_chart(df_transposed)

            with col2:
                st.write(model.titleModelTypeAvgPays)
                df_avg_user_usd.dropna(inplace=True)
                df_transposeg_avt = df_avg_user_usd.pivot(index="date", columns="tag", values="avg_user_usd")
                st.line_chart(df_transposeg_avt)

        st.markdown("---")

        with st.container():
            col1, col2, col3 = st.columns(3)

            with col1:
                with st.container():
                    st.write(model.titleBigR)
                    df_bigR, df2 = db.classify_by_paytype(["big_R"], ab_name=ab_id_name)
                    df_list = df_bigR.to_dict(orient="records")  # ["pays"]
                    alternatives_list = []
                    values_list = []
                    for dict_df in df_list:
                        values_list.append(dict_df["pays"])
                        alternatives_list.append(dict_df["alternatives"])

                    data = pd.DataFrame(
                        {
                            "alternatives": alternatives_list,
                            "Pays": values_list,
                        }
                    )

                    # Create a horizontal bar chart
                    chart = (
                        alt.Chart(data)
                        .mark_bar()
                        .encode(
                            x="Pays:Q",
                            y=alt.Y("alternatives:N", sort="-x"),
                            color=alt.Color("alternatives:N", legend=None),
                        )
                    )

                    st.altair_chart(chart)
            with col2:
                with st.container():
                    st.write(model.titleMidR)

                    df_midR, df2 = db.classify_by_paytype(["mid_R"], ab_name=ab_id_name)
                    df_list = df_midR.to_dict(orient="records")  # ["pays"]
                    alternatives_list = []
                    values_list = []
                    for dict_df in df_list:
                        values_list.append(dict_df["pays"])
                        alternatives_list.append(dict_df["alternatives"])

                    data = pd.DataFrame(
                        {
                            "alternatives": alternatives_list,
                            "Pays": values_list,
                        }
                    )

                    # Create a horizontal bar chart
                    chart = (
                        alt.Chart(data)
                        .mark_bar()
                        .encode(
                            x="Pays:Q",
                            y=alt.Y("alternatives:N", sort="-x"),
                            color=alt.Color("alternatives:N", legend=None),
                        )
                    )

                    st.altair_chart(chart)
            with col3:
                with st.container():
                    st.write(model.titleSmallR)

                    df_smallR, df2 = db.classify_by_paytype(
                        ["small_R"], ab_name=ab_id_name
                    )
                    df_list = df_smallR.to_dict(orient="records")  # ["pays"]
                    alternatives_list = []
                    values_list = []
                    for dict_df in df_list:
                        values_list.append(dict_df["pays"])
                        alternatives_list.append(dict_df["alternatives"])

                    data = pd.DataFrame(
                        {
                            "alternatives": alternatives_list,
                            "Pays": values_list,
                        }
                    )

                    # Create a horizontal bar chart
                    chart = (
                        alt.Chart(data)
                        .mark_bar()
                        .encode(
                            x="Pays:Q",
                            y=alt.Y("alternatives:N", sort="-x"),
                            color=alt.Color("alternatives:N", legend=None),
                        )
                    )

                    st.altair_chart(chart)

        st.markdown("---")

        with st.container():
            st.write(model.titleAllPlayers)

            df_allR, df2 = db.classify_by_paytype([], ab_name=ab_id_name)
            df_list = df2.to_dict(orient="records")  # ["pays"]
            alternatives_list = []
            values_list = []
            for dict_df in df_list:
                values_list.append(dict_df["all_pays"])
                alternatives_list.append(dict_df["alternatives"])

            data = pd.DataFrame(
                {
                    "alternatives": alternatives_list,
                    "Pays": values_list,
                }
            )

            # Create a horizontal bar chart
            chart = (
                alt.Chart(data)
                .mark_bar()
                .encode(
                    x="Pays:Q",
                    y=alt.Y("alternatives:N", sort="-x"),
                    color=alt.Color("alternatives:N", legend=None),
                )
            )

            st.altair_chart(chart)

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
