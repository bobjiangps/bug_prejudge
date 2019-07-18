from utils.mysql_helper import MysqlConnection
from utils.file_helper import FileHelper
from utils.error_analyzer import ErrorAnalyzer
from configuration.config import Config
from fuzzywuzzy import fuzz
import pandas as pd
import os


def generate_regression_history_data(db_conn, project_id, file_path):
    generate_flag = Config.load_env("generate_regression_history")
    if not os.path.exists(regression_history_file):
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


if __name__ == "__main__":
    # preparation
    test_round_id = Config.load_env("test_round_id")
    response = {"id": test_round_id, "message": None, "scripts": [], "cases": []}
    data_folder = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)
    regression_db = MysqlConnection().connect("local_regression")

    # test round
    current_test_round = regression_db.get_first_result_from_database("select * from test_rounds where id=%d;" % int(test_round_id))
    print("specified test round information:\n", current_test_round)
    regression_history_file = os.path.join(os.getcwd(), "data", "history_regression_%s.csv" % current_test_round["project_id"])
    test_round_errors_file = os.path.join(os.getcwd(), "data", "test_round_errors.csv")

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

    if generate_error_result:
        round_errors = pd.read_csv(test_round_errors_file)
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
    else:
        print("go to simple prejudge")
        #todo, mark the pass and not-run results

    print(response)
