import streamlit as st
import json
import pandas as pd
from tools import agstyler
from tools.agstyler import PINLEFT
from toolbar import component_toolbar_buttons


class Setup:
    class Model:
        header1 = "Experiments"
        header2 = "Models"
        header3 = "ModelTypes"
        header4 = "FeatureStore"
        experiments_file = "docs/experiments.json"
        models_file = "docs/models.json"
        model_type_file = "docs/modeltypes.json"
        feature_store_file = "docs/featurestore.json"

    def view(self, model):
        tab = st.radio(
            "Select",
            ["Experiments", "ModelTypes", "Models", "FeatureStore"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if tab == "Experiments":
            st.title(model.header1)
            self.setup_experiments(model)
        elif tab == "Models":
            st.title(model.header2)
            self.setup_models(model)
        elif tab == "ModelTypes":
            st.title(model.header3)
            self.setup_modetypes(model)
        elif tab == "FeatureStore":
            st.title(model.header4)
            self.setup_feature_store(model)

    def setup_modetypes(self, model):
        self.action_event = False
        if "action" not in st.session_state:
            st.session_state["action"] = None

        with open(model.model_type_file, "r") as f:
            modeltypes_json = json.load(f)

        modeltypes = modeltypes_json["modeltypes"]

        data = []
        for modeltype in modeltypes:
            data.append(
                {
                    "id": modeltype["id"],
                    "name": modeltype["name"],
                    "description": modeltype["description"],
                }
            )
        self.df = pd.DataFrame(data)

        formatter = {
            "id": ("ID", {"hide": True}),
            "name": ("Label", {**PINLEFT, "editable": True}),
            "description": ("Description", {**PINLEFT, "editable": True}),
        }

        def run_component(props):
            value = component_toolbar_buttons(key="toolbar_buttons_labels", **props)
            return value

        def handle_event(value):
            if value is not None:
                if "action_timestamp" not in st.session_state:
                    self.action_event = True
                    st.session_state["action_timestamp"] = value["timestamp"]
                else:
                    if st.session_state["action_timestamp"] != value["timestamp"]:
                        self.action_event = True
                        st.session_state["action_timestamp"] = value["timestamp"]
                    else:
                        self.action_event = False

            if value is not None and value["action"] == "create" and self.action_event:
                if st.session_state["action"] != "delete":
                    max_id = self.df["id"].max()
                    self.df.loc[-1] = [max_id + 1, "", ""]  # adding a row
                    self.df.index = self.df.index + 1  # shifting index
                    self.df.sort_index(inplace=True)
                    st.session_state["action"] = "create"
            elif (
                value is not None and value["action"] == "delete" and self.action_event
            ):
                if (
                    st.session_state["action"] != "delete"
                    and st.session_state["action"] != "create"
                ):
                    rows = st.session_state["selected_rows"]
                    if len(rows) > 0:
                        idx = rows[0]["_selectedRowNodeInfo"]["nodeRowIndex"]
                        self.df.drop(self.df.index[idx], inplace=True)
                        self.df.reset_index(drop=True, inplace=True)
                    st.session_state["action"] = "delete"
            elif value is not None and value["action"] == "save" and self.action_event:
                st.session_state["action"] = "save"

        props = {
            "buttons": {
                "create": False,
                "delete": False,
                "save": False,
            }
        }

        handle_event(run_component(props))

        if st.session_state["action"] == "save" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]
            st.session_state["response"] = None

        if st.session_state["action"] == "create" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]

        if st.session_state["action"] == "delete" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]

        response = agstyler.draw_grid(
            self.df,
            formatter=formatter,
            fit_columns=True,
            pagination_size=10,
            selection="single",
            use_checkbox=False,
        )

        rows = response["selected_rows"]
        st.session_state["selected_rows"] = rows

        if st.session_state["action"] == "create" and self.action_event:
            st.session_state["response"] = response["data"]
        elif st.session_state["action"] == "delete" and self.action_event:
            st.session_state["response"] = response["data"]
        elif st.session_state["action"] == "save" and self.action_event:
            data = response["data"].values.tolist()
            rows = []
            for row in data:
                rows.append({"id": row[0], "name": row[1], "description": row[2]})

            modeltypes_json["modeltypes"] = rows
            with open(model.model_type_file, "w") as f:
                json.dump(modeltypes_json, f, indent=2)

    def setup_experiments(self, model):
        self.action_event = False
        if "action" not in st.session_state:
            st.session_state["action"] = None

        with open(model.experiments_file, "r") as f:
            experiments_json = json.load(f)

        experiments = experiments_json["experiments"]

        data = []
        for experiment in experiments:
            data.append(
                {
                    "id": experiment["id"],
                    "name": experiment["name"],
                    "description": experiment["description"],
                }
            )
        self.df = pd.DataFrame(data)

        formatter = {
            "id": ("ID", {"hide": True}),
            "name": ("Label", {**PINLEFT, "editable": True}),
            "description": ("Description", {**PINLEFT, "editable": True}),
        }

        def run_component(props):
            value = component_toolbar_buttons(key="toolbar_buttons_labels", **props)
            return value

        def handle_event(value):
            if value is not None:
                if "action_timestamp" not in st.session_state:
                    self.action_event = True
                    st.session_state["action_timestamp"] = value["timestamp"]
                else:
                    if st.session_state["action_timestamp"] != value["timestamp"]:
                        self.action_event = True
                        st.session_state["action_timestamp"] = value["timestamp"]
                    else:
                        self.action_event = False

            if value is not None and value["action"] == "create" and self.action_event:
                if st.session_state["action"] != "delete":
                    max_id = self.df["id"].max()
                    self.df.loc[-1] = [max_id + 1, "", ""]  # adding a row
                    self.df.index = self.df.index + 1  # shifting index
                    self.df.sort_index(inplace=True)
                    st.session_state["action"] = "create"
            elif (
                value is not None and value["action"] == "delete" and self.action_event
            ):
                if (
                    st.session_state["action"] != "delete"
                    and st.session_state["action"] != "create"
                ):
                    rows = st.session_state["selected_rows"]
                    if len(rows) > 0:
                        idx = rows[0]["_selectedRowNodeInfo"]["nodeRowIndex"]
                        self.df.drop(self.df.index[idx], inplace=True)
                        self.df.reset_index(drop=True, inplace=True)
                    st.session_state["action"] = "delete"
            elif value is not None and value["action"] == "save" and self.action_event:
                st.session_state["action"] = "save"

        props = {
            "buttons": {
                "create": False,
                "delete": False,
                "save": False,
            }
        }

        handle_event(run_component(props))

        if st.session_state["action"] == "save" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]
            st.session_state["response"] = None

        if st.session_state["action"] == "create" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]

        if st.session_state["action"] == "delete" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]

        response = agstyler.draw_grid(
            self.df,
            formatter=formatter,
            fit_columns=True,
            pagination_size=10,
            selection="single",
            use_checkbox=False,
        )

        rows = response["selected_rows"]
        st.session_state["selected_rows"] = rows

        if st.session_state["action"] == "create" and self.action_event:
            st.session_state["response"] = response["data"]
        elif st.session_state["action"] == "delete" and self.action_event:
            st.session_state["response"] = response["data"]
        elif st.session_state["action"] == "save" and self.action_event:
            data = response["data"].values.tolist()
            rows = []
            for row in data:
                rows.append({"id": row[0], "name": row[1], "description": row[2]})

            experiments_json["experiments"] = rows
            with open(model.experiments_file, "w") as f:
                json.dump(experiments_json, f, indent=2)

    def setup_models(self, model):
        self.action_event = False
        if "action" not in st.session_state:
            st.session_state["action"] = None

        with open(model.models_file, "r") as f:
            models_json = json.load(f)

        models = models_json["models"]

        data = []
        for _model in models:
            data.append(
                {
                    "id": _model["id"],
                    "name": _model["name"],
                    "env": _model["env"],
                    "recomserver": _model["recomserver"],
                    "rewardserver": _model["rewardserver"],
                    "data_recomserver": _model["data_recomserver"],
                    "data_rewardserver": _model["data_rewardserver"],
                    "description": _model["description"],
                }
            )
        self.df = pd.DataFrame(data)

        formatter = {
            "id": ("ID", {"hide": True}),
            "name": ("Model", {**PINLEFT, "editable": True}),
            "env": ("Env", {**PINLEFT, "editable": True}),
            "recomserver": ("Recomserver", {**PINLEFT, "editable": True}),
            "rewardserver": ("Rewardserver", {**PINLEFT, "editable": True}),
            "data_recomserver": ("DataRecom", {**PINLEFT, "editable": True}),
            "data_rewardserver": ("DataReward", {**PINLEFT, "editable": True}),
            "description": ("Description", {**PINLEFT, "editable": True}),
        }

        def run_component(props):
            value = component_toolbar_buttons(key="toolbar_buttons_groups", **props)
            return value

        def handle_event(value):
            if value is not None:
                if "action_timestamp" not in st.session_state:
                    self.action_event = True
                    st.session_state["action_timestamp"] = value["timestamp"]
                else:
                    if st.session_state["action_timestamp"] != value["timestamp"]:
                        self.action_event = True
                        st.session_state["action_timestamp"] = value["timestamp"]
                    else:
                        self.action_event = False

            if value is not None and value["action"] == "create" and self.action_event:
                if st.session_state["action"] != "delete":
                    try:
                        max_id = self.df["id"].max()
                    except:
                        max_id = -1
                    self.df.loc[-1] = [
                        max_id + 1,
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                    ]  # adding a row
                    self.df.index = self.df.index + 1  # shifting index
                    self.df.sort_index(inplace=True)
                    st.session_state["action"] = "create"
            elif (
                value is not None and value["action"] == "delete" and self.action_event
            ):
                if (
                    st.session_state["action"] != "delete"
                    and st.session_state["action"] != "create"
                ):
                    rows = st.session_state["selected_rows"]
                    if len(rows) > 0:
                        idx = rows[0]["_selectedRowNodeInfo"]["nodeRowIndex"]
                        self.df.drop(self.df.index[idx], inplace=True)
                        self.df.reset_index(drop=True, inplace=True)
                    st.session_state["action"] = "delete"
            elif value is not None and value["action"] == "save" and self.action_event:
                st.session_state["action"] = "save"

        props = {
            "buttons": {
                "create": False,
                "delete": False,
                "save": False,
            }
        }

        handle_event(run_component(props))

        if st.session_state["action"] == "save" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]
            st.session_state["response"] = None

        if st.session_state["action"] == "create" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]

        if st.session_state["action"] == "delete" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]

        response = agstyler.draw_grid(
            self.df,
            formatter=formatter,
            fit_columns=True,
            pagination_size=10,
            selection="single",
            use_checkbox=False,
        )

        rows = response["selected_rows"]
        st.session_state["selected_rows"] = rows

        if st.session_state["action"] == "create" and self.action_event:
            st.session_state["response"] = response["data"]
        elif st.session_state["action"] == "delete" and self.action_event:
            st.session_state["response"] = response["data"]
        elif st.session_state["action"] == "save" and self.action_event:
            data = response["data"].values.tolist()
            rows = []
            for row in data:
                rows.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "env": row[2],
                        "recomserver": row[3],
                        "rewardserver": row[4],
                        "data_recomserver": row[5],
                        "data_rewardserver": row[6],
                        "description": row[7],
                    }
                )

            models_json["models"] = rows
            with open(model.models_file, "w") as f:
                json.dump(models_json, f, indent=2)

    def setup_feature_store(self, model):
        self.action_event = False
        if "action" not in st.session_state:
            st.session_state["action"] = None

        with open(model.feature_store_file, "r") as f:
            features_json = json.load(f)

        features = features_json["features"]

        data = []
        for _feature in features:
            data.append(
                {
                    "id": _feature["id"],
                    "name": _feature["name"],
                    "owner": _feature["owner"],
                    "db_name": _feature["db_name"],
                    "model_name": _feature["model_name"],
                    "exp_list": _feature["exp_list"],
                    "data": _feature["data"],
                    "description": _feature["description"],
                }
            )
        self.df = pd.DataFrame(data)

        formatter = {
            "id": ("ID", {"hide": True}),
            "name": ("Model", {**PINLEFT, "editable": True}),
            "owner": ("Owner", {**PINLEFT, "editable": True}),
            "db_name": ("DB_Name", {**PINLEFT, "editable": True}),
            "model_name": ("Model_name", {**PINLEFT, "editable": True}),
            "exp_list": ("Experiments", {**PINLEFT, "editable": True}),
            "data": ("Data", {**PINLEFT, "editable": True}),
            "description": ("Description", {**PINLEFT, "editable": True}),
        }

        def run_component(props):
            value = component_toolbar_buttons(key="toolbar_buttons_groups", **props)
            return value

        def handle_event(value):
            if value is not None:
                if "action_timestamp" not in st.session_state:
                    self.action_event = True
                    st.session_state["action_timestamp"] = value["timestamp"]
                else:
                    if st.session_state["action_timestamp"] != value["timestamp"]:
                        self.action_event = True
                        st.session_state["action_timestamp"] = value["timestamp"]
                    else:
                        self.action_event = False

            if value is not None and value["action"] == "create" and self.action_event:
                if st.session_state["action"] != "delete":
                    try:
                        max_id = self.df["id"].max()
                    except:
                        max_id = -1
                    self.df.loc[-1] = [
                        max_id + 1,
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                    ]  # adding a row
                    self.df.index = self.df.index + 1  # shifting index
                    self.df.sort_index(inplace=True)
                    st.session_state["action"] = "create"
            elif (
                value is not None and value["action"] == "delete" and self.action_event
            ):
                if (
                    st.session_state["action"] != "delete"
                    and st.session_state["action"] != "create"
                ):
                    rows = st.session_state["selected_rows"]
                    if len(rows) > 0:
                        idx = rows[0]["_selectedRowNodeInfo"]["nodeRowIndex"]
                        self.df.drop(self.df.index[idx], inplace=True)
                        self.df.reset_index(drop=True, inplace=True)
                    st.session_state["action"] = "delete"
            elif value is not None and value["action"] == "save" and self.action_event:
                st.session_state["action"] = "save"

        props = {
            "buttons": {
                "create": False,
                "delete": False,
                "save": False,
            }
        }

        handle_event(run_component(props))

        if st.session_state["action"] == "save" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]
            st.session_state["response"] = None

        if st.session_state["action"] == "create" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]

        if st.session_state["action"] == "delete" and "response" in st.session_state:
            if st.session_state["response"] is not None:
                self.df = st.session_state["response"]

        response = agstyler.draw_grid(
            self.df,
            formatter=formatter,
            fit_columns=True,
            pagination_size=10,
            selection="single",
            use_checkbox=False,
        )

        rows = response["selected_rows"]
        st.session_state["selected_rows"] = rows

        if st.session_state["action"] == "create" and self.action_event:
            st.session_state["response"] = response["data"]
        elif st.session_state["action"] == "delete" and self.action_event:
            st.session_state["response"] = response["data"]
        elif st.session_state["action"] == "save" and self.action_event:
            data = response["data"].values.tolist()
            rows = []
            for row in data:
                rows.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "owner": row[2],
                        "db_name": row[3],
                        "model_name": row[4],
                        "exp_list": row[5],
                        "data": row[6],
                        "description": row[7],
                    }
                )

            features_json["features"] = rows
            with open(model.feature_store_file, "w") as f:
                json.dump(features_json, f, indent=2)
