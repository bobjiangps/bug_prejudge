from utils.mysql_helper import MysqlConnection
from configuration.config import Config
import os
import pandas as pd


def generate_history_regression_data(dbconn, project_id, filepath):
    generate_flag = Config.load_env()["generate_history_regression"]
    if not os.path.exists(filepath):
        generate_flag = True
    data_folder = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

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


if __name__ == "__main__":
    # test_round_id = input("Please input test round id you want to check:\n")  # 97585 for test
    test_round_id = 97585
    db = MysqlConnection().connect("local_regression")
    current_test_round = db.get_first_result_from_database("select * from test_rounds where id=%d;" % int(test_round_id))
    print("specified test round infomation:\n", current_test_round)
    history_regression_file = os.path.join(os.getcwd(), "data", "history_regression.csv")
    generate_history_regression_data(db, current_test_round["project_id"], history_regression_file)

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
        print("10% quantile is:", history.loc[history["test_suite_id"] == current_test_round["test_suite_id"]].pass_rate.quantile(.1))
        print("current pass rate is:", current_test_round["pass_rate"])
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
