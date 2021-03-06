from utils.mysql_helper import MysqlConnection
from utils.file_helper import FileHelper
from utils.error_analyzer import ErrorAnalyzer
from utils.simple_prejudge_helper import SimplePrejudgeHelper
from configuration.config import Config, CommandParser
from fuzzywuzzy import fuzz
from datetime import datetime
import pandas as pd
import os
import json


def generate_regression_history_data(db_conn, project_id, file_path):
    generate_flag = Config.load_env("generate_regression_history")
    if not os.path.exists(file_path):
        generate_flag = True
    if generate_flag:
        print("generate history regression data")
        # select history data of 12 month for reference
        period_regression_sql = "select * from test_rounds where project_id=%d and DATE_SUB(CURDATE(), INTERVAL 12 MONTH) <= date(start_time) and end_time is not NULL;" % int(project_id)
        period_regression_history = db_conn.get_all_results_from_database(period_regression_sql)
        FileHelper.save_db_query_result_to_csv(period_regression_history, file_path)
        print("there are %d rows in database when query the history\n" % len(period_regression_history))
    else:
        print("NOT generate history regression data\n")


def generate_test_round_errors_data(db_conn, round_id, file_path):
    test_round_errors_sql = "SELECT * FROM automation_case_results where automation_script_result_id in (select id from automation_script_results where test_round_id=%d) and result = 'failed';" % int(round_id)
    print("generate test round errors data")
    test_round_errors = db_conn.get_all_results_from_database(test_round_errors_sql)
    if len(test_round_errors) == 0:
        print("no errors in this test round with id: %d" % int(round_id))
        return False
    else:
        FileHelper.save_db_query_result_to_csv(test_round_errors, file_path)
        print("there are %d rows in database when query the round error\n" % len(test_round_errors))
        return True


def generate_test_round_results_data(db_conn, file_path, round_id=None, script_id=None, case_id=None):
    # test_round_results_sql = "SELECT * FROM automation_case_results where automation_script_result_id in (2609677, 2609831, 2609879, 2609971, 2610080, 2610095, 2610333, 2610366, 2610380, 2610415, 2609629, 2609636, 2609638, 2609644, 2609651, 2609663);"
    if case_id:
        test_round_results_sql = "SELECT * FROM automation_case_results where id=%d;" % int(case_id)
    elif script_id:
        test_round_results_sql = "SELECT * FROM automation_case_results where automation_script_result_id=%d;" % int(script_id)
    else:
        test_round_results_sql = "SELECT * FROM automation_case_results where automation_script_result_id in (select id from automation_script_results where test_round_id=%d);" % int(round_id)
    print("generate test round all results data")
    test_round_results = db_conn.get_all_results_from_database(test_round_results_sql)
    if len(test_round_results) == 0:
        print("no result in this test round with id: %d" % int(round_id))
        return False
    else:
        FileHelper.save_db_query_result_to_csv(test_round_results, file_path)
        print("there are %d rows in database when query the round all results\n" % len(test_round_results))
        return True


def generate_triage_history_data(db_conn, project_name, file_path):
    # triage_history_sql = "SELECT * FROM `automation_case_results` where triage_result is not NULL and error_type_id in (select id from error_types where name in ('Product Error', 'Product Change')) and automation_script_result_id in (select id from automation_script_results where triage_result is not NULL and automation_script_id in (select id from automation_scripts where project_id=2))"
    # triage_history_sql = "SELECT * FROM `automation_case_results` where error_type_id in (select id from error_types) and automation_script_result_id in (select id from automation_script_results where automation_script_id in (select id from automation_scripts where project_id=2))"
    triage_history_sql = "select * from prejudge_seeds where project_name='%s'" % project_name
    print("generate triage history data")
    triage_history = db_conn.get_all_results_from_database(triage_history_sql)
    if len(triage_history) == 0:
        print("no triage history in project: %s" % project_name)
        return False
    else:
        FileHelper.save_db_query_result_to_csv(triage_history, file_path)
        print("there are %d rows in database when query the triage history of project: %s\n" % (len(triage_history), project_name))
        return True


if __name__ == "__main__":
    # preparation
    start_time = datetime.now()
    args = CommandParser.args()
    test_round_id = args.round_id
    automation_script_result_id = args.script_id
    automation_case_result_id = args.case_id
    # test_round_id = Config.load_env("test_round_id")
    response = {"id": test_round_id, "message": ""}
    data_folder = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)
    regression_db = MysqlConnection().connect("local_regression")

    # test round
    current_test_round = regression_db.get_first_result_from_database("select * from test_rounds where id=%d;" % int(test_round_id))
    print("specified test round information:\n", current_test_round)
    project_name = regression_db.get_first_result_from_database("select name from projects where id=%d" % int(current_test_round["project_id"]))["name"]
    regression_history_file = os.path.join(os.getcwd(), "data", "regression_history_%s.csv" % project_name)
    test_round_errors_file = os.path.join(os.getcwd(), "data", "test_round_errors.csv")
    test_round_all_results_file = os.path.join(os.getcwd(), "data", "test_round_results.csv")
    triage_history_file = os.path.join(os.getcwd(), "data", "triage_history_%s.csv" % project_name)

    # generate regression history
    generate_regression_history_data(regression_db, current_test_round["project_id"], regression_history_file)

    # decide normal test round or not
    regression_history = pd.read_csv(regression_history_file)
    to_drop = ["counter", "sprint", "exist_regression_report"]
    regression_history.drop(columns=to_drop, inplace=True)
    normal_round = None
    if current_test_round["test_suite_id"] not in regression_history["test_suite_id"]:
        print("Test round with new test suite, no history record")
        # check pass rate line for new test suite
        if current_test_round["pass_rate"] < Config.load_env("pass_rate_line"):
            print("NOT normal Test Round !!! need to check error messages first")
            normal_round = False
        else:
            print("Normal Test Round..")
            normal_round = True
    else:
        pass_rate_quantile_ten_percent = regression_history.loc[regression_history["test_suite_id"] == current_test_round["test_suite_id"]].pass_rate.quantile(.1)
        average_pass_rate = regression_history.loc[regression_history["test_suite_id"] == current_test_round["test_suite_id"]].pass_rate.mean()
        print("10% quantile is:", "%.2f%%" % pass_rate_quantile_ten_percent)
        print("current pass rate is:", "%.2f%%" % current_test_round["pass_rate"])
        if (current_test_round["pass_rate"] <= pass_rate_quantile_ten_percent) or ((average_pass_rate - current_test_round["pass_rate"]) > Config.load_env("pass_rate_offset") * 100):
            print("NOT normal Test Round !!! need to check error messages first")
            normal_round = False
        else:
            print("Normal Test Round..")
            normal_round = True

    # generate error data
    generate_error_result = generate_test_round_errors_data(regression_db, test_round_id, test_round_errors_file)
    round_errors = pd.read_csv(test_round_errors_file)
    generate_all_result = generate_test_round_results_data(regression_db, test_round_all_results_file, round_id=test_round_id, script_id=automation_script_result_id, case_id=automation_case_result_id)
    round_all_results = pd.read_csv(test_round_all_results_file)

    if generate_error_result:
        # normal_round = False  # debug, will be removed
        if normal_round:
            most_failure_element = ErrorAnalyzer.check_element_caused_most_failures(round_errors)
            response["message"] = "The element '%s' has most failures: %d times" % (most_failure_element[0], most_failure_element[1])
        else:
            network_error_percentage = ErrorAnalyzer.check_network_issue_percentage(round_errors)
            if network_error_percentage > 0.5:
                response["message"] = "More than 50%% of failures are caused by network issue, please check environment then rerun test round %d" % test_round_id
            else:
                most_failure_element = ErrorAnalyzer.check_element_caused_most_failures(round_errors)
                response["message"] = "The element '%s' has most failures: %d times" % (most_failure_element[0], most_failure_element[1])

        # check whether has triage history or not
        has_triage = None
        if os.path.exists(triage_history_file):
            has_triage = True
        else:
            prejudge_db = MysqlConnection().connect("local_prejudge")
            has_triage = generate_triage_history_data(prejudge_db, project_name, triage_history_file)

        # different logic with has_triage flag
        has_triage = False # debug, remove
        if has_triage:
            print("go to detail prejudge")
            # todo
        else:
            print("go to simple prejudge")
            # for index in range(len(round_errors)):
            #     case = round_errors.iloc[[index]]
            #     case_prejudge_result = SimplePrejudgeHelper.prejudge_case(case)
            #     response["cases"][case.id[index]] = {"script_result_id": case.automation_script_result_id[index], "result": case_prejudge_result}
            response["scripts"] = SimplePrejudgeHelper.prejudge_all(round_all_results)
    else:
        print("go to simple prejudge")
        response["scripts"] = SimplePrejudgeHelper.prejudge_all(round_all_results)

    # response["scripts"] = SimplePrejudgeHelper.summarize_script_by_prejudged_case(response["cases"])
    response["time"] = str(datetime.now())
    if Config.load_env("response_into_file"):
        with open(os.path.join(os.getcwd(), "data", "response.json"), "w") as f:
            json.dump(response, f)
    end_time = datetime.now()
    print(f"duration: {end_time - start_time}")
