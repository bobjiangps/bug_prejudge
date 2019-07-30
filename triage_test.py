from utils.mysql_helper import MysqlConnection
from utils.file_helper import FileHelper
from utils.simple_prejudge_helper import SimplePrejudgeHelper
import pandas as pd
import os


def generate_triage_history_data(db_conn, project_name, file_path):
    # triage_history_sql = "SELECT * FROM `automation_case_results` where triage_result is not NULL and error_type_id in (select id from error_types where name in ('Product Error', 'Product Change')) and automation_script_result_id in (select id from automation_script_results where triage_result is not NULL and automation_script_id in (select id from automation_scripts where project_id=2))"
    # triage_history_sql = "SELECT * FROM `automation_case_results` where error_type_id in (select id from error_types) and automation_script_result_id in (select id from automation_script_results where automation_script_id in (select id from automation_scripts where project_id=2))"
    triage_history_sql = """
        SELECT tr.id as round_id, acr.automation_case_id, asr.automation_script_id, te.name as env, b.name as browser, et.name as triage_type, acr.error_message, (UNIX_TIMESTAMP(asr.end_time)-UNIX_TIMESTAMP(asr.start_time)) as script_duration FROM `automation_case_results` as acr
        left join `automation_script_results` as asr on acr.automation_script_result_id=asr.id
        left join `test_rounds` as tr on asr.test_round_id=tr.id
        left join `test_environments` as te on tr.test_environment_id=te.id
        left join `browsers` as b on tr.browser_id=b.id
        left join `projects` as p on p.id=tr.project_id
        left join `error_types` as et on et.id=acr.error_type_id
        where p.name='%s' and et.name is not NULL  
        ORDER BY `round_id`  ASC
    """ % project_name
    print("generate triage history data of project: %s" % project_name)
    triage_history_data = db_conn.get_all_results_from_database(triage_history_sql)
    if len(triage_history_data) == 0:
        print("no triage history in project: %s" % project_name)
        return False
    else:
        FileHelper.save_db_query_result_to_csv(triage_history_data, file_path)
        print("there are %d rows in database when query the triage history of project: %s\n" % (len(triage_history_data), project_name))
        return True


project_name = "Endurance"
triage_type = "Product Error"
triage_file = os.path.join(os.getcwd(), "data", "temp_triage_%s.csv" % project_name)
regression_db = MysqlConnection().connect("local_regression")
# generate_file = True
generate_file = False
if generate_file:
    generate_triage_history_data(regression_db, project_name, triage_file)

triage_history = pd.read_csv(triage_file)
# triage_product_error = triage_history.loc[triage_history["triage_type"] == triage_type]
# new_triage_product_error = pd.get_dummies(triage_product_error, columns=['env'], prefix_sep='_')
# new_triage_product_error = pd.get_dummies(new_triage_product_error, columns=['browser'], prefix_sep='_')
# new_triage_file = os.path.join(os.getcwd(), "data", "temp_triage_%s_new.csv" % project_name)
# new_triage_product_error.to_csv(new_triage_file)

automation_script_id = 72499
avg_duration_sql = "select avg(UNIX_TIMESTAMP(end_time)-UNIX_TIMESTAMP(start_time)) as avg_duration from `automation_script_results` where automation_script_id=%s and DATE_SUB(CURDATE(), INTERVAL 12 MONTH) <= date(end_time)" % str(automation_script_id)
con = regression_db.get_conn()
script_avg_duration = pd.read_sql(avg_duration_sql, con)
con.close()
print(script_avg_duration["avg_duration"][0])
