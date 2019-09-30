from utils.mysql_helper import MysqlConnection
from utils.simple_prejudge_helper import SimplePrejudgeHelper
import pandas as pd
import os


def generate_triage_history_data(db_conn, file_path):
    triage_history_sql = """
        SELECT tr.id as round_id, p.name as project, acr.automation_case_id, asr.automation_script_id, te.name as env, b.name as browser, et.name as triage_type, acr.error_message, (UNIX_TIMESTAMP(asr.end_time)-UNIX_TIMESTAMP(asr.start_time)) as script_duration FROM `automation_case_results` as acr
        left join `automation_script_results` as asr on acr.automation_script_result_id=asr.id
        left join `test_rounds` as tr on asr.test_round_id=tr.id
        left join `test_environments` as te on tr.test_environment_id=te.id
        left join `browsers` as b on tr.browser_id=b.id
        left join `projects` as p on p.id=tr.project_id
        left join `error_types` as et on et.id=acr.error_type_id
        where et.name is not NULL and p.name is not NULL 
        ORDER BY `round_id`  ASC
    """
    print("generate triage history data of all projects")
    con = db_conn.get_conn()
    triage_history_data = pd.read_sql(triage_history_sql, con)
    con.close()
    if len(triage_history_data) == 0:
        print("no triage history in all projects")
        return False
    else:
        triage_history_data["error_type"] = triage_history_data["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
        triage_history_data.to_csv(file_path)
        print("there are %d rows in database when query the triage history of all projects\n" % len(triage_history_data))
        project_list = triage_history_data["project"].unique()
        for project in project_list:
            convert_triage_data = triage_history_data[triage_history_data["project"] == project]
            convert_triage_data["avg_duration"] = convert_triage_data["automation_script_id"].apply(lambda x: get_avg_duration_of_script(db_conn, x))
            convert_triage_data["avg_duration"] = pd.to_numeric(convert_triage_data["avg_duration"])
            convert_triage_data["duration_offset"] = convert_triage_data["script_duration"] - convert_triage_data["avg_duration"]
            convert_triage_data["duration"] = convert_triage_data["duration_offset"] / convert_triage_data["avg_duration"]
            # min_duration = convert_triage_data["duration_offset"].min()
            # max_duration = convert_triage_data["duration_offset"].max()
            # convert_triage_data["duration"] = convert_triage_data["duration_offset"].apply(lambda x: (x - min_duration) / (max_duration - min_duration))
            convert_triage_data = pd.get_dummies(convert_triage_data, columns=["env"], prefix_sep="_")
            convert_triage_data = pd.get_dummies(convert_triage_data, columns=["browser"], prefix_sep="_")
            convert_triage_data = pd.get_dummies(convert_triage_data, columns=["error_type"], prefix_sep="_")
            to_drop = ["round_id", "project", "automation_case_id", "automation_script_id", "error_message", "script_duration", "avg_duration", "duration_offset"]
            convert_triage_data.drop(columns=to_drop, inplace=True)
            convert_triage_data.dropna(axis=0, subset=["duration"], inplace=True)
            print(len(convert_triage_data), len(convert_triage_data.loc[convert_triage_data["triage_type"] == "Product Error"]), project)
            convert_file_path = file_path.split(".csv")[0] + "_%s.csv" % project
            convert_triage_data.to_csv(convert_file_path)
        return True


def get_avg_duration_of_script(db_conn, script_id):
    error_limit = 10
    while error_limit:
        try:
            avg_duration_sql = "select avg(UNIX_TIMESTAMP(end_time)-UNIX_TIMESTAMP(start_time)) as avg_duration from `automation_script_results` where automation_script_id=%s and DATE_SUB(CURDATE(), INTERVAL 12 MONTH) <= date(end_time)" % str(script_id)
            avg_duration = db_conn.get_first_result_from_database(avg_duration_sql)["avg_duration"]
            break
        except:
            print("error when get avg duration")
            error_limit -= 1
    return avg_duration


if __name__ == "__main__":
    triage_history_file = os.path.join(os.getcwd(), "data", "triage_history.csv")
    regression_db = MysqlConnection().connect("local_regression")
    generate_triage_history_data(regression_db, triage_history_file)
