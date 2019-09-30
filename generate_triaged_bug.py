from utils.mysql_helper import MysqlConnection
from utils.simple_prejudge_helper import SimplePrejudgeHelper
import pandas as pd
import os
import re


def generate_existent_bug_data(db_conn, file_path):
    existent_bug_sql = """
        SELECT tr.id as round_id, p.name as project, acr.automation_case_id, asr.automation_script_id, te.name as env, b.name as browser, et.name as triage_type, acr.error_message, acr.triage_result, (UNIX_TIMESTAMP(asr.end_time)-UNIX_TIMESTAMP(asr.start_time)) as script_duration FROM `automation_case_results` as acr
        left join `automation_script_results` as asr on acr.automation_script_result_id=asr.id
        left join `test_rounds` as tr on asr.test_round_id=tr.id
        left join `test_environments` as te on tr.test_environment_id=te.id
        left join `browsers` as b on tr.browser_id=b.id
        left join `projects` as p on p.id=tr.project_id
        left join `error_types` as et on et.id=acr.error_type_id
        where et.name = 'Product Error' and acr.triage_result is not NULL  
        ORDER BY `round_id`  ASC
    """
    print("generate existent bug data of all projects")
    con = db_conn.get_conn()
    existent_bug_data = pd.read_sql(existent_bug_sql, con)
    con.close()
    if len(existent_bug_data) == 0:
        print("no bug recorded in all projects")
        return False
    else:
        existent_bug_data.dropna(inplace=True)
        existent_bug_data["error_type"] = existent_bug_data["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
        print("there are %d rows in database when query the existent bug of all projects\n" % len(existent_bug_data))
        existent_bug_data["bug_id"] = existent_bug_data["triage_result"].apply(lambda x: search_bug_id(x))
        existent_bug_data.dropna(axis=0, subset=["bug_id"], inplace=True)
        existent_bug_data.to_csv(file_path)
        print("there are %d rows which has bug id in all projects\n" % len(existent_bug_data))
        project_list = existent_bug_data["project"].unique()
        for project in project_list:
            convert_bug_data = existent_bug_data[existent_bug_data["project"] == project]
            to_drop = ["round_id", "script_duration"]
            convert_bug_data.drop(columns=to_drop, inplace=True)
            print(len(convert_bug_data), project)
            convert_file_path = file_path.split(".csv")[0] + "_%s.csv" % project
            convert_bug_data.to_csv(convert_file_path)
        return True


def search_bug_id(text):
    pattern = "\W*(\w+-\d+).*"
    result = re.search(pattern, text, re.IGNORECASE)
    if result:
        return result.groups()[0]


if __name__ == "__main__":
    existent_bug_file = os.path.join(os.getcwd(), "data", "triaged_bug.csv")
    regression_db = MysqlConnection().connect("local_regression")
    generate_existent_bug_data(regression_db, existent_bug_file)
