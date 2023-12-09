import streamlit as st
from natsort import natsorted
import os
import math
import json
from utils import create_connection, get_file_size
import pandas as pd
from streamlit_ace import st_ace, KEYBINDINGS, LANGUAGES, THEMES
from utils import get_bj_day
import time
from datetime import timedelta
from datetime import datetime
import hirlite
import pickle
from st_aggrid import AgGrid
from mlopskit import make

DB_NAME = "data.db"
# Functions
def create_table():
    conn = create_connection(DB_NAME)
    mycur = conn.cursor()
    mycur.execute(
        "CREATE TABLE IF NOT EXISTS blogtable(author TEXT,title TEXT UNIQUE,article TEXT,postdate DATE)"
    )


center_db = "/home/leepand/center_db/monitor.db"

data_store = hirlite.Rlite(center_db, encoding="utf8")

avatar1 = "https://www.w3schools.com/howto/img_avatar.png"
avatar2 = "https://www.w3schools.com/howto/img_avatar2.png"

today = get_bj_day()
current_date = datetime.strptime(today, "%Y-%m-%d")  # 将字符串转换为datetime对象
date_list = []

# 通过循环生成前7天的日期列表
for i in range(7):
    delta = timedelta(days=i)  # 创建一个时间间隔对象，表示i天
    date = current_date - delta  # 当前日期减去时间间隔，获得前i天的日期
    date_list.append(date.strftime("%Y-%m-%d"))  # 将日期对象转换为字符串并添加到列表中


def pic_select(owner):
    if owner in ["孙迪", "董哲"]:
        return avatar2
    else:
        return avatar1


# Reading Time
def readingTime(mytext):
    total_words = len([token for token in mytext.split(" ")])
    estimatedTime = total_words / 200.0
    return estimatedTime


def tabs(default_tabs=[], default_active_tab=0):
    if not default_tabs:
        return None

    active_tab = st.radio("", default_tabs, index=default_active_tab)  # , key="tabs")
    child = default_tabs.index(active_tab) + 1

    st.markdown(
        """  
        <style type="text/css">
        div[role=radiogroup] > label > div:first-of-type, .stRadio > label {
        display: none;               
        }
        div[role=radiogroup] {
            flex-direction: unset
        }
        div[role=radiogroup] label {             
            border: 1px solid #999;
            background: #EEE;
            padding: 4px 12px;
            border-radius: 4px 4px 0 0;
            position: relative;
            top: 1px;
            }
        div[role=radiogroup] label:nth-child("""
        + str(child)
        + """) {    
            background: #FFF !important;
            border-bottom: 1px solid transparent;
        }            
        </style>
    """,
        unsafe_allow_html=True,
    )

    return active_tab


class FeatureStore:
    class Model:
        # pageTitle = "Data Review"
        subheader_2 = "Select"
        subheader_3 = "Result"
        selection_owner_text = "Owner to review"
        selection_title_text = "Project to review"
        initial_msg = "Please select a file to review"
        feature_store_file = "docs/featurestore.json"
        HeaderTitle = "Feature Store"
        Owner_list = ["孙迪", "董哲", "王博", "林书博", "Jeffrey"]

        img_file = None

        def get_title_temp(self, title, star_user, owner, short_article):
            title_temp = f"""
            <div style="background-color:#EEEEEE;padding:10px;border-radius:10px;margin:10px;">
                <h4 style="color:black;text-align:center;">
                    {title}
                </h4>
                <img src={star_user} alt="Avatar" style="vertical-align: middle;float:left;width: 50px;height: 50px;border-radius: 50%;">
                <h6>
                    Owner:{owner}
                </h6>
                <br/>
                <br/>
                <p style="text-align:justify">
                    {short_article}
                </p>
            </div>
            """
            return title_temp

        head_message_temp = """
            <div style="background-color:#EEEEEE;padding:10px;border-radius:5px;margin:10px;">
            <h1 style="color:black;text-align:center;">{}</h1>
            <img src={} alt="Avatar" style="vertical-align: middle;float:left;width: 50px;height: 50px;border-radius: 50%;">
            <h6>Author:{}</h6>     
            <h6>Post Date: {}</h6>
        
        </div>
        """
        full_message_temp = """
            <div style="background-color:silver;padding:10px;border-radius:5px;margin:10px;">
                <p style="text-align:justify;color:black;padding:10px">{}</p>
            </div>
            """

        def set_image_file(self, img_file):
            st.session_state["img_file_review"] = img_file

        def get_image_file(self):
            if "img_file_review" not in st.session_state:
                return None
            return st.session_state["img_file_review"]

        json_file = None

        def set_json_file(self, json_file):
            st.session_state["json_file_review"] = json_file

        def get_json_file(self):
            if "json_file_review" not in st.session_state:
                return None
            return st.session_state["json_file_review"]

    def view(self, model):
        # st.title(model.pageTitle)
        create_table()
        # with st.sidebar:
        # st.markdown("---")
        # st.subheader(model.subheader_2)

        # get list of files in inference directory
        # processed_file_names = self.get_processed_file_names("docs/inference/")
        feature_meta_json = self.get_meta_data(model)
        owners = self.get_owners(feature_meta_json)

        _, colT21 = st.columns([3, 7])
        with colT21:
            st.title(model.HeaderTitle)

        active_tab = tabs(
            [
                "Project List",
                "View Project",
                "Add Project",
                "Edit Project",
                "Search",
                "Manager",
            ]
        )
        if active_tab == "Project List":
            result = self.view_all_notes()
            if not result:
                st.markdown(f"请先访问`Add Project`界面创建项目。")
            for i in result:
                b_author = i[0]
                b_title = i[1]
                short_article = str(i[2])[0:50]

                b_post_date = i[3]
                owner_star = pic_select(b_author)
                mark_down_text = model.get_title_temp(
                    b_title, owner_star, b_author, short_article
                )
                st.markdown(
                    mark_down_text,
                    unsafe_allow_html=True,
                )
        elif active_tab == "Edit Project":
            st.subheader("Edit Project")
            _owners = model.Owner_list
            blog_author = st.selectbox("Select Owner Name", _owners)
            projects = self.get_blog_by_author(author=blog_author)
            _titles = [p[1] for p in projects]
            blog_title = st.selectbox("Select Project Title", _titles)
            post_result = self.get_blog_by_title(blog_title)
            # st.write(blog_title)
            # st.write(post_result)
            _b_article = post_result[0][2]
            THEME = THEMES[3]

            content = st_ace(
                value=_b_article,
                # language=LANGUAGES[145],
                language="markdown",
                theme=THEME,
                keybinding=KEYBINDINGS[3],
                # show_gutter=True,
                wrap=False,
                # auto_update=True,
                # font_size=c2.slider("Font Size", 10, 24, 16),
                min_lines=15,
                # key="edit_project",
            )
            blog_post_date = get_bj_day()
            if st.button("Save"):
                if blog_author == "Leepand":
                    blog_author = "Jeffrey"
                self.edit_data(
                    title=blog_title,
                    new_article=content,
                    new_author=blog_author,
                    new_postdate=blog_post_date,
                )
                st.success("Project:{} edited!".format(blog_title))

        elif active_tab == "View Project":
            st.subheader("View Project")
            view_by_list = ["Owner", "Title"]
            selection_view_by = st.selectbox("View By:", view_by_list)
            if selection_view_by == "Owner":
                owners_list = model.Owner_list
                selection_sub = st.selectbox(model.selection_owner_text, owners_list)
                post_result = self.get_blog_by_author(author=selection_sub)
            else:
                all_titles = [i[0] for i in self.view_all_titles()]

                selection_sub = st.selectbox(model.selection_title_text, all_titles)
                post_result = self.get_blog_by_title(selection_sub)

            # all_titles = [i[0] for i in self.view_all_titles()]
            # postlist = st.sidebar.selectbox("View Projects", all_titles)

            for i in post_result:
                b_author = i[0]
                b_title = i[1]
                b_article = i[2]
                b_post_date = i[3]
                # st.text("Reading Time:{}".format(readingTime(b_article)))
                owner_star = pic_select(b_author)
                st.text("Reading Time:{} minutes".format(readingTime(str(i[2]))))
                st.markdown(
                    model.head_message_temp.format(
                        b_title, owner_star, b_author, b_post_date
                    ),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    b_article,
                    unsafe_allow_html=True
                    # model.full_message_temp.format(b_article), unsafe_allow_html=True
                )

        elif active_tab == "Add Project":
            st.subheader("Add Your Project")
            # blog_author = st.text_input("Enter Owner Name",max_chars=50)
            _owners = model.Owner_list
            blog_author = st.selectbox("Select Owner Name", _owners)
            blog_title = st.text_input("Enter Project Title")
            THEME = THEMES[3]
            blog_article = st_ace(
                placeholder="Post Project Here",
                # language=LANGUAGES[145],
                language="markdown",
                theme=THEME,
                keybinding=KEYBINDINGS[3],
                wrap=False,
                # auto_update=True,
                # font_size=c2.slider("Font Size", 10, 24, 16),
                min_lines=15,
                key="add_project",
            )
            # blog_article = st.text_area("Post Project Here", height=200)
            blog_post_date = st.date_input("Date")
            if st.button("Add"):
                self.add_data(
                    author=blog_author,
                    title=blog_title,
                    article=blog_article,
                    postdate=blog_post_date,
                )
                st.success("Project:{} saved".format(blog_title))

        elif active_tab == "Search":
            st.subheader("Search Projects")
            search_term = st.text_input("Enter Term")
            # search_choice = st.radio("Field to Search",("title","author"),key="vblog")
            search_choice = st.selectbox("Field to Search", ("title", "author"))
            # search_choice = st.radio("Field to Search",("title","author"),key="search")
            # st.checkbox("title")
            if st.button("Search"):
                if search_choice == "title":
                    article_result = self.get_blog_by_title(search_term)
                elif search_choice == "author":
                    article_result = self.get_blog_by_author(search_term)

                # Preview Articles
                for i in article_result:
                    st.text("Reading Time:{} minutes".format(readingTime(str(i[2]))))
                    # st.write(article_temp.format(i[1],i[0],i[3],i[2]),unsafe_allow_html=True)
                    owner_star = pic_select(i[0])
                    st.write(
                        model.head_message_temp.format(i[1], owner_star, i[0], i[3]),
                        unsafe_allow_html=True,
                    )
                    st.write(
                        model.full_message_temp.format(i[2]), unsafe_allow_html=True
                    )
        elif active_tab == "Manager":
            st.subheader("Manage Project")
            result = self.view_all_notes()
            clean_db = pd.DataFrame(
                result, columns=["Owner", "Title", "Article", "Date"]
            )
            st.dataframe(clean_db)
            unique_list = [i[0] for i in self.view_all_titles()]
            delete_by_title = st.selectbox("Select Title", unique_list)
            if st.button("Delete"):
                # self.delete_data(delete_by_title)
                st.warning("Deleted: '{}'".format(delete_by_title))

            if st.checkbox("Metrics"):
                new_df = clean_db
                new_df["Length"] = new_df["Article"].str.len()

                st.dataframe(new_df)
                # st.dataframe(new_df['Author'].value_counts())
                st.subheader("Owner Stats")
                new_df["Owner"].value_counts().plot(kind="bar")
                st.pyplot()
                new_df["Owner"].value_counts().plot.pie(autopct="%1.1f%%")
                st.pyplot()

            if st.checkbox("Feature Update Info"):
                # 假设你有一个名为data的字典，其中包含要转换为DataFrame的数
                time_menu = ["今天", "昨天"]
                time_menu = date_list
                options = st.selectbox("时间区间", time_menu)

                model_name_desc_list = []
                model_name_list = []
                success_cnt_list = []
                real_cnt_list = []
                update_gap_list = []
                update_date_list = []
                owner_list = []
                size_of_data_list = []

                if options == "今天":
                    _date = get_bj_day()
                else:
                    _date = options  # get_yestoday_bj()
                meta_data = feature_meta_json["features"]
                owner_map = {
                    "sundi": "孙迪",
                    "linshubo": "林书博",
                    "dongzhe": "董哲",
                    "wangbo": "王博",
                }
                query_date = _date
                model_off_line_db_meta = {}
                for owner in model.Owner_list:
                    for meta in meta_data:
                        if owner_map[meta["owner"]] == owner:
                            model_name = meta["model_name"]
                            db_name = meta["db_name"]
                            model_desc = meta["description"]

                            data_store_key = f"{model_name}:{query_date}"
                            db_info = data_store.get(data_store_key)

                            model_name_desc_list.append(model_desc)
                            model_name_list.append(model_name)

                            if db_info is None:
                                succ_cnt = "暂无数据"
                                real_cnt = "暂无数据"
                                update_gap = -1
                                data_size = "暂无数据"
                                _current_date = _date
                            else:
                                _data = pickle.loads(db_info)
                                succ_cnt = _data["success_insert_cnt"]
                                real_cnt = _data["correct_data_cnt"]
                                _current_date = _data["current_date"]
                                update_gap = real_cnt - succ_cnt
                                p = _data["data_path"]
                                # file = f"{p}/{db_name}.db"
                                file = os.path.join(p, f"{db_name}.db")
                                if model_name in model_off_line_db_meta:
                                    model_off_line_db_meta[model_name].append(file)
                                else:
                                    model_off_line_db_meta[model_name] = [file]

                                try:
                                    data_size = get_file_size(file)
                                except:
                                    data_size = f"file {file} not found"
                            size_of_data_list.append(data_size)
                            update_gap_list.append(update_gap)
                            real_cnt_list.append(real_cnt)
                            success_cnt_list.append(succ_cnt)
                            update_date_list.append(_current_date)
                            owner_list.append(owner)
                data = {
                    "模型名称": model_name_desc_list,
                    "model_name": model_name_list,
                    "成功条数": success_cnt_list,
                    "实际条数": real_cnt_list,
                    "更新差值": update_gap_list,
                    "数据大小": size_of_data_list,
                    "更新日期": update_date_list,
                    "责任人": owner_list,
                }

                def color_survived(val):
                    color = "red" if val > 0 else "yellow" if val < 0 else "green"
                    return f"background-color: {color}"

                df = pd.DataFrame(data)
                st.markdown("#### Detailed Data Update View")
                AgGrid(df)
                """st.table(
                    df[
                        [
                            "模型名称",
                            "model_name",
                            "成功条数",
                            "实际条数",
                            "更新差值",
                            "数据大小",
                            "更新日期",
                            "责任人",
                        ]
                    ]
                    .sort_values(["更新差值"], ascending=False)
                    .reset_index(drop=True)
                    .head(20)
                    .style.applymap(color_survived, subset=["更新差值"])
                )"""
                st.markdown("#### Detailed Data Tests")
                sub_model = st.selectbox("选择模型", model_name_list)
                model_db_file_list = model_off_line_db_meta.get(sub_model)
                if model_db_file_list is not None:
                    sub_model_db = st.selectbox("选择模型存储库", model_db_file_list)
                    uid = st.text_input('请输入uid', '')
                    if uid:
                        model_key = f"{uid}:{sub_model}"
                        # model_db = hirlite.Rlite(sub_model_db, encoding="utf8")
                        out = None
                        # out=model_db.get(model_key)
                        if out is None:
                            st.write(f'数据库{sub_model_db}中{uid}不存在')
                        else:
                            st.markdown(f'```json\n\n{pickle.loads(out)}不存在\n')

    def get_processed_file_names(self, dir_name):
        # get ordered list of files without file extension, excluding hidden files, with JSON extension only
        file_names = [
            os.path.splitext(f)[0]
            for f in os.listdir(dir_name)
            if os.path.isfile(os.path.join(dir_name, f))
            and not f.startswith(".")
            and f.endswith(".json")
        ]
        file_names = natsorted(file_names)
        return file_names

    def get_meta_data(self, model):
        feature_meta_file = model.feature_store_file
        with open(feature_meta_file, "r") as f:
            feature_meta_json = json.load(f)
        return feature_meta_json

    def get_owners(self, data):
        owners = [_data["owner"] for _data in data["features"]]
        return owners

    def get_selection_index(self, file, files_list):
        return files_list.index(file)

    def render_results(self, model):
        json_file = model.get_json_file()
        if json_file is not None:
            with open(json_file) as f:
                data_json = json.load(f)
                st.subheader(model.subheader_3)
                st.markdown("---")
                st.json(data_json)
                st.markdown("---")

    def add_data(self, author, title, article, postdate):
        conn = create_connection(DB_NAME)
        mycur = conn.cursor()
        mycur.execute(
            "INSERT INTO blogtable(author,title,article,postdate) VALUES (?,?,?,?)",
            (author, title, article, postdate),
        )
        conn.commit()

    def edit_data(self, title, new_author, new_article, new_postdate):
        conn = create_connection(DB_NAME)
        mycur = conn.cursor()
        mycur.execute(
            "UPDATE blogtable SET author=?, article=?, postdate=? WHERE title=?",
            (new_author, new_article, new_postdate, title),
        )
        conn.commit()

    def view_all_notes(self):
        conn = create_connection(DB_NAME)
        mycur = conn.cursor()
        mycur.execute("SELECT * FROM blogtable")
        data = mycur.fetchall()
        return data

    def get_blog_by_title(self, title):
        conn = create_connection(DB_NAME)
        mycur = conn.cursor()
        mycur.execute('SELECT * FROM blogtable WHERE title="{}"'.format(title))
        data = mycur.fetchall()
        return data

    def get_blog_by_author(self, author):
        conn = create_connection(DB_NAME)
        mycur = conn.cursor()
        mycur.execute('SELECT * FROM blogtable WHERE author="{}"'.format(author))
        data = mycur.fetchall()
        return data

    def delete_data(self, title):
        conn = create_connection(DB_NAME)
        mycur = conn.cursor()
        mycur.execute('DELETE FROM blogtable WHERE title="{}"'.format(title))
        conn.commit()

    def view_all_titles(self):
        conn = create_connection(DB_NAME)
        mycur = conn.cursor()
        mycur.execute("SELECT DISTINCT title FROM blogtable")
        data = mycur.fetchall()
        return data
