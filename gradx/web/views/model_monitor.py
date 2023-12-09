import streamlit as st

import json
import math
import os
from natsort import natsorted
from tools import agstyler

import sqlite3
import streamlit_toggle as tog
from pathlib import Path
from streamlit_ace import st_ace, KEYBINDINGS, LANGUAGES, THEMES

from tools.agstyler import PINLEFT
import pandas as pd
from toolbar_main import component_toolbar_main
from st_aggrid import AgGrid
from utils import create_connection


def upload_data():
    st.markdown("# Upload Data")
    sqlite_dbs = [file for file in os.listdir(".") if file.endswith(".db")]
    db_filename = st.selectbox("Database", sqlite_dbs)
    table_name = st.text_input("Table Name to Insert")
    conn = create_connection(db_filename)
    uploaded_file = st.file_uploader("Choose a file")
    upload = st.button("Create Table")
    if upload:
        # read csv
        try:
            df = pd.read_csv(uploaded_file)
            df.to_sql(name=table_name, con=conn)
            st.write("Data uploaded successfully. These are the first 5 rows.")
            st.dataframe(df.head(5))

        except Exception as e:
            st.write(e)


def create_database():
    st.markdown("# Create Database")

    st.info(
        """A database in SQLite is just a file on same server. 
        By convention their names always must end in .db"""
    )

    db_filename = st.text_input("Database Name")
    create_db = st.button("Create Database")

    conn = create_connection("default.db")
    mycur = conn.cursor()
    mycur.execute("PRAGMA database_list;")
    available_table = mycur.fetchall()
    with st.expander("Available Databases"):
        st.write(pd.DataFrame(available_table))

    if create_db:

        if db_filename.endswith(".db"):
            conn = create_connection(db_filename)

            st.success(
                "New Database has been Created! Please move on to next tab for loading data into Table."
            )
        else:
            st.error(
                "Database name must end with .db as we are using sqlite in the background to create files."
            )


class ModelMonitor:
    class Model:
        pageTitle = "Data Monitor"

        assign_labels_text = "Assign Labels"
        text_caption_1 = "Check 'Assign Labels' to enable editing of labels and values, move and resize the boxes to annotate the document."
        text_caption_2 = "Add annotations by clicking and dragging on the document, when 'Assign Labels' is unchecked."

        selected_field = "Selected Field: "
        save_text = "Save"
        saved_text = "Saved!"

        subheader_1 = "Select"
        subheader_2 = "Upload"
        annotation_text = "Annotation"
        no_annotation_file = "No annotation file selected"
        no_annotation_mapping = "Please annotate the document. Uncheck 'Assign Labels' and draw new annotations"

        download_text = "Download"
        download_hint = "Download the annotated structure in JSON format"

        annotation_selection_help = "Select an annotation file to load"
        upload_help = "Upload a file to annotate"
        upload_button_text = "Upload"
        upload_button_text_desc = "Choose a file"

        assign_labels_text = "Assign Labels"
        assign_labels_help = "Check to enable editing of labels and values"

        export_labels_text = "Export Labels"
        export_labels_help = "Create key-value pairs for the labels in JSON format"
        done_text = "Done"

        grouping_id = "ID"
        grouping_value = "Value"

        completed_text = "Completed"
        completed_help = "Check to mark the annotation as completed"

        error_text = "Value is too long. Please shorten it."
        selection_must_be_continuous = "Please select continuous rows"

    def view(self, model):
        with st.sidebar:
            st.markdown("---")
            st.subheader(model.subheader_1)

            placeholder_upload = st.empty()

            if "annotation_index" not in st.session_state:
                st.session_state["annotation_index"] = 0
                annotation_index = 0
            else:
                annotation_index = st.session_state["annotation_index"]

            completed_check = st.empty()

            btn = st.button(model.export_labels_text)
            if btn:
                self.export_labels(model)
                st.write(model.done_text)

            st.subheader(model.subheader_2)

            with st.form("upload-form", clear_on_submit=True):
                uploaded_file = st.file_uploader(
                    model.upload_button_text_desc,
                    accept_multiple_files=False,
                    type=["png", "jpg", "jpeg"],
                    help=model.upload_help,
                )
                submitted = st.form_submit_button(model.upload_button_text)

                if submitted and uploaded_file is not None:
                    ret = self.upload_file(uploaded_file)

        _, colT21 = st.columns([3, 7])
        with colT21:
            st.title("Model Monitor")
        # st.title(model.pageTitle + " - " + annotation_selection)
        intro, db, tbl, qry = st.tabs(
            ["1 Intro to SQL", "2 Create Database", "3 Upload Data", "4 Query Data"]
        )
        with intro:
            st.write((Path(__file__).parent / "sql.md").read_text())
            st.markdown(
                f"""
                - API {os.path.join("GRADX_HOST", ':8000/api')}
                - API documentation {os.path.join("GRADX_HOST", ':8000/api/docs')}
                - rq dashboard {os.path.join("GRADX_HOST", ':9181')}
                """
            )
            df = pd.read_csv(
                "https://raw.githubusercontent.com/fivethirtyeight/data/master/airline-safety/airline-safety.csv"
            )
            AgGrid(df)
            with db:
                create_database()
            with tbl:
                upload_data()
            with qry:
                sqlite_dbs = [file for file in os.listdir(".") if file.endswith(".db")]
                db_filename = st.selectbox("DB Filename", sqlite_dbs)
                conn = create_connection(db_filename)
                mycur = conn.cursor()
                mycur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
                )
                available_table = mycur.fetchall()
                st.write("Available Tables")
                st.dataframe(pd.DataFrame(available_table))
                # with readme("streamlit-ace"):
                with st.chat_message("streamlit-ace"):
                    c1, c2 = st.columns([3, 0.5])

                    # c2.subheader("Parameters")
                    # st.write(LANGUAGES)
                    with c2:
                        st.write("")
                        st.write("")
                        st.write("")
                        st.write("")
                        dark_mode = tog.st_toggle_switch(
                            label="Dark",
                            key="darkmode",
                            default_value=False,
                            label_after=False,
                            inactive_color="#D3D3D3",
                            active_color="#11567f",
                            track_color="#29B5E8",
                        )
                        if dark_mode:
                            THEME = THEMES[0]
                        else:
                            THEME = THEMES[3]
                    with c1:
                        st.subheader("Query Editor")
                        content = st_ace(
                            placeholder="--Select Database and Write your SQL Query Here!",
                            language=LANGUAGES[145],
                            theme=THEME,
                            keybinding=KEYBINDINGS[3],
                            font_size=c2.slider("Font Size", 10, 24, 16),
                            min_lines=15,
                            key="run_query",
                        )

                        if content:
                            st.subheader("Content")

                            st.text(content)

                            def run_query():
                                query = content
                                conn = create_connection(db_filename)

                                try:
                                    query = conn.execute(query)
                                    cols = [column[0] for column in query.description]
                                    results_df = pd.DataFrame.from_records(
                                        data=query.fetchall(), columns=cols
                                    )
                                    st.dataframe(results_df)
                                    export = results_df.to_csv()
                                    st.download_button(
                                        label="Download Results",
                                        data=export,
                                        file_name="query_results.csv",
                                    )
                                except Exception as e:
                                    st.write(e)

                            run_query()
