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
        where et.name is not NULL  
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
        return True


if __name__ == "__main__":
    triage_history_file = os.path.join(os.getcwd(), "data", "triage_history.csv")
    regression_db = MysqlConnection().connect("local_regression")
    generate_triage_history_data(regression_db, triage_history_file)
