class RerunAnalyzer:

    def __init__(self, test_round_id, test_script_id, automation_script_result_id, db_conn):
        self.round_id = test_round_id
        self.script_id = test_script_id
        self.script_result_id = automation_script_result_id
        self.db_conn = db_conn

    def get_script_result_if_has_triage_result_before_rerun(self):
        triage_rerun_sql = """SELECT asr.id, et.name, asr.prejudge_type FROM `automation_script_results` as asr
                              left join error_types as et on et.id = asr.error_type_id 
                              where asr.automation_script_id=%s 
                              and asr.test_round_id=%s 
                              and asr.triage_result is not null 
                              and asr.triage_result != 'N/A'
                              and asr.id <= %d
                              order by id desc""" % (str(self.script_id), str(self.round_id), int(self.script_result_id))
        print(triage_rerun_sql)
        result = self.db_conn.get_first_result_from_database(triage_rerun_sql)
        if result:
            return {"automation_script_result_id": result["id"],
                    "triaged_error_type": result["name"],
                    "prejudged_type": result["prejudge_type"]}
        else:
            return False
