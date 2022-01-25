from utils.mysql_helper import MysqlConnection
from utils.simple_prejudge_helper import SimplePrejudgeHelper
from utils.triage_analyzer import TriageAnalyzer
from utils.gradient import sigmoid
from configuration import classification
from fuzzywuzzy import fuzz
import pandas as pd
import math
import os


class MLPrejudgeHelper:

    regression_db = MysqlConnection().connect("local_regression")

    error_priority = classification.error_priority
    triage_priority = classification.triage_priority
    classify = classification.classify

    @classmethod
    def prejudge_all(cls, init_triage_history, init_test_round_results, script_not_case_flag=False, algorithm="knn", logistic_bug_file=None):
        script_result = {}
        if len(init_test_round_results) > 1:
            errors = init_test_round_results[init_test_round_results["result"] == "failed"].copy()
            warning = init_test_round_results[init_test_round_results["result"] == "warning"].copy()
            errors = pd.merge(errors, warning, how="outer")
            not_errors = init_test_round_results[init_test_round_results["result"] != "failed"][init_test_round_results["result"] != "warning"]
            for seq in range(len(not_errors)):
                case = not_errors.iloc[seq]
                script_result_id = str(case.automation_script_result_id)
                case_prejudge_result = SimplePrejudgeHelper.prejudge_case(case)
                if script_result_id not in script_result.keys():
                    script_result[script_result_id] = {"result": case_prejudge_result, "keyword": case_prejudge_result, "cases": {str(case.automation_case_result_id): {"result": case_prejudge_result, "keyword": case_prejudge_result}}}
                else:
                    script_result[script_result_id]["cases"][str(case.automation_case_result_id)] = {"result": case_prejudge_result, "keyword": case_prejudge_result}
                    if cls.error_priority[case_prejudge_result] < cls.error_priority[script_result[script_result_id]["result"]]:
                        script_result[script_result_id]["result"] = case_prejudge_result
            if len(errors) > 0:
                if algorithm == "knn":
                    error_results = cls.neighbor_classifier(init_triage_history, errors)
                    cls.merge_result(script_result, error_results)
                elif algorithm == "logistic":
                    error_results = cls.logistic_regression(init_triage_history, errors, bug_file=logistic_bug_file)
                    cls.merge_result(script_result, error_results)
        else:
            case = init_test_round_results.iloc[[0]]
            script_result_id = str(case.automation_script_result_id[0])
            if case.result[0] in ["pass", "not-run"]:
                case_prejudge_result = SimplePrejudgeHelper.prejudge_case(case.loc[0])
                if script_not_case_flag:
                    script_result[script_result_id] = {"result": case_prejudge_result, "keyword": case_prejudge_result, "cases": {str(case.automation_case_result_id[0]): {"result": case_prejudge_result, "keyword": case_prejudge_result}}}
                else:
                    script_result[script_result_id] = {"result": None, "cases": {str(case.automation_case_result_id[0]): {"result": case_prejudge_result, "keyword": case_prejudge_result}}}
            else:
                if algorithm == "knn":
                    prejudge_result = cls.neighbor_classifier(init_triage_history, case)
                elif algorithm == "logistic":
                    prejudge_result = cls.logistic_regression(init_triage_history, case, bug_file=logistic_bug_file)
                else:
                    prejudge_result = None
                script_result = prejudge_result
                if not script_not_case_flag:
                    script_result[list(script_result.keys())[0]]["result"] = None
                    del script_result[list(script_result.keys())[0]]["keyword"]

        # check the triage history to decide inherit triage type or not, if not need, delete the following block
        for script_result_id in script_result.keys():
            ta = TriageAnalyzer(script_result_id, script_result[script_result_id], cls.regression_db)
            inherit_triage_type = ta.inherit_triage_or_not()
            if inherit_triage_type:
                script_result[script_result_id]["result"] = inherit_triage_type
                script_result[script_result_id]["keyword"] = "Match the rule to inherit previous triaged type"
                for case_result_id in script_result[script_result_id]["cases"]:
                    if script_result[script_result_id]["cases"][case_result_id]["result"].lower() != "pass":
                        script_result[script_result_id]["cases"][case_result_id]["result"] = inherit_triage_type
                        script_result[script_result_id]["cases"][case_result_id]["keyword"] = "Match the rule to inherit previous triaged type"

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

    @classmethod
    def logistic_regression(cls, parameter, init_test_round_errors, bug_file=None):
        prejudge_result = {}
        # init_test_round_errors["error_type"] = init_test_round_errors["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
        init_test_round_errors["error_type"] = init_test_round_errors.apply(SimplePrejudgeHelper.prejudge_error_message_v2, axis=1)
        test_round_errors = init_test_round_errors.copy()
        test_round_errors["avg_duration"] = test_round_errors["automation_script_id"].apply(lambda x: cls.get_avg_duration_of_script(cls.regression_db, x))
        test_round_errors["avg_duration"] = pd.to_numeric(test_round_errors["avg_duration"])
        test_round_errors["duration_offset"] = test_round_errors["script_duration"] - test_round_errors["avg_duration"]
        test_round_errors["duration"] = test_round_errors["duration_offset"] / test_round_errors["avg_duration"]
        # min_duration = test_round_errors["duration_offset"].min()
        # max_duration = test_round_errors["duration_offset"].max()
        # if min_duration == max_duration:
        #     test_round_errors["duration"] = test_round_errors["duration_offset"].apply(lambda x: 1)
        # else:
        #     test_round_errors["duration"] = test_round_errors["duration_offset"].apply(lambda x: (x - min_duration) / (max_duration - min_duration))
        # test_round_errors["duration"] = pd.to_numeric(test_round_errors["duration"])
        test_round_errors = pd.get_dummies(test_round_errors, columns=["env"], prefix_sep="_")
        test_round_errors = pd.get_dummies(test_round_errors, columns=["browser"], prefix_sep="_")
        test_round_errors = pd.get_dummies(test_round_errors, columns=["error_type"], prefix_sep="_")
        to_drop = ["round_id", "result", "automation_case_id", "automation_script_id", "automation_case_result_id", "automation_script_result_id", "error_message", "script_duration", "avg_duration", "duration_offset"]
        test_round_errors.drop(columns=to_drop, inplace=True)
        missing_columns = list(set(parameter.columns.values) ^ set(test_round_errors.columns.values))
        for column in missing_columns:
            if column == "offset":
                test_round_errors[column] = 1
            else:
                test_round_errors[column] = 0
        init_test_round_errors["predict_triage"] = "tbd"
        init_test_round_errors["calculate"] = "tbd"

        existent_bugs = pd.read_csv(bug_file) if bug_file and os.path.exists(bug_file) else []
        columns = parameter.columns.values
        for seq in range(len(test_round_errors)):
            error = test_round_errors.iloc[seq]
            calculate = 0
            for c in columns:
                calculate += error[c] * parameter.loc[0, c]
            sigmoid_calculate = sigmoid(calculate)
            # predict_triage = "Product Error" if sigmoid_calculate > 0.5 else "Not Product Error"
            # predict_triage = "suspect bug" if sigmoid_calculate > 0.5 else init_test_round_errors.iloc[seq]["error_type"]
            predict_match_bug = None
            if sigmoid_calculate > 0.5:
                predict_triage = "suspect bug"
                if len(existent_bugs) > 0:
                    print("check old bug list")
                    init_error = init_test_round_errors.iloc[seq]
                    for bug_seq in range(len(existent_bugs)):
                        temp_bug = existent_bugs.iloc[bug_seq]
                        if str(init_error.automation_case_id) == str(temp_bug.automation_case_id) and str(init_error.automation_script_id) == str(temp_bug.automation_script_id) \
                           and init_error.env == temp_bug.env and init_error.browser == temp_bug.browser and fuzz.ratio(str(init_error.error_message), str(temp_bug.error_message)) >= 95:
                            predict_match_bug = temp_bug.bug_id
                            predict_triage = "existent bug"
                            break
            else:
                predict_triage = init_test_round_errors.iloc[seq]["error_type"]
            init_test_round_errors.loc[seq, "predict_triage"] = predict_triage
            init_test_round_errors.loc[seq, "calculate"] = sigmoid_calculate
            automation_case_result_id = str(int(init_test_round_errors.iloc[seq]["automation_case_result_id"]))
            automation_script_result_id = str(int(init_test_round_errors.iloc[seq]["automation_script_result_id"]))
            if automation_script_result_id not in prejudge_result.keys():
                if predict_match_bug:
                    prejudge_result[automation_script_result_id] = {"result": predict_triage, "keyword": predict_match_bug, "cases": {automation_case_result_id: {"result": predict_triage, "keyword": predict_match_bug}}}
                else:
                    prejudge_result[automation_script_result_id] = {"result": predict_triage, "keyword": predict_triage, "cases": {automation_case_result_id: {"result": predict_triage, "keyword": SimplePrejudgeHelper.extract_error_keyword(predict_triage, init_test_round_errors.iloc[seq]["error_message"])}}}
                    if predict_triage == "element not found":
                        prejudge_result[automation_script_result_id]["keyword"] = list(prejudge_result[automation_script_result_id]["cases"].values())[0]["keyword"]
            else:
                # prejudge_result[automation_script_result_id]["cases"][automation_case_result_id]["result"] = predict_triage
                if predict_match_bug:
                    prejudge_result[automation_script_result_id]["cases"][automation_case_result_id] = {"result": predict_triage, "keyword": predict_match_bug}
                    if prejudge_result[automation_script_result_id]["keyword"] not in cls.error_priority.keys():
                        if predict_match_bug not in prejudge_result[automation_script_result_id]["keyword"].split(","):
                            prejudge_result[automation_script_result_id]["keyword"] += ",%s" % predict_match_bug
                    else:
                        prejudge_result[automation_script_result_id]["keyword"] = predict_match_bug
                else:
                    prejudge_result[automation_script_result_id]["cases"][automation_case_result_id] = {"result": predict_triage, "keyword": SimplePrejudgeHelper.extract_error_keyword(predict_triage, init_test_round_errors.iloc[seq]["error_message"])}
                # if cls.classify[predict_triage] < cls.classify[prejudge_result[automation_script_result_id]["result"]]:
                if cls.error_priority[predict_triage] < cls.error_priority[prejudge_result[automation_script_result_id]["result"]]:
                    if prejudge_result[automation_script_result_id]["result"] == "element not found":
                        prejudge_result[automation_script_result_id]["keyword"] = predict_triage
                    prejudge_result[automation_script_result_id]["result"] = predict_triage
                    if prejudge_result[automation_script_result_id]["keyword"] in cls.error_priority.keys():
                        prejudge_result[automation_script_result_id]["keyword"] = predict_triage
                if prejudge_result[automation_script_result_id]["result"] == "element not found":
                    for case in prejudge_result[automation_script_result_id]["cases"].values():
                        if case["result"] == "element not found":
                            prejudge_result[automation_script_result_id]["keyword"] = case["keyword"]
                            break
        return prejudge_result

    @staticmethod
    def get_avg_duration_of_script(db_conn, script_id):
        error_limit = 10
        duration = 0
        while error_limit:
            try:
                duration_sql = "select (UNIX_TIMESTAMP(end_time)-UNIX_TIMESTAMP(start_time)) as duration from \
                               `automation_script_results` where automation_script_id=%s and DATE_SUB(CURDATE(), INTERVAL 12 MONTH) <= date(end_time) and result='pass'" % str(
                    script_id)
                con = db_conn.get_conn()
                duration_data = pd.read_sql(duration_sql, con)
                con.close()
                if not isnan(duration_data.median()["duration"]):
                    duration = float(duration_data.median())
                break
            except:
                print("error when get median duration")
                error_limit -= 1
        return duration

    @staticmethod
    def merge_result(old_result, new_result):
        old_keys = old_result.keys()
        new_keys = new_result.keys()
        for k in new_keys:
            if k in old_keys:
                old_result[k]["cases"] = dict(old_result[k]["cases"], **new_result[k]["cases"])
                old_result[k]["result"] = new_result[k]["result"]
                try:
                    old_result[k]["keyword"] = new_result[k]["keyword"]
                except KeyError:
                    pass
            else:
                old_result[k] = new_result[k]
        return old_result
