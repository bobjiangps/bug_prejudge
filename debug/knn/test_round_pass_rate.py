from utils.mysql_helper import MysqlConnection
from configuration.config import Config
from collections import Counter
import os
import pandas as pd
import re


def generate_history_regression_data(dbconn, project_id, filepath):
    generate_flag = Config.load_env()["generate_history_regression"]
    if not os.path.exists(filepath):
        generate_flag = True

    if generate_flag:
        print("----generate history regression data----")
        # query history data of 6 month for reference
        six_month_regression_sql = "select * from test_rounds where project_id=%d and DATE_SUB(CURDATE(), INTERVAL 6 MONTH) <= date(start_time) and end_time is not NULL;" % int(project_id)
        history_regression = dbconn.get_all_results_from_database(six_month_regression_sql)
        with open(filepath, "w") as f:
            f.write(",".join(history_regression[0].keys()) + "\n")
            for row in history_regression:
                new_row = [str(x).replace("\r", " ").replace("\n", " ").replace(",", " ") for x in row.values()]
                f.write(",".join(new_row) + "\n")
        print("----there are %d rows in database when query the sql----\n" % len(history_regression))
    else:
        print("----NOT generate history regression data----\n")

def generate_test_round_errors_data(dbconn, round_id, filepath):
    test_round_errors_sql = "SELECT * FROM automation_case_results where automation_script_result_id in (select id from automation_script_results where test_round_id=%d) and result = 'failed';" % int(round_id)
    # test_round_errors_sql = "select * from automation_case_results where result='failed' and error_message like '%Timeout%';"  # to be removed
    print("----generate test round errors data----")
    test_round_erros = dbconn.get_all_results_from_database(test_round_errors_sql)
    if len(test_round_erros) == 0:
        print("no errors in this test round with id: %d" % int(round_id))
        return False
    else:
        with open(filepath, "w") as f:
            f.write(",".join(test_round_erros[0].keys()) + "\n")
            for row in test_round_erros:
                new_row = [str(x).replace("\r", " ").replace("\n", " ").replace(",", " ") for x in row.values()]
                f.write(",".join(new_row) + "\n")
        print("----there are %d rows in database when query the sql----\n" % len(test_round_erros))
        return True


if __name__ == "__main__":
    # test_round_id = input("Please input test round id you want to check:\n")  # 97585 for test
    test_round_id = 97585  # to be removed
    response = {"id": test_round_id, "message": None, "scripts": None, "cases": None}
    data_folder = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)
    regression_db = MysqlConnection().connect("local_regression")
    current_test_round = regression_db.get_first_result_from_database("select * from test_rounds where id=%d;" % int(test_round_id))
    print("specified test round infomation:\n", current_test_round)
    history_regression_file = os.path.join(os.getcwd(), "data", "history_regression.csv")
    generate_history_regression_data(regression_db, current_test_round["project_id"], history_regression_file)

    history = pd.read_csv(history_regression_file)
    to_drop = ["counter", "sprint", "exist_regression_report"]
    history.drop(columns=to_drop, inplace=True)

    normal_round = None
    if current_test_round["test_suite_id"] not in history["test_suite_id"]:
        print("Test round with new test suite, no history record")
        normal_round = True
    else:
        # loc retrieves only the rows that matches the condition
        # print(history.loc[history["test_suite_id"] == current_test_round["test_suite_id"]].count)
        # 分位数，这里代表有90%的值都大于这个数字，那么如果新的值落在这个值以下，可以考虑为可能异常；比如总数14个，N1到N14，(14-1)/10+1=2.3, N2+(N3-N2)*0.3就是10%分位数
        print("10% quantile is:", "%.2f%%" % history.loc[history["test_suite_id"] == current_test_round["test_suite_id"]].pass_rate.quantile(.1))
        print("current pass rate is:", "%.2f%%" % current_test_round["pass_rate"])
        # where returns the whole dataframe, replacing rows that don't match the condition as NaN by default
        # print(history.where(history["test_suite_id"] == current_test_round["test_suite_id"]).count())
        # print(history.where(history["test_suite_id"] == current_test_round["test_suite_id"]).pass_rate.mean())

        pass_rate_quantile_ten_percent = history.loc[history["test_suite_id"] == current_test_round["test_suite_id"]].pass_rate.quantile(.1)
        average_pass_rate = history.loc[history["test_suite_id"] == current_test_round["test_suite_id"]].pass_rate.mean()
        if current_test_round["pass_rate"] <= pass_rate_quantile_ten_percent or (average_pass_rate - current_test_round["pass_rate"]) > Config.load_env()["pass_rate_offset"] * 100:
            print("Unnormal Test Round !!! need to check error messages first")
            normal_round = False
        else:
            print("Normal Test Round..")
            normal_round = True

    normal_round = False  # debug, will be removed
    if normal_round:
        #todo
        print("todo...")
    else:
        test_round_errors_file = os.path.join(os.getcwd(), "data", "test_round_errors.csv")
        # generate_error_result = generate_test_round_errors_data(regression_db, test_round_id, test_round_errors_file)
        generate_error_result = True  # debug, will be removed
        if generate_error_result:
            network_error_keyword = ["Net::ReadTimeout", "Request Timeout"]
            round_errors = pd.read_csv(test_round_errors_file)
            # print(round_errors[round_errors["error_message"].str.contains("|".join(network_error_keyword), flags=re.IGNORECASE, regex=True)])
            round_network_errors = round_errors[round_errors["error_message"].str.contains("|".join(network_error_keyword), flags=re.IGNORECASE, regex=True)]
            network_error_percentage = round_network_errors.id.count()/round_errors.id.count()
            print("network error percentage is:", "%.2f%%" % (network_error_percentage * 100))
            if network_error_percentage > 0.5:
                response["message"] = "More than 50%% of failures are caused by network issue, please check environment then rerun test round %d" % test_round_id
                print("Attention!!! %s" % response["message"])
            else:
                # element_error_keyword = [".*Execute - wait \w*::\w* to present.*", ".*The element.*does not exist.*", ".*Execute - open .*::.*- failed.*", ".*Execute - select .*::.*- failed.*", ".*Execute - get .*::.*- failed.*"]
                # round_element_errors = round_errors[round_errors["error_message"].str.match("|".join(element_error_keyword), flags=re.IGNORECASE)]
                # print(round_element_errors)
                # element_error_keyword = [".*Execute - get (.*::.*)- failed.*"]
                # round_element_errors = round_errors[round_errors["error_message"].str.extract(element_error_keyword[0], flags=re.IGNORECASE, expand=False)]
                # print(round_element_errors)
                element_error_keyword = [".*Execute - wait (\w*::\w*) to present.*", ".*Execute - open .* (\w*::\w*) .*- failed.*", ".*Execute - select .* (\w*::\w*) .*- failed.*", ".*Execute - get .* (\w*::\w*) .*- failed.*"]
                round_element_errors_match = round_errors[round_errors["error_message"].str.match("|".join(element_error_keyword), flags=re.IGNORECASE)]
                round_element_errors_extract = round_element_errors_match.error_message.str.extract("|".join(element_error_keyword), flags=re.IGNORECASE, expand=False)
                print(round_element_errors_extract)  # to be removed
                round_element_errors_record = []
                for seq in round_element_errors_extract:
                    print(seq)  # to be removed
                    for item in round_element_errors_extract[seq]:
                        if str(item) != "nan":
                            print(item)  # to be removed
                            round_element_errors_record.append(item)
                most_failure_element = Counter(round_element_errors_record).most_common(1)
                response["message"] = "The element '%s' has most failures: %d times" % (most_failure_element[0][0], most_failure_element[0][1])
                print(response["message"])


