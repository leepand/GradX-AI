import streamlit as st
import os
import time
from PIL import Image
import math
from streamlit_sparrow_labeling import st_sparrow_labeling
import requests
from config import settings
import json
from streamlit_extras.colored_header import colored_header
from streamlit_ace import st_ace, THEMES
from client import HTTPClient, method_form, call_method, ExecutionError
import pickle
import hirlite

model_file = "docs/models.json"
cache_store = hirlite.Rlite("db/cache.db", encoding="utf8")


THEMES = [
    "ambiance",
    "chaos",
    "chrome",
    "clouds",
    "clouds_midnight",
    "cobalt",
    "crimson_editor",
    "dawn",
    "dracula",
    "dreamweaver",
    "eclipse",
    "github",
    "gob",
    "gruvbox",
    "idle_fingers",
    "iplastic",
    "katzenmilch",
    "kr_theme",
    "kuroir",
    "merbivore",
    "merbivore_soft",
    "mono_industrial",
    "monokai",
    "nord_dark",
    "pastel_on_dark",
    "solarized_dark",
    "solarized_light",
    "sqlserver",
    "terminal",
    "textmate",
    "tomorrow",
    "tomorrow_night",
    "tomorrow_night_blue",
    "tomorrow_night_bright",
    "tomorrow_night_eighties",
    "twilight",
    "vibrant_ink",
    "xcode",
]


# @st.cache_resource
def get_client(server_host="1.31.24.138", server_port=5001):
    return HTTPClient(host=server_host, port=int(server_port))


def save_json_to_file(json_string, file_path):
    with open(file_path, "w") as file:
        # json_string1=json_dumps_data(json_string)
        file.write(json_string)


def load_json_from_file(file_path):
    with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as file:
        json_data = json.load(file, strict=False)
        return json_data


def json_dumps_data(data):
    _data = json.dumps(
        data,
        separators=(",", ":"),
    )
    return _data


PIXELS_PER_LINE = 27
INDENT = 8


class DataInference:
    class Model:
        # pageTitle = "Data Inference"
        initial_msg = "Please upload a file for inference"

        upload_help = "Upload a file to extract data from it"
        upload_button_text = "Upload"
        upload_button_text_desc = "Choose a file"

        extract_data = "Extract Data"

        model_in_use = "donut"

        img_file = None
        models_file = "docs/models.json"

        def set_image_file(self, img_file):
            st.session_state["img_file"] = img_file

        def get_image_file(self):
            if "img_file" not in st.session_state:
                return None
            return st.session_state["img_file"]

        data_result = None

        def set_data_result(self, data_result):
            st.session_state["data_result"] = data_result

        def get_data_result(self):
            if "data_result" not in st.session_state:
                return None
            return st.session_state["data_result"]

    def view(self, model):
        # st.title(model.pageTitle)
        with open(model_file, "r") as f:
            models_json = json.load(f)
        models = models_json["models"]
        model_name_list = []
        if len(models) < 1:
            st.error("Please setup first at setup page!")

        model_info = {}
        for _model in models:
            model_name = _model["name"]
            if model_name in model_info:
                model_info[model_name].append(_model)
            else:
                model_info[model_name] = [_model]
        model_name_list = list(model_info.keys())
        with st.sidebar:
            st.markdown("---")
            st.sidebar.header("Model Inference `v.1.0`")

            st.sidebar.subheader("Model Env")
            model_env = st.sidebar.selectbox("Display by env", ("Dev", "Prod"))
            st.sidebar.subheader("Model Name")
            if len(model_name_list) > 0:
                model_name = st.sidebar.selectbox("Models", model_name_list)
            else:
                model_name = st.sidebar.selectbox("Models", ("no model"))
            st.sidebar.subheader("Model Server")
            model_server = st.sidebar.selectbox(
                "Servers", ("recomserver", "rewardserver")
            )
        model_base_info = model_info[model_name]
        for index, x_i in enumerate(model_base_info):
            if x_i["env"].lower() == model_env.lower():
                model_setup_info = x_i
                break
        # st.write(model_setup_info)
        try:
            server_name = model_setup_info[model_server]
            dataform_server = str(server_name).strip("'<>() ").replace("'", '"')
            ports = json.loads(dataform_server)["ports"]
        except:
            ports = model_setup_info[model_server]["ports"]
        client = get_client(server_port=ports[0])
        methods = ["predict"]
        # tabs = st.tabs(methods)

        tabs = ["predict"]
        for method_name, tab in zip(methods, tabs):
            with st.container():
                # with tab:
                # tab.header(method_name)
                # st.header(method_name)
                _, colT21 = st.columns([3, 7])
                with colT21:
                    st.title("Model Inference")
                method = call_method(client=client, method_name="predict")

                colored_header(
                    label="Model Input",
                    description="Use this app to reformat and edit json files",
                    color_name="violet-70",
                )
                input_data_template = {
                    "uid": 1,
                    "request_id": 2.0,
                    "feature1": "abc",
                    "feature2": {"a": 3},
                    "feature3": [4, 5.0, "def"],
                }

                json_file = st.file_uploader(
                    "Upload JSON Data",
                    type=["json"],
                )

                col1, col2 = st.columns(2)
                sep1 = col1.selectbox("Separators (1)", [",", ":", "="])
                sep2 = col2.selectbox("Separators (2)", [":", ",", "="])
                indents = col1.number_input("Indentation", min_value=1, value=4)
                sort_keys = st.checkbox("Sort Keys", True)
                theme_key = st.checkbox("Dark Theme", True)
                if theme_key:
                    theme_app = "solarized_dark"
                else:
                    theme_app = THEMES[3]
                update_model_file = st.checkbox("Update data", False)
                if json_file:
                    # with open(json_file) as f:
                    temp = json.load(json_file)

                    formatted = json.dumps(
                        temp,
                        indent=indents,
                        sort_keys=sort_keys,
                        separators=(f"{sep1}", f"{sep2}"),
                    )

                    content = st_ace(
                        value=formatted,
                        language="markdown",
                        # theme="solarized_dark",
                        theme=THEMES[3],
                        keybinding="vscode",
                        min_lines=20,
                        max_lines=None,
                        font_size=14,
                        tab_size=4,
                        wrap=False,
                        show_gutter=True,
                        show_print_margin=False,
                        readonly=False,
                        annotations=None,
                    )

                    st.download_button(
                        label="Download formatted JSON",
                        data=content,
                        file_name=f"{model_name}_{model_server}.json",
                        mime="json",
                    )
                    data = content
                else:
                    # st.warning("Upload a .json to get started")
                    # data = st.text_area("data", value=input_data_template)
                    # with open(json_file) as f:
                    data_key = f"data_{model_server}"
                    data_template = model_setup_info.get(data_key)
                    data_key_cache = f"{model_name}:{model_server}:{model_env}"
                    data_example = cache_store.get(data_key_cache)
                    if data_template is None:
                        if data_example is None:
                            temp = input_data_template  # json.load(json_file)
                        else:
                            temp = pickle.loads(data_example)
                    else:
                        try:
                            temp = json.loads(data_template)  # [model_server]
                        except:
                            if data_example is None:
                                temp = input_data_template
                            else:
                                temp = pickle.loads(data_example)
                    if isinstance(temp,dict):
                        formatted = json.dumps(
                        temp,
                        indent=indents,
                        sort_keys=sort_keys,
                        separators=(f"{sep1}", f"{sep2}"),
                    )
                    else:
                        formatted = temp

                    content = st_ace(
                        value=formatted,
                        language="markdown",
                        # theme="solarized_dark",
                        theme=theme_app,
                        keybinding="vscode",
                        min_lines=20,
                        max_lines=None,
                        font_size=14,
                        tab_size=4,
                        wrap=False,
                        show_gutter=True,
                        show_print_margin=False,
                        readonly=False,
                        annotations=None,
                    )
                    st.download_button(
                        label="Download formatted JSON",
                        data=content,
                        file_name=f"{model_name}_{model_server}.json",
                        mime="json",
                    )
                    data = content

                with st.form(key=method_name):
                    x = f"model service ports: {ports},server: {model_server}"
                    st.write(x)
                    submit_button = st.form_submit_button(label="Submit")
                    if submit_button:
                        st.write(data)
                        if isinstance(data, dict):
                            loaded_json = data
                        else:

                            valid_json = data  # .replace("'", '"')
                            dataform = str(valid_json).strip("'<>() ").replace("'", '"')
                            try:
                                loaded_json = json.loads(r"{}".format(valid_json))
                            except:
                                loaded_json = eval(valid_json)
                                # loaded_json = json.loads(json.dumps(_dataform))

                        # st.json(data)
                        arg_values = method(
                            payload=loaded_json, name=f"predict/{model_server}"
                        )
                        st.markdown("---")
                        with st.spinner("Processing..."):
                            if update_model_file:
                                data_key = f"{model_name}:{model_server}:{model_env}"
                                cache_store.set(data_key, pickle.dumps(loaded_json))
                            st.write("Response:")
                            # st.json(arg_values)
                            result = f"""
                            ```python
                            {arg_values}
                            ```
                            """
                            result = json.dumps(
                                arg_values,
                                indent=indents,
                                sort_keys=sort_keys,
                                separators=(f"{sep1}", f"{sep2}"),
                            )

                            st.markdown("```json\n" + result + "\n```")

    def render_results(self, model):
        with st.form(key="results_form"):
            button_placeholder = st.empty()

            submit = button_placeholder.form_submit_button(
                model.extract_data, type="primary"
            )
            if "inference_error" in st.session_state:
                st.error(st.session_state.inference_error)
                del st.session_state.inference_error

            if submit:
                button_placeholder.empty()

                api_url = "https://katanaml-org-sparrow-ml.hf.space/api-inference/v1/sparrow-ml/inference"
                file_path = model.get_image_file()

                with open(file_path, "rb") as file:
                    model_in_use = model.model_in_use
                    sparrow_key = settings.sparrow_key

                    # Prepare the payload
                    files = {"file": (file.name, file, "image/jpeg")}

                    data = {
                        "image_url": "",
                        "model_in_use": model_in_use,
                        "sparrow_key": sparrow_key,
                    }

                    with st.spinner("Extracting data from document..."):
                        response = requests.post(
                            api_url, data=data, files=files, timeout=180
                        )
                if response.status_code != 200:
                    print("Request failed with status code:", response.status_code)
                    print("Response:", response.text)

                    st.session_state[
                        "inference_error"
                    ] = "Error extracting data from document"
                    st.experimental_rerun()

                model.set_data_result(response.text)

                # Display JSON data in Streamlit
                st.markdown("---")
                st.json(response.text)

                # replace file extension to json
                file_path = file_path.replace(".jpg", ".json")
                with open(file_path, "w") as f:
                    json.dump(response.text, f, indent=2)

                st.experimental_rerun()
            else:
                if model.get_data_result() is not None:
                    st.markdown("---")
                    st.json(model.get_data_result())
