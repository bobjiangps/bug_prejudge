from utils.mysql_helper import MysqlConnection
from utils.simple_prejudge_helper import SimplePrejudgeHelper
import pandas as pd
import math


class MLPrejudgeHelper:

    regression_db = MysqlConnection().connect("local_regression")

    @classmethod
    def neighbor_classifier(cls, init_triage_history, neighbor=3):
        triage_history = init_triage_history.copy()
        triage_history["avg_duration"] = triage_history["automation_script_id"].apply(lambda x: cls.get_avg_duration_of_script(cls.regression_db, x))
        triage_history["error_type"] = triage_history["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
        triage_history["duration_offset"] = triage_history["script_duration"] - triage_history["avg_duration"]
        min_duration = triage_history["duration_offset"].min()
        max_duration = triage_history["duration_offset"].max()
        triage_history["duration"] = triage_history["duration_offset"].apply(lambda x: (x - min_duration) / (max_duration - min_duration))
        triage_history = pd.get_dummies(triage_history, columns=["env"], prefix_sep="_")
        triage_history = pd.get_dummies(triage_history, columns=["browser"], prefix_sep="_")
        triage_history = pd.get_dummies(triage_history, columns=["error_type"], prefix_sep="_")
        to_drop = ["round_id", "project", "automation_case_id", "automation_script_id", "error_message", "script_duration", "avg_duration", "duration_offset"]
        triage_history.drop(columns=to_drop, inplace=True)

        round_id_for_test = 98251  # debug, remove
        test_round_errors_sql = """SELECT tr.id as round_id, acr.automation_case_id, asr.automation_script_id, te.name as env, b.name as browser, acr.error_message, (UNIX_TIMESTAMP(asr.end_time)-UNIX_TIMESTAMP(asr.start_time)) as script_duration FROM `automation_case_results` as acr
                                    left join `automation_script_results` as asr on acr.automation_script_result_id=asr.id
                                    left join `test_rounds` as tr on asr.test_round_id=tr.id
                                    left join `test_environments` as te on tr.test_environment_id=te.id
                                    left join `browsers` as b on tr.browser_id=b.id
                                    left join `projects` as p on p.id=tr.project_id
                                    left join `error_types` as et on et.id=acr.error_type_id
                                    where tr.id=%d and acr.result='failed';
                                    """ % round_id_for_test
        con = cls.regression_db.get_conn()
        init_test_round_errors = pd.read_sql(test_round_errors_sql, con)
        con.close()
        init_test_round_errors["error_type"] = init_test_round_errors["error_message"].apply(lambda x: SimplePrejudgeHelper.prejudge_error_message(x))
        test_round_errors = init_test_round_errors.copy()
        test_round_errors["avg_duration"] = test_round_errors["automation_script_id"].apply(lambda x: cls.get_avg_duration_of_script(cls.regression_db, x))
        test_round_errors["duration_offset"] = test_round_errors["script_duration"] - test_round_errors["avg_duration"]
        min_duration = test_round_errors["duration_offset"].min()
        max_duration = test_round_errors["duration_offset"].max()
        if min_duration == max_duration:
            test_round_errors["duration"] = test_round_errors["duration_offset"].apply(lambda x: 1)
        else:
            test_round_errors["duration"] = test_round_errors["duration_offset"].apply(lambda x: (x - min_duration) / (max_duration - min_duration))
        test_round_errors = pd.get_dummies(test_round_errors, columns=["env"], prefix_sep="_")
        test_round_errors = pd.get_dummies(test_round_errors, columns=["browser"], prefix_sep="_")
        test_round_errors = pd.get_dummies(test_round_errors, columns=["error_type"], prefix_sep="_")
        to_drop = ["round_id", "automation_case_id", "automation_script_id", "error_message", "script_duration", "avg_duration", "duration_offset"]
        test_round_errors.drop(columns=to_drop, inplace=True)
        missing_columns = list(set(triage_history.columns.values) ^ set(test_round_errors.columns.values))
        for column in missing_columns:
            test_round_errors[column] = 0
        test_round_errors.drop(columns=["triage_type"], inplace=True)
        init_triage_history["distance"] = "tbd"
        init_test_round_errors["predict_triage"] = "tbd"

        distance = []
        knn_columns = test_round_errors.columns.values
        for seq in range(len(test_round_errors)):
            error = test_round_errors.iloc[seq]
            for index, row in triage_history.iterrows():
                distance_sum = 0
                for column in knn_columns:
                    distance_sum += math.pow(getattr(row, column) - error[column], 2)
                distance.append(math.sqrt(distance_sum))
                init_triage_history.loc[index, "distance"] = math.sqrt(distance_sum)
            init_triage_history = init_triage_history.sort_values(by=["distance"])
            predict_top = init_triage_history.iloc[:neighbor]["triage_type"]
            init_test_round_errors.loc[seq, "predict_triage"] = pd.value_counts(predict_top).index[0]

        # features = ["duration", "env_LV-PERF", "env_LV-QA", "env_LV-REG", "browser_chrome", "browser_ie", "error_type_code error", "error_type_element not found",
        #             "error_type_execution environment issue", "error_type_network issue", "error_type_other", "error_type_suspect bug"]
        # triage = triage_history[features]
        # labels = triage_history["triage_type"]
        # knn = KNeighborsClassifier(n_neighbors=neighbor)
        # knn.fit(triage, labels)
        # label_values = knn.classes_
        # for seq in range(len(test_round_errors)):
        #     print(seq)
        #     print(knn.predict([test_round_errors.iloc[seq, [i for i in range(12)]]]))
        #     print(knn.predict_proba([test_round_errors.iloc[seq, [i for i in range(12)]]]))

        return "123"

    @staticmethod
    def get_avg_duration_of_script(db_conn, script_id):
        avg_duration_sql = "select avg(UNIX_TIMESTAMP(end_time)-UNIX_TIMESTAMP(start_time)) as avg_duration from `automation_script_results` where automation_script_id=%s and DATE_SUB(CURDATE(), INTERVAL 12 MONTH) <= date(end_time)" % str(script_id)
        avg_duration = db_conn.get_first_result_from_database(avg_duration_sql)["avg_duration"]
        return avg_duration

