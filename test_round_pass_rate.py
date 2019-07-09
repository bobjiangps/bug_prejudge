from utils.mysql_helper import MysqlConnection
from configuration.config import Config
import os


def generate_history_regression_data(dbconn, project_id, filename="history_regression.csv"):
    generate_flag = Config.load_env()["generate_history_regression"]
    history_regression_file = os.path.join(os.getcwd(), "data", filename)
    if not os.path.exists(history_regression_file):
        generate_flag = True
    data_folder = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    if generate_flag:
        print("----generate history regression data----")
        # query history data of 6 month for reference
        six_month_regression_sql = "select * from test_rounds where project_id=%d and DATE_SUB(CURDATE(), INTERVAL 6 MONTH) <= date(start_time) and end_time is not NULL;" % int(project_id)
        history_regression = dbconn.get_all_results_from_database(six_month_regression_sql)
        with open(history_regression_file, "w") as f:
            f.write(",".join(history_regression[0].keys()) + "\n")
            for row in history_regression:
                new_row = [str(x).replace("\r", " ").replace("\n", " ").replace(",", " ") for x in row.values()]
                f.write(",".join(new_row) + "\n")
        print("there are %d rows in database when query the sql" % len(history_regression))
    else:
        print("----NOT generate history regression data----")


if __name__ == "__main__":
    # test_round_id = input("Please input test round id you want to check:\n")  # 97585 for test
    test_round_id = 97585
    db = MysqlConnection().connect("local_regression")
    current_test_round = db.get_first_result_from_database("select * from test_rounds where id=%d;" % int(test_round_id))
    print("specified test round infomation:\n", current_test_round)
    generate_history_regression_data(db, current_test_round["project_id"])
