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
cache_store = hirlite.Rlite("db/cache.db", encoding="utf8")


class Dashboard:
    class Model:
        pageTitle = "Dashboard"

        paysTitle = "今日/昨日总付费 $"

        inferenceTimeTitle = "Inference Time"

        altPaysTitle = "model/control总付费 $"

        dailyInferenceTitle = "model/control Lift ＄"

        accuracyTitle = "Mean Accuracy"

        titleModelEval = "## Evaluation Accuracy"
        titleInferencePerformance = "## Inference Performance"
        titleMidR = "## Mid R"
        titleBigR = "## Big R"
        titleSmallR = "## Small R"
        titleAllPlayers = "## All Players"

        status_file = "docs/status.json"
        annotation_files_dir = "docs/json"

    def view(self, model):
        # st.title(model.pageTitle)

        api_url = "https://katanaml-org-sparrow-ml.hf.space/api-inference/v1/sparrow-ml/statistics"
        json_data_inference = []
        response = requests.get(api_url)
        if response.status_code == 200:
            json_data_inference = response.json()
        else:
            print(
                f"Error: Unable to fetch data from the API (status code {response.status_code})"
            )

        api_url_t = "https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/statistics/training"
        json_data_training = []
        response_t = requests.get(api_url_t)
        if response_t.status_code == 200:
            json_data_training = response_t.json()
        else:
            print(
                f"Error: Unable to fetch data from the API (status code {response_t.status_code})"
            )

        api_url_e = "https://katanaml-org-sparrow-ml.hf.space/api-training/v1/sparrow-ml/statistics/evaluate"
        json_data_evaluate = []
        response_e = requests.get(api_url_e)
        if response_e.status_code == 200:
            json_data_evaluate = response_e.json()
        else:
            print(
                f"Error: Unable to fetch data from the API (status code {response_e.status_code})"
            )

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

                # calculate inference time average
                for i in range(0, len(json_data_inference)):
                    inference_time_avg = inference_time_avg + json_data_inference[i][0]
                inference_time_avg = round(
                    inference_time_avg / len(json_data_inference), 2
                )

                delta_time = 0
                if len(json_data_inference) > 3:
                    avg_time_last = (
                        json_data_inference[len(json_data_inference) - 1][0]
                        + json_data_inference[len(json_data_inference) - 2][0]
                        + json_data_inference[len(json_data_inference) - 3][0]
                    ) / 3

                    if avg_time_last > inference_time_avg:
                        delta_time = round(
                            100 - ((inference_time_avg * 100) / avg_time_last), 2
                        )
                    else:
                        delta_time = (
                            round(100 - ((avg_time_last * 100) / inference_time_avg), 2)
                            * -1
                        )

                st.metric(
                    label=model.inferenceTimeTitle,
                    value=str(inference_time_avg) + " s",
                    delta=str(delta_time) + "%",
                    delta_color="inverse",
                )

            with col5:
                models_unique = []
                models_dict = {}
                for i in range(0, len(json_data_evaluate)):
                    if json_data_evaluate[i][3] not in models_unique:
                        models_unique.append(json_data_evaluate[i][3])
                        models_dict[json_data_evaluate[i][3]] = json_data_evaluate[i][
                            1
                        ]["mean_accuracy"]

                avg_accuracy = 0
                for key, value in models_dict.items():
                    avg_accuracy = avg_accuracy + value
                avg_accuracy = round(avg_accuracy / len(models_dict), 2)

                if len(models_unique) > 3:
                    # calculate average accuracy for last 3 values
                    avg_accuracy_last = 0
                    for i in range(1, 4):
                        avg_accuracy_last = (
                            avg_accuracy_last
                            + models_dict[models_unique[len(models_unique) - i]]
                        )
                    avg_accuracy_last = round(avg_accuracy_last / 3, 2)
                else:
                    avg_accuracy_last = avg_accuracy

                if avg_accuracy_last > avg_accuracy:
                    delta_accuracy = round(
                        100 - ((avg_accuracy * 100) / avg_accuracy_last), 2
                    )
                else:
                    delta_accuracy = (
                        round(100 - ((avg_accuracy_last * 100) / avg_accuracy), 2) * -1
                    )

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
                st.write(model.titleInferencePerformance)

                models_dict = {}

                models = []
                for i in range(0, len(json_data_inference)):
                    models.append(json_data_inference[i][3])

                models_unique = []
                for item in models:
                    if item not in models_unique:
                        models_unique.append(item)

                for i, key in enumerate(models_unique):
                    models_dict[key] = []

                for i in range(0, len(json_data_inference)):
                    models_dict[json_data_inference[i][3]].append(
                        round(json_data_inference[i][0])
                    )

                data = pd.DataFrame(models_dict)
                st.line_chart(data)

            with col2:
                st.write(model.titleModelEval)

                models_unique = []
                models_dict = {}
                for i in range(0, len(json_data_evaluate)):
                    if json_data_evaluate[i][3] not in models_unique:
                        models_unique.append(json_data_evaluate[i][3])
                        models_dict[json_data_evaluate[i][3]] = json_data_evaluate[i][
                            1
                        ]["accuracies"]

                data = pd.DataFrame(models_dict)
                st.line_chart(data)

        st.markdown("---")

        with st.container():
            col1, col2, col3 = st.columns(3)

            with col1:
                with st.container():
                    st.write(model.titleBigR)
                    df_bigR,df2 = db.classify_by_paytype(["big_R"], ab_name=ab_id_name)
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

                    df_midR,df2 = db.classify_by_paytype(["mid_R"], ab_name=ab_id_name)
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

                    df_smallR,df2 = db.classify_by_paytype(["small_R"], ab_name=ab_id_name)
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

            df_allR,df2 = db.classify_by_paytype([], ab_name=ab_id_name)
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
