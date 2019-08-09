from utils.mysql_helper import MysqlConnection
from utils.simple_prejudge_helper import SimplePrejudgeHelper
import pandas as pd
import math


class MLPrejudgeHelper:

    regression_db = MysqlConnection().connect("local_regression")

    error_priority = {
        "suspect bug": 1,
        "element not found": 2,
        "execution environment issue": 3,
        "code error": 4,
        "network issue": 5,
        "other": 6,
        "not-run": 7,
        "pass": 8
    }

    triage_priority = {
        "Product Error": 1,
        "Product Change": 2,
        "Environment Error": 3,
        "Framework Issue": 4,
        "Script Issue": 5,
        "Data Issue": 6,
        "Dynamic Issue": 7,
        "Other": 8,
        "Not in Branch": 9,
        "Not Ready": 10
    }

    @classmethod
    def prejudge_all(cls, init_triage_history, init_test_round_results, algorithm="knn"):
        script_result = {}
        if len(init_test_round_results) > 1:
            errors = init_test_round_results[init_test_round_results["result"] == "failed"].copy()
            not_errors = init_test_round_results[init_test_round_results["result"] != "failed"]
            for seq in range(len(not_errors)):
                case = not_errors.iloc[seq]
                script_result_id = str(case.automation_script_result_id)
                case_prejudge_result = SimplePrejudgeHelper.prejudge_case(case)
                if script_result_id not in script_result.keys():
                    script_result[script_result_id] = {"result": case_prejudge_result, "cases": {str(case.automation_case_result_id): case_prejudge_result}}
                else:
                    script_result[script_result_id]["cases"][str(case.automation_case_result_id)] = case_prejudge_result
                    if cls.error_priority[case_prejudge_result] < cls.error_priority[script_result[script_result_id]["result"]]:
                        script_result[script_result_id]["result"] = case_prejudge_result
            if algorithm == "knn":
                error_results = cls.neighbor_classifier(init_triage_history, errors)
                cls.merge_result(script_result, error_results)
        else:
            case = init_test_round_results.iloc[[0]]
            script_result_id = str(case.automation_script_result_id[0])
            if case.result[0] == "pass":
                case_prejudge_result = SimplePrejudgeHelper.prejudge_case(case)
                script_result[script_result_id] = {"result": None, "cases": {str(case.automation_case_result_id[0]): case_prejudge_result}}
            else:
                if algorithm == "knn":
                    prejudge_result = cls.neighbor_classifier(init_triage_history, case)
                    script_result = prejudge_result
                    script_result[list(script_result.keys())[0]]["result"] = None
        return script_result

    @classmethod
    def neighbor_classifier(cls, init_triage_history, init_test_round_errors, neighbor=3):
        prejudge_result = {}
        triage_history = init_triage_history.copy()
        triage_history["avg_duration"] = triage_history["automation_script_id"].apply(lambda x: cls.get_avg_duration_of_script(cls.regression_db, x))
        triage_history["avg_duration"] = pd.to_numeric(triage_history["avg_duration"])
        triage_history["duration_offset"] = triage_history["script_duration"] - triage_history["avg_duration"]
        min_duration = triage_history["duration_offset"].min()
        max_duration = triage_history["duration_offset"].max()
        triage_history["duration"] = triage_history["duration_offset"].apply(lambda x: (x - min_duration) / (max_duration - min_duration))
        triage_history = pd.get_dummies(triage_history, columns=["env"], prefix_sep="_")
        triage_history = pd.get_dummies(triage_history, columns=["browser"], prefix_sep="_")
        triage_history = pd.get_dummies(triage_history, columns=["error_type"], prefix_sep="_")
        to_drop = ["round_id", "project", "automation_case_id", "automation_script_id", "error_message", "script_duration", "avg_duration", "duration_offset"]
        triage_history.drop(columns=to_drop, inplace=True)

        init_test_round_errors["error_type"] = init_test_round_errors["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
        test_round_errors = init_test_round_errors.copy()
        test_round_errors["avg_duration"] = test_round_errors["automation_script_id"].apply(lambda x: cls.get_avg_duration_of_script(cls.regression_db, x))
        test_round_errors["avg_duration"] = pd.to_numeric(test_round_errors["avg_duration"])
        test_round_errors["duration_offset"] = test_round_errors["script_duration"] - test_round_errors["avg_duration"]
        min_duration = test_round_errors["duration_offset"].min()
        max_duration = test_round_errors["duration_offset"].max()
        if min_duration == max_duration:
            test_round_errors["duration"] = test_round_errors["duration_offset"].apply(lambda x: 1)
        else:
            test_round_errors["duration"] = test_round_errors["duration_offset"].apply(lambda x: (x - min_duration) / (max_duration - min_duration))
        test_round_errors["duration"] = pd.to_numeric(test_round_errors["duration"])
        test_round_errors = pd.get_dummies(test_round_errors, columns=["env"], prefix_sep="_")
        test_round_errors = pd.get_dummies(test_round_errors, columns=["browser"], prefix_sep="_")
        test_round_errors = pd.get_dummies(test_round_errors, columns=["error_type"], prefix_sep="_")
        to_drop = ["round_id", "result", "automation_case_id", "automation_script_id", "automation_case_result_id", "automation_script_result_id", "error_message", "script_duration", "avg_duration", "duration_offset"]
        test_round_errors.drop(columns=to_drop, inplace=True)
        missing_columns = list(set(triage_history.columns.values) ^ set(test_round_errors.columns.values))
        for column in missing_columns:
            test_round_errors[column] = 0
        test_round_errors.drop(columns=["triage_type"], inplace=True)
        init_triage_history["distance"] = "tbd"
        init_test_round_errors["predict_triage"] = "tbd"

        knn_columns = test_round_errors.columns.values
        for seq in range(len(test_round_errors)):
            error = test_round_errors.iloc[seq]
            for index, row in triage_history.iterrows():
                distance_sum = 0
                for column in knn_columns:
                    distance_sum += math.pow(getattr(row, column) - error[column], 2)
                init_triage_history.loc[index, "distance"] = math.sqrt(distance_sum)
            init_triage_history = init_triage_history.sort_values(by=["distance"])
            predict_top = init_triage_history.iloc[:neighbor]["triage_type"]
            automation_case_result_id = str(int(init_test_round_errors.iloc[seq]["automation_case_result_id"]))
            automation_script_result_id = str(int(init_test_round_errors.iloc[seq]["automation_script_result_id"]))
            predict_triage = pd.value_counts(predict_top).index[0]
            init_test_round_errors.loc[seq, "predict_triage"] = predict_triage
            if automation_script_result_id not in prejudge_result.keys():
                prejudge_result[automation_script_result_id] = {"result": predict_triage, "cases": {automation_case_result_id: predict_triage}}
            else:
                prejudge_result[automation_script_result_id]["cases"][automation_case_result_id] = predict_triage
                if cls.triage_priority[predict_triage] < cls.triage_priority[prejudge_result[automation_script_result_id]["result"]]:
                    prejudge_result[automation_script_result_id]["result"] = predict_triage

        # features = ["duration", "env_LV-PERF", "env_LV-QA", "env_LV-REG", "browser_chrome", "browser_ie", "error_type_code error", "error_type_element not found",
        #             "error_type_execution environment issue", "error_type_network issue", "error_type_other", "error_type_suspect bug"]
        # triage = triage_history[features]
        # labels = triage_history["triage_type"]
        # from sklearn.neighbors import KNeighborsClassifier
        # knn = KNeighborsClassifier(n_neighbors=neighbor)
        # knn.fit(triage, labels)
        # label_values = knn.classes_
        # for seq in range(len(test_round_errors)):
        #     # print(seq)
        #     # print(knn.predict([test_round_errors.iloc[seq, [i for i in range(12)]]]))
        #     # print(knn.predict_proba([test_round_errors.iloc[seq, [i for i in range(12)]]]))
        #     automation_case_result_id = str(int(init_test_round_errors.iloc[seq]["automation_case_result_id"]))
        #     automation_script_result_id = str(int(init_test_round_errors.iloc[seq]["automation_script_result_id"]))
        #     predict_triage = knn.predict([test_round_errors.iloc[seq, [i for i in range(12)]]])[0]
        #     init_test_round_errors.loc[seq, "predict_triage"] = predict_triage
        #     if automation_script_result_id not in prejudge_result.keys():
        #         prejudge_result[automation_script_result_id] = {"result": predict_triage, "cases": {automation_case_result_id: predict_triage}}
        #     else:
        #         prejudge_result[automation_script_result_id]["cases"][automation_case_result_id] = predict_triage
        #         if cls.triage_priority[predict_triage] < cls.triage_priority[prejudge_result[automation_script_result_id]["result"]]:
        #             prejudge_result[automation_script_result_id]["result"] = predict_triage

        return prejudge_result

    @staticmethod
    def get_avg_duration_of_script(db_conn, script_id):
        avg_duration_sql = "select avg(UNIX_TIMESTAMP(end_time)-UNIX_TIMESTAMP(start_time)) as avg_duration from `automation_script_results` where automation_script_id=%s and DATE_SUB(CURDATE(), INTERVAL 12 MONTH) <= date(end_time)" % str(script_id)
        avg_duration = db_conn.get_first_result_from_database(avg_duration_sql)["avg_duration"]
        return avg_duration

    @staticmethod
    def merge_result(old_result, new_result):
        old_keys = old_result.keys()
        new_keys = new_result.keys()
        for k in new_keys:
            if k in old_keys:
                old_result[k]["cases"] = dict(old_result[k]["cases"], **new_result[k]["cases"])
                old_result[k]["result"] = new_result[k]["result"]
            else:
                old_result[k] = new_result[k]
        return old_result
