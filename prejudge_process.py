from utils.mysql_helper import MysqlConnection
from utils.file_helper import FileHelper
from utils.error_analyzer import ErrorAnalyzer
from utils.simple_prejudge_helper import SimplePrejudgeHelper
from utils.ml_prejudge_helper import MLPrejudgeHelper
from configuration.config import Config
from datetime import datetime
import pandas as pd
import os


class PrejudgeProcess:

    def __init__(self, round_id=None, script_id=None, case_id=None):
        self.test_round_id = round_id
        self.automation_script_result_id = script_id
        self.automation_case_result_id = case_id

    def run(self):
        start_time = datetime.now()
        response = {"id": self.test_round_id, "message": ""}
        data_folder = os.path.join(os.getcwd(), "data")
        if not os.path.exists(data_folder):
            os.mkdir(data_folder)
        regression_db = MysqlConnection().connect("local_regression")

        # test round
        current_test_round = regression_db.get_first_result_from_database("select * from test_rounds where id=%d;" % int(self.test_round_id))
        print("specified test round information:\n", current_test_round)
        project_name = regression_db.get_first_result_from_database("select name from projects where id=%d" % int(current_test_round["project_id"]))["name"]
        regression_history_file = os.path.join(os.getcwd(), "data", "regression_history_%s.csv" % project_name)
        triage_history_file = os.path.join(os.getcwd(), "data", "triage_history.csv")

        # generate regression history
        self.generate_regression_history_data(regression_db, current_test_round["project_id"], regression_history_file)

        # decide normal test round or not
        regression_history = pd.read_csv(regression_history_file)
        to_drop = ["counter", "sprint", "exist_regression_report"]
        regression_history.drop(columns=to_drop, inplace=True)
        if current_test_round["test_suite_id"] not in regression_history["test_suite_id"]:
            print("Test round with new test suite, no history record")
            # check pass rate line for new test suite
            if current_test_round["pass_rate"] < Config.load_env("pass_rate_line"):
                print("NOT normal Test Round !!! need to check error messages first")
                normal_round = False  # normal_round to be used in future
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
        round_errors = self.generate_test_round_errors_data(regression_db)
        round_all_results = self.generate_test_round_results_data(regression_db)
        if len(round_errors) > 0:
            # if normal_round:
            #     most_failure_element = ErrorAnalyzer.check_element_caused_most_failures(round_errors)
            #     response["message"] = "The element '%s' has most failures: %d times" % (most_failure_element[0], most_failure_element[1])
            # else:
            #     network_error_percentage = ErrorAnalyzer.check_network_issue_percentage(round_errors)
            #     if network_error_percentage > 0.5:
            #         response["message"] = "More than 50%% of failures are caused by network issue, please check environment then rerun test round %d" % test_round_id
            #     else:
            #         most_failure_element = ErrorAnalyzer.check_element_caused_most_failures(round_errors)
            #         response["message"] = "The element '%s' has most failures: %d times" % (most_failure_element[0], most_failure_element[1])

            if not os.path.exists(triage_history_file):
                print("not exist triage history file")
                os.system("python generate_triage_history.py")
            else:
                print("exist triage history file")
            init_triage_history = pd.read_csv(triage_history_file, index_col=0)
            init_triage_history = init_triage_history[init_triage_history["project"] == project_name]
            has_triage = True if len(init_triage_history) > Config.load_env("triage_trigger_ml") else False

            # different logic with has_triage flag
            if has_triage:
                print("go to ml prejudge")
                if Config.load_env("algorithm") == "knn":
                    init_test_round_results = self.generate_test_round_results_data_ml(regression_db)
                    response["scripts"] = MLPrejudgeHelper.prejudge_all(init_triage_history, init_test_round_results, algorithm="knn")
                    response["type"] = "knn"
                elif Config.load_env("algorithm") == "logistic":
                    project_parameter_file = os.path.join(os.getcwd(), "data", "parameter_%s.csv" % project_name)
                    project_parameter = pd.read_csv(project_parameter_file)
                    init_test_round_results = self.generate_test_round_results_data_ml(regression_db)
                    response["scripts"] = MLPrejudgeHelper.prejudge_all(project_parameter, init_test_round_results, algorithm="logistic")
                    response["type"] = "logistic"
                else:
                    raise Exception("unknown algorithm")

                # print("go to ml prejudge")
                # init_triage_history["script_duration"].replace("None", 0, inplace=True)
                # init_triage_history["script_duration"] = pd.to_numeric(init_triage_history["script_duration"])
                # init_test_round_results = self.generate_test_round_results_data_ml(regression_db)
                # # response["scripts"] = MLPrejudgeHelper.neighbor_classifier(init_triage_history, init_test_round_results)
                # response["scripts"] = MLPrejudgeHelper.prejudge_all(init_triage_history, init_test_round_results)
                # response["type"] = "ml"
            else:
                print("go to simple prejudge")
                response["scripts"] = SimplePrejudgeHelper.prejudge_all(round_all_results)
                response["type"] = "simple"
        else:
            print("go to simple prejudge")
            response["scripts"] = SimplePrejudgeHelper.prejudge_all(round_all_results)
            response["type"] = "simple"

        response["message"] = self.summary_prejudged_errors(response["scripts"])
        response["time"] = str(datetime.now())
        end_time = datetime.now()
        print(f"duration: {end_time - start_time}")
        return response

    @staticmethod
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

    def generate_test_round_errors_data(self, db_conn):
        test_round_errors_sql = "SELECT * FROM automation_case_results where automation_script_result_id in (select id from automation_script_results where test_round_id=%d) and result = 'failed';" % int(self.test_round_id)
        print("generate test round errors data")
        con = db_conn.get_conn()
        test_round_errors = pd.read_sql(test_round_errors_sql, con)
        con.close()
        if len(test_round_errors) == 0:
            print("no errors in this test round with id: %d" % int(self.test_round_id))
            return []
        else:
            print("there are %d rows in database when query the round error\n" % len(test_round_errors))
            return test_round_errors

    def generate_test_round_results_data(self, db_conn):
        if self.automation_case_result_id:
            test_round_results_sql = "SELECT * FROM automation_case_results where id=%d;" % int(self.automation_case_result_id)
        elif self.automation_script_result_id:
            test_round_results_sql = "SELECT * FROM automation_case_results where automation_script_result_id=%d;" % int(self.automation_script_result_id)
        else:
            test_round_results_sql = "SELECT * FROM automation_case_results where automation_script_result_id in (select id from automation_script_results where test_round_id=%d);" % int(self.test_round_id)
        print("generate test round all results data")
        con = db_conn.get_conn()
        test_round_results = pd.read_sql(test_round_results_sql, con)
        con.close()
        if len(test_round_results) == 0:
            print("no result in this test round with id: %d" % int(self.test_round_id))
            return []
        else:
            print("there are %d rows in database when query the round all results\n" % len(test_round_results))
            return test_round_results

    def generate_test_round_results_data_ml(self, db_conn):
        if self.automation_case_result_id:
            suffix = "where acr.id=%d;" % int(self.automation_case_result_id)
        elif self.automation_script_result_id:
            suffix = "where asr.id=%d;" % int(self.automation_script_result_id)
        else:
            suffix = "where tr.id=%d;" % int(self.test_round_id)
        print("generate test round all results data for ml")
        test_round_results_sql = """SELECT tr.id as round_id, acr.result, acr.automation_case_id, asr.automation_script_id, acr.id as automation_case_result_id, asr.id as automation_script_result_id,
                                    te.name as env, b.name as browser, acr.error_message, (UNIX_TIMESTAMP(asr.end_time)-UNIX_TIMESTAMP(asr.start_time)) as script_duration FROM `automation_case_results` as acr
                                    left join `automation_script_results` as asr on acr.automation_script_result_id=asr.id
                                    left join `test_rounds` as tr on asr.test_round_id=tr.id
                                    left join `test_environments` as te on tr.test_environment_id=te.id
                                    left join `browsers` as b on tr.browser_id=b.id
                                    left join `projects` as p on p.id=tr.project_id
                                    left join `error_types` as et on et.id=acr.error_type_id %s;
                                    """ % suffix
        con = db_conn.get_conn()
        test_round_results = pd.read_sql(test_round_results_sql, con)
        con.close()
        return test_round_results

    @staticmethod
    def summary_prejudged_errors(results):
        summary = {}
        for v in results.values():
            if v["result"] not in ["not-run", "pass"]:
                for c in v["cases"].values():
                    if c not in ["not-run", "pass"]:
                        if c not in summary.keys():
                            summary[c] = 1
                        else:
                            summary[c] += 1
        return summary
