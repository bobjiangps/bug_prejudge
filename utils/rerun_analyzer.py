class RerunAnalyzer:

    def __init__(self, automation_script_result_id, db_conn):
        self.script_result_id = automation_script_result_id
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
                                  where automation_script_result_id=%d""" % int(script_result_id)
        result = self.db_conn.get_all_results_from_database(failed_case_info_sql)
        new_result = {}
        for case in result:
            new_result[case["automation_case_id"]] = {"prejudged_type": case["prejudge_type"],
                                                      "error_message": case["error_message"]}
        return new_result
