import duckdb
from google.cloud import bigquery
from utils import get_bj_day, get_yestoday_bj, get_lastn_date_bj


def get_conn(db=":memory:", is_shared=False):
    return duckdb.connect(database=db, read_only=is_shared)


def calculate_mean(lst):
    if len(lst) == 0:
        return None  # 返回 None 或其他特定值

    total = sum(lst)
    mean = total / len(lst)
    return mean


class Database:
    def __init__(self, filter_big_user=0):
        self.conn = get_conn("db/datahack.duckdb")
        self.bqclient = bigquery.Client()
        self.min_pays = float(filter_big_user)
        self.today = get_bj_day()

    def get_filter_opts(self):
        query_str = f"""SELECT
            SUM(CAST(jsonpayload.usd AS float64)) AS pay,
            jsonPayload.uid AS uid,
            DATE(timestamp,'-3') AS date
                FROM
            `seateam.fact.purchase`
                WHERE
            DATE(timestamp,'-3')='{self.today}'
                GROUP BY
            date,
            uid
                HAVING
            pay>{self.min_pays}
                ORDER BY
            date"""
        results = self.bqclient.query(query_str)
        df_filters = results.to_dataframe()
        uid_list = []
        for row in df_filters.itertuples():
            uid_list.append(str(row.uid))
        return uid_list

    def get_model_type_frombq(
        self, ab_name_list=[], model_type_list=[], ab_date=None, pay_date=None
    ):
        if len(model_type_list) > 2:
            filter_opts_modeltype = (
                f"jsonPayload.exposure_details IN {tuple(model_type_list)}"
            )
        elif len(model_type_list) == 1:
            filter_opts_modeltype = (
                f"jsonPayload.exposure_details in ({model_type_list[0]})"
            )
        else:
            filter_opts_modeltype = "1=1"

        if len(ab_name_list) > 2:
            filter_opts_ab = f"jsonPayload.ab_id IN {tuple(ab_name_list)}"
        elif len(model_type_list) == 1:
            filter_opts_ab = f"jsonPayload.ab_id in ({ab_name_list[0]})"
        else:
            filter_opts_ab = "1=1"

        ab_date = get_yestoday_bj()
        pay_date = get_lastn_date_bj(7)
        query_str = f"""
            WITH
                #####
                churn_tag AS (
                SELECT
                    DISTINCT ab_id, CAST(uid AS String) AS uid,
                    exposure_details,
                    alternatives,
                    CONCAT(alternatives, " - ", exposure_details) AS tag
                FROM (
                    SELECT
                    jsonPayload.*
                    FROM
                    `seateam.fact.sys_churn_pay_result`
                    WHERE
                    timestamp>=TIMESTAMP("{ab_date} 20:00:00", "+08" )
                    AND {filter_opts_ab}
                    AND {filter_opts_modeltype}
                    AND jsonPayload.log_type = 4)),
                ####
                pay AS (
                SELECT
                    jsonPayload.*,
                    DATE(TIMESTAMP(jsonPayload.tsp), "-11") AS date
                FROM
                    `seateam.fact.purchase`
                WHERE
                    timestamp>=TIMESTAMP("{pay_date} 11:00:00", "+08" )
                    AND (NOT IFNULL(jsonpayload.is_sandbox, 0) = 1))
                SELECT
                ab_id,
                date,
                tag,
                COUNT(*) AS cnt,
                COUNT(DISTINCT uid) AS users,
                SUM(CAST(USD AS float64)) AS usd,
                SUM(CAST(USD AS float64))/COUNT(DISTINCT uid) AS avg_user_usd
                FROM
                pay
                LEFT JOIN
                churn_tag
                USING
                (uid)
                GROUP BY
                1,
                2,
                3
                ORDER BY
                1,
                2,
                3
            """
        results = self.bqclient.query(query_str)
        df_query = results.to_dataframe()
        self.conn.execute("""DROP TABLE IF EXISTS ab_modeltype_pays; """)
        self.conn.execute("create table ab_modeltype_pays as select * from df_query")
        return df_query

    def get_model_type_pays(self, ab_name, model_type_list=[]):
        alt_list = [
            "control",
            "control1",
            "control2",
            "control3",
            "test",
            "test1",
            "test2",
        ]
        filter_alt_list = []
        if len(model_type_list) > 0:
            for modeltype in model_type_list:
                for alt in alt_list:
                    filter_alt_list.append(f"""{alt} - {modeltype}""")

            filters = f"tag in {tuple(filter_alt_list)}"
        else:
            filters = "1=1"

        df_avg_user_usd = self.conn.execute(
            f"""select date,tag,avg_user_usd 
                    from ab_modeltype_pays
                    where ab_id='{ab_name}'
                    and {filters}
            """
        ).df()
        df_usd = self.conn.execute(
            f"""select date,tag,usd 
                        from ab_modeltype_pays
                        where ab_id='{ab_name}'
                        and {filters} """
        ).df()
        return df_avg_user_usd, df_usd

    def get_realdata_frombq(self, stat_date=None):
        if stat_date is None:
            stat_date = self.today
        start_date = get_yestoday_bj()
        end_date = self.today
        if self.min_pays > 0:
            uid_list = self.get_filter_opts()
            if len(uid_list) > 0:
                filter_opts = (
                    f"CAST(jsonpayload.uid AS string) not in {tuple(uid_list)}"
                )
            else:
                filter_opts = f"1=1"
        else:
            filter_opts = f"1=1"

        q_str = f"""
                WITH
                    #####
                    pay_tag AS (
                    SELECT
                        CAST(jsonpayload.uid AS string) AS uid,
                        DATE(timestamp, "-03") AS date,
                        jsonpayload.pay_type AS pay_type,
                        SUM(CAST(jsonpayload.usd AS float64)) AS pay
                    FROM
                        `seateam.fact.purchase`
                    WHERE
                        DATE(timestamp, "-03") BETWEEN '{start_date}'
                        AND '{end_date}'
                    GROUP BY
                        1,
                        2,
                        3),
                    #####
                    ab_tag AS (
                    SELECT
                        jsonpayload.ab_id AS ab_id,
                        CAST(jsonpayload.uid AS string) AS uid,
                        DATE(timestamp, "-03") as date,
                        jsonpayload.alternatives AS alternatives
                    FROM
                        `fact.sys_churn_pay_result`
                    WHERE
                        jsonpayload.log_type=1
                        AND {filter_opts}
                        AND DATE(timestamp, "-03") BETWEEN '{start_date}'
                        AND '{end_date}' QUALIFY ROW_NUMBER() OVER(PARTITION BY uid,ab_id,date
                                             ORDER BY DATE(timestamp, "-03"))=1)
                    SELECT
                    ab_id,
                    ab_tag.date,
                    alternatives,
                    pay_type,
                    COUNT(ab_tag.uid) AS users,
                    SUM(pay) AS sum_pays
                    FROM
                    ab_tag
                    JOIN
                    pay_tag
                    ON
                        ab_tag.uid=pay_tag.uid
                        AND ab_tag.date= pay_tag.date
                    GROUP BY
                    1,
                    2,
                    3,
                    4
                    ORDER BY
                    1,
                    2,
                    3,
                    4
        """
        results = self.bqclient.query(q_str)
        df_query = results.to_dataframe()
        self.conn.execute("""DROP TABLE IF EXISTS ab_pays; """)
        self.conn.execute("create table ab_pays as select * from df_query")
        return df_query

    def get_allpays(self, ab_name):
        yestoday = get_yestoday_bj()
        today = get_bj_day()
        query = f"""
            SELECT SUM(sum_pays) AS all_pays, date
            FROM ab_pays
            WHERE ab_id = '{ab_name}'
            GROUP BY date
        """

        result_df = self.conn.execute(query).df()
        pays_dict = result_df.set_index("date")["all_pays"].to_dict()

        today_all_pays = pays_dict.get(today, 0)
        yes_today_all_pays = pays_dict.get(yestoday, 0)

        return today_all_pays, yes_today_all_pays

    def cal_model_control_pays(self, ab_name):
        mapping_dict = {
            "test": ["test1", "test"],
            "control": ["control", "test2", "control2", "control1", "control3"],
        }
        ab_tests = self.conn.execute(
            f"""
            SELECT alternatives,SUM(sum_pays) as all_pays 
            FROM ab_pays 
            WHERE ab_id='{ab_name}' AND date='{self.today}'
            GROUP BY alternatives"""
        ).df()
        ab_tests_dict = ab_tests.set_index("alternatives")["all_pays"].to_dict()
        test_mapping_list = mapping_dict["test"]
        model_val = max(
            ab_tests_dict.get(test_alt, 0) for test_alt in test_mapping_list
        )

        control_mapping_list = mapping_dict["control"]
        new_control_vals = [
            ab_tests_dict.get(control_alt, 0)
            for control_alt in control_mapping_list
            if ab_tests_dict.get(control_alt, 0) != 0
        ]

        control_val = calculate_mean(new_control_vals)
        return model_val, control_val

    def classify_by_paytype(self, pay_type_list, ab_name):
        if len(pay_type_list) == 0:
            opts = "1=1"
        elif len(pay_type_list) == 1:
            opts = f"Pay_type = '{pay_type_list[0]}'"
        else:
            opts = f"Pay_type in {tuple(pay_type_list)}"
        df1_script = f"""
                SELECT
                alternatives,
                Pay_type,
                SUM(sum_pays) AS pays
                FROM (
                SELECT
                    alternatives,
                    CASE
                    WHEN pay_type < 4 AND pay_type>0 THEN 'small_R'
                    WHEN pay_type >=4
                    AND pay_type<6 THEN 'mid_R'
                    WHEN pay_type >=6 AND pay_type<8 THEN 'big_R'
                    Else 'Null_R'
                END
                    AS Pay_type,
                    sum_pays AS sum_pays
                FROM
                    ab_pays
                WHERE ab_id='{ab_name}' AND date='{self.today}')
                GROUP BY
                Pay_type,
                alternatives
                ORDER BY
                Pay_type
            """
        df2_script = """
            SELECT
                alternatives,
                SUM(pays) AS all_pays
                FROM
                df1
                GROUP BY
                alternatives
            """
        df1 = self.conn.execute(df1_script).df()
        df2 = self.conn.execute(df2_script).df()
        df = self.conn.execute(
            f"""
            SELECT
                a.alternatives,
                a.Pay_type,
                a.pays,
                a.pays/b.all_pays AS pay_percentage,
                b.all_pays
                FROM (
                SELECT
                    *
                FROM
                    df1
                WHERE
                    {opts}) AS a
                JOIN
                df2 AS b
                ON
                a.alternatives=b.alternatives
            """
        ).df()
        return df, df2
