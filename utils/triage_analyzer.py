from fuzzywuzzy import fuzz
from configuration import classification


class TriageAnalyzer:

    error_priority = classification.error_priority
    triage_priority = classification.triage_priority

    def __init__(self, automation_script_result_id, automation_script_result_value, db_conn):
        self.script_result_id = automation_script_result_id
        self.script_result_value = automation_script_result_value
        self.db_conn = db_conn
        self.round_id, self.script_id = self.get_round_id_and_script_id()

    def get_round_id_and_script_id(self):
        round_script_sql = "SELECT test_round_id, automation_script_id FROM `automation_script_results` where id=%d" % int(self.script_result_id)
        result = self.db_conn.get_first_result_from_database(round_script_sql)
        return result["test_round_id"], result["automation_script_id"]

    def get_triaged_script_info_before_rerun(self):
        triage_rerun_sql = """SELECT asr.id, et.name, asr.prejudge_type FROM `automation_script_results` as asr
                              left join error_types as et on et.id = asr.error_type_id
                              where asr.automation_script_id=%s
                              and asr.test_round_id=%s
                              and asr.triage_result is not null
                              and asr.triage_result != 'N/A'
                              and asr.id < %d
                              order by id desc""" % (str(self.script_id), str(self.round_id), int(self.script_result_id))
        result = self.db_conn.get_first_result_from_database(triage_rerun_sql)
        if result:
            return {"previous_script_result_id": result["id"],
                    "triaged_error_type": result["name"],
                    "prejudged_type": result["prejudge_type"]}
        else:
            return False

    def script_updated_or_not_after_test_round_started(self):
        script_updated_during_round_sql = """SELECT ass.updated_at > tr.start_time as updated FROM `automation_scripts` as ass
                                             join `test_rounds` as tr
                                             where ass.id=%d and tr.id=%d""" % (int(self.script_id), int(self.round_id))
        result = self.db_conn.get_first_result_from_database(script_updated_during_round_sql)
        if result["updated"]:
            return True
        else:
            return False

    def get_failed_case_info_of_script_result(self, script_result_id):
        failed_case_info_sql = """SELECT error_message, automation_case_id, prejudge_type FROM `automation_case_results`
                                  where automation_script_result_id=%d
                                  and error_message is not NULL and error_message != ''""" % int(script_result_id)
        result = self.db_conn.get_all_results_from_database(failed_case_info_sql)
        new_result = {}
        for case in result:
            new_result[case["automation_case_id"]] = {"prejudged_type": case["prejudge_type"],
                                                      "error_message": case["error_message"]}
        return new_result

    def inherit_triage_or_not(self):
        triaged = self.get_triaged_script_info_before_rerun()
        inherit_triage = False
        if triaged:
            # 如果和上次的错误的case一致，并且错误的case的error message基本一样，那么给出原先的triage结果，标明来自上一次。
            # 如果和上次的错误的case一致但是多出来了错误case，一致的case的error message基本一样，那么检查增加的case错误类型，如果优先级高则给该类型，否则给出原先的结果。
            # 如果比上次的错误的case少，但是错误的case都包含在上次的case中，且错误的case的error message基本一样，那么给出原先的triage结果。
            # 如果和上次的错误case不一致，不用检查error message，按新结果处理（因为可能是有新的产品代码提交导致，或者可能是因为环境因素导致, 或者可能是之前标注错误）
            previous_failed_case_info = self.get_failed_case_info_of_script_result(triaged["previous_script_result_id"])
            current_failed_case_info = self.get_failed_case_info_of_script_result(self.script_result_id)
            if set(previous_failed_case_info.keys()) >= set(current_failed_case_info.keys()):
                for case_id in current_failed_case_info.keys():
                    previous_case = previous_failed_case_info[case_id]
                    current_case = current_failed_case_info[case_id]
                    if (fuzz.ratio(str(previous_case["error_message"]), str(current_case["error_message"])) >= 90) and (previous_case["prejudged_type"] == current_case["prejudged_type"]):
                        inherit_triage = True
                    else:
                        inherit_triage = False
                        break
            elif set(previous_failed_case_info.keys()) < set(current_failed_case_info.keys()):
                if self.error_priority[self.script_result_value["result"]] < self.triage_priority[triaged["triaged_error_type"]]:
                    inherit_triage = False
                else:
                    for case_id in previous_failed_case_info.keys():
                        previous_case = previous_failed_case_info[case_id]
                        current_case = current_failed_case_info[case_id]
                        if (fuzz.ratio(str(previous_case["error_message"]), str(current_case["error_message"])) >= 90) and (previous_case["prejudged_type"] == current_case["prejudged_type"]):
                            inherit_triage = True
                        else:
                            inherit_triage = False
                            break
            else:
                inherit_triage = False
        if inherit_triage:
            return triaged["triaged_error_type"]
        else:
            return False
