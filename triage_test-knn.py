from utils.mysql_helper import MysqlConnection
from utils.file_helper import FileHelper
from utils.simple_prejudge_helper import SimplePrejudgeHelper
import pandas as pd
import os
import math
import datetime


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

def get_avg_duration_of_script(db_conn, script_id):
    avg_duration_sql = "select avg(UNIX_TIMESTAMP(end_time)-UNIX_TIMESTAMP(start_time)) as avg_duration from `automation_script_results` where automation_script_id=%s and DATE_SUB(CURDATE(), INTERVAL 12 MONTH) <= date(end_time)" % str(script_id)
    avg_duration = db_conn.get_first_result_from_database(avg_duration_sql)["avg_duration"]
    return avg_duration

start_time = datetime.datetime.now()
project_name = "Endurance"
triage_type = "Product Error"
triage_file = os.path.join(os.getcwd(), "data", "temp_init_triage_%s.csv" % project_name)
regression_db = MysqlConnection().connect("local_regression")
generate_file = True
# generate_file = False
if generate_file:
    generate_triage_history_data(regression_db, project_name, triage_file)

init_triage_history = pd.read_csv(triage_file)
triage_history = init_triage_history.copy()
# triage_product_error = triage_history.loc[triage_history["triage_type"] == triage_type]
# new_triage_product_error = pd.get_dummies(triage_product_error, columns=['env'], prefix_sep='_')
# new_triage_product_error = pd.get_dummies(new_triage_product_error, columns=['browser'], prefix_sep='_')
# new_triage_file = os.path.join(os.getcwd(), "data", "temp_triage_%s_new.csv" % project_name)
# new_triage_product_error.to_csv(new_triage_file)

# automation_script_id = 72499
# avg_duration_sql = "select avg(UNIX_TIMESTAMP(end_time)-UNIX_TIMESTAMP(start_time)) as avg_duration from `automation_script_results` where automation_script_id=%s and DATE_SUB(CURDATE(), INTERVAL 12 MONTH) <= date(end_time)" % str(automation_script_id)
# con = regression_db.get_conn()
# script_avg_duration = pd.read_sql(avg_duration_sql, con)
# con.close()
# print(script_avg_duration["avg_duration"][0])

triage_history["avg_duration"] = triage_history["automation_script_id"].apply(lambda x: get_avg_duration_of_script(regression_db, x))
triage_history["error_type"] = triage_history["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
triage_history["duration_offset"] = triage_history["script_duration"] - triage_history["avg_duration"]
min_duration = triage_history["duration_offset"].min()
max_duration = triage_history["duration_offset"].max()
triage_history["duration"] = triage_history["duration_offset"].apply(lambda x: (x-min_duration)/(max_duration - min_duration))
triage_history = pd.get_dummies(triage_history, columns=['env'], prefix_sep='_')
triage_history = pd.get_dummies(triage_history, columns=['browser'], prefix_sep='_')
triage_history = pd.get_dummies(triage_history, columns=['error_type'], prefix_sep='_')
to_drop = ["round_id", "automation_case_id", "automation_script_id", "error_message", "script_duration", "avg_duration", "duration_offset"]
triage_history.drop(columns=to_drop, inplace=True)
# triage_history.to_csv(os.path.join(os.getcwd(), "data", "temp_triage_%s_new.csv" % project_name))

triaged_labels = triage_history["triage_type"]
# triage_history.drop(columns=["triage_type"], inplace=True)
# print(type(triaged_labels))
# print(triaged_labels[0])
# print(type(triage_history))
# print(triage_history.loc[0])
# temp = triage_history.loc[0]
# print(temp["duration"])
# print(temp.loc["duration"])
# print(len(temp))
# print("0-0-0-0-0-0-")
# for i in temp:
#     print(i)


round_id_for_test = 98251
test_round_errors_sql = """SELECT tr.id as round_id, acr.automation_case_id, asr.automation_script_id, te.name as env, b.name as browser, acr.error_message, (UNIX_TIMESTAMP(asr.end_time)-UNIX_TIMESTAMP(asr.start_time)) as script_duration FROM `automation_case_results` as acr
                            left join `automation_script_results` as asr on acr.automation_script_result_id=asr.id
                            left join `test_rounds` as tr on asr.test_round_id=tr.id
                            left join `test_environments` as te on tr.test_environment_id=te.id
                            left join `browsers` as b on tr.browser_id=b.id
                            left join `projects` as p on p.id=tr.project_id
                            left join `error_types` as et on et.id=acr.error_type_id
                            where tr.id=%d and acr.result='failed';
                            """ % round_id_for_test
con = regression_db.get_conn()
init_test_round_errors = pd.read_sql(test_round_errors_sql, con)
con.close()
init_test_round_errors["error_type"] = init_test_round_errors["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
init_test_round_errors.to_csv(os.path.join(os.getcwd(), "data", "temp_init_round_error_%s.csv" % project_name))
test_round_errors = init_test_round_errors.copy()
test_round_errors["avg_duration"] = test_round_errors["automation_script_id"].apply(lambda x: get_avg_duration_of_script(regression_db, x))
test_round_errors["error_type"] = test_round_errors["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
test_round_errors["duration_offset"] = test_round_errors["script_duration"] - test_round_errors["avg_duration"]
min_duration = test_round_errors["duration_offset"].min()
max_duration = test_round_errors["duration_offset"].max()
if min_duration == max_duration:
    test_round_errors["duration"] = test_round_errors["duration_offset"].apply(lambda x: 1)
else:
    test_round_errors["duration"] = test_round_errors["duration_offset"].apply(lambda x: (x-min_duration)/(max_duration - min_duration))
test_round_errors = pd.get_dummies(test_round_errors, columns=['env'], prefix_sep='_')
test_round_errors = pd.get_dummies(test_round_errors, columns=['browser'], prefix_sep='_')
test_round_errors = pd.get_dummies(test_round_errors, columns=['error_type'], prefix_sep='_')
to_drop = ["round_id", "automation_case_id", "automation_script_id", "error_message", "script_duration", "avg_duration", "duration_offset"]
test_round_errors.drop(columns=to_drop, inplace=True)
missing_columns = list(set(triage_history.columns.values) ^ set(test_round_errors.columns.values))
for column in missing_columns:
    test_round_errors[column] = 0
test_round_errors.drop(columns=["triage_type"], inplace=True)
test_round_errors.to_csv(os.path.join(os.getcwd(), "data", "temp_new_round_error_%s.csv" % project_name))
triage_history.to_csv(os.path.join(os.getcwd(), "data", "temp_new_triage_%s.csv" % project_name))
init_triage_history["distance"] = "tbd"
init_test_round_errors["predict_triage"] = "tbd"
print("----------")
# test_error = test_round_errors.loc[0]
test_error = test_round_errors
distance = []
knn_columns = test_round_errors.columns.values
# print(triaged_labels)

# for index, row in triage_history.iterrows():
#     sum = 0
#     for column in knn_columns:
#         print("-=-=-=-=-=-")
#         print(column)
#         print(getattr(row, column))
#         print(test_error[column])
#         sum += math.pow(getattr(row, column) - test_error[column], 2)
#     print(sum)
#     print(math.sqrt(sum))
#     distance.append(math.sqrt(sum))
#     init_triage_history.loc[index, "distance"] = math.sqrt(sum)

for seq in range(len(test_error)):
    error = test_error.iloc[seq]
    for index, row in triage_history.iterrows():
        sum = 0
        for column in knn_columns:
            sum += math.pow(getattr(row, column) - error[column], 2)
        distance.append(math.sqrt(sum))
        init_triage_history.loc[index, "distance"] = math.sqrt(sum)
    init_triage_history = init_triage_history.sort_values(by=["distance"])
    predict_top = init_triage_history.iloc[:3]["triage_type"]
    # print(seq)
    # print(predict_top)
    # print(pd.value_counts(predict_top).index[0])
    init_test_round_errors.loc[seq, "predict_triage"] = pd.value_counts(predict_top).index[0]
init_test_round_errors.to_csv(os.path.join(os.getcwd(), "data", "temp_init_round_error_%s.csv" % project_name))
end_time = datetime.datetime.now()
print("duration: ", end_time - start_time)

# init_triage_history = init_triage_history.sort_values(by=["distance"])
# init_triage_history.to_csv(os.path.join(os.getcwd(), "data", "temp_triage_%s_new_new_init.csv" % project_name))
# predict_top_3 = init_triage_history.iloc[:3]["triage_type"]
# print(pd.value_counts(predict_top_3))
# print(pd.value_counts(predict_top_3).index[0])
# predict_list = []
# for p in predict_top_3:
#     predict_list.append(p)
# print(predict_list)

