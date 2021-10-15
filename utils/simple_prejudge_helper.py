import re
from utils.mysql_helper import MysqlConnection
from utils.triage_analyzer import TriageAnalyzer
from configuration import classification


class SimplePrejudgeHelper:

    regression_db = MysqlConnection().connect("local_regression")

    error_priority = classification.error_priority

    log_error_re = [".*(in .?logger_error).*", ".*(AssertionError).*"]
    assert_fail_re = [".*(Assert -.*- failed).*"]
    expectation_fail_re = [".*(expected.*got.*\n).*\.+", ".*(expected.*to include.*\")\n"]
    element_error_re = [".*(Execute - wait \w*::\w* to present).*", ".*(The element.*does not exist).*",
                        ".*(Execute - open .*::.*- failed).*", ".*(Execute - select .*::.*- failed).*",
                        ".*(waiting for .*to be located).*", ".*(waiting for .*to be present).*",
                        "seconds.* (.* not present) in.*seconds", ".*\n.*(unable to locate element.*\n).*\.+"]
    env_issue_re = [".*(Driver info):.*", ".*(no implicit conversion).*", ".*(Internal Server Error).*"]
    net_issue_re = [".*(Net::ReadTimeout).*", ".*(Request Timeout).*"]
    code_error_re = [".*(undefined method).*", ".*(undefined local variable).*", ".*(uninitialized constant).*", ".*(invalid argument).*"]

    @classmethod
    def prejudge_case(cls, case):
        if case.result == "failed":
            # prejudge_type = cls.prejudge_error_message(case.error_message)
            prejudge_type = cls.prejudge_error_message_v2(case)
        else:
            prejudge_type = case.result
        return prejudge_type

    @classmethod
    def prejudge_all(cls, cases, script_not_case_flag=False):
        script_result = {}
        if len(cases) > 1:
            for index in range(len(cases)):
                case = cases.iloc[index]
                script_result_id = str(case.automation_script_result_id)
                case_prejudge_result = cls.prejudge_case(case)
                keyword = cls.extract_error_keyword(case_prejudge_result, case.error_message) if case.result == "failed" else cls.extract_error_keyword(case_prejudge_result)
                if script_result_id not in script_result.keys():
                    script_result[script_result_id] = {"result": case_prejudge_result, "keyword": case_prejudge_result, "cases": {str(case.id): {"result": case_prejudge_result, "keyword": keyword}}}
                else:
                    script_result[script_result_id]["cases"][str(case.id)] = {"result": case_prejudge_result, "keyword": keyword}
                    if cls.error_priority[case_prejudge_result] < cls.error_priority[script_result[script_result_id]["result"]]:
                        script_result[script_result_id]["result"] = case_prejudge_result
                        script_result[script_result_id]["keyword"] = case_prejudge_result
                if script_result[script_result_id]["result"] == "element not found":
                    for case in script_result[script_result_id]["cases"].values():
                        if case["result"] == "element not found":
                            script_result[script_result_id]["keyword"] = case["keyword"]
                            break
        else:
            case = cases.iloc[0]
            script_result_id = str(case.automation_script_result_id)
            case_prejudge_result = cls.prejudge_case(case)
            keyword = cls.extract_error_keyword(case_prejudge_result, case.error_message) if case.result == "failed" else cls.extract_error_keyword(case_prejudge_result)
            if script_not_case_flag:
                script_result[script_result_id] = {"result": case_prejudge_result, "keyword": case_prejudge_result, "cases": {str(case.id): {"result": case_prejudge_result, "keyword": keyword}}}
                if script_result[script_result_id]["result"] == "element not found":
                    script_result[script_result_id]["keyword"] = keyword
            else:
                script_result[script_result_id] = {"result": None, "cases": {str(case.id): {"result": case_prejudge_result, "keyword": keyword}}}

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
    def summarize_script_by_prejudged_case(cls, case_results):
        script_result = {}
        for case in case_results.values():
            if case["script_result_id"] not in script_result.keys():
                script_result[case["script_result_id"]] = case["result"]
            else:
                if cls.error_priority[case["result"]] < cls.error_priority[script_result[case["script_result_id"]]]:
                    script_result[case["script_result_id"]] = case["result"]
        return script_result

    @classmethod
    def prejudge_script(cls, script):
        script_prejudge_type = ""
        script_prejudge_priority = 9
        for case in script:
            case_prejudge_type = cls.prejudge_case(case)
            if cls.error_priority[case_prejudge_type] < script_prejudge_priority:
                script_prejudge_type = case_prejudge_type
                script_prejudge_priority = cls.error_priority[case_prejudge_type]
        return script_prejudge_type

    @classmethod
    def prejudge_error_message(cls, error_message):
        if error_message and str(error_message) != "nan":
            if re.search("|".join(cls.log_error_re), error_message, re.IGNORECASE):
                if re.search("|".join(cls.assert_fail_re), error_message, re.IGNORECASE):
                    prejudge_type = "suspect bug"
                elif re.search("|".join(cls.element_error_re), error_message, re.IGNORECASE):
                    prejudge_type = "element not found"
                elif re.search("|".join(cls.env_issue_re), error_message, re.IGNORECASE):
                    prejudge_type = "execution environment issue"
                elif re.search("|".join(cls.net_issue_re), error_message, re.IGNORECASE):
                    prejudge_type = "network issue"
                else:
                    prejudge_type = "suspect bug"
            else:
                if re.search("|".join(cls.expectation_fail_re), error_message, re.IGNORECASE | re.DOTALL):
                    prejudge_type = "suspect bug"
                elif re.search("|".join(cls.element_error_re), error_message, re.IGNORECASE):
                    prejudge_type = "element not found"
                elif re.search("|".join(cls.env_issue_re), error_message, re.IGNORECASE):
                    prejudge_type = "execution environment issue"
                elif re.search("|".join(cls.net_issue_re), error_message, re.IGNORECASE):
                    prejudge_type = "network issue"
                elif re.search("|".join(cls.code_error_re), error_message, re.IGNORECASE):
                    prejudge_type = "code error"
                else:
                    prejudge_type = "other"
        else:
            prejudge_type = "other" if not error_message or len(error_message) == 0 else error_message
        return prejudge_type

    @classmethod
    def prejudge_error_message_v2(cls, data):
        prejudge_type = cls.prejudge_error_message(data.error_message)
        if prejudge_type in ["code error", "other"]:
            recent = cls.regression_db.get_all_results_from_database(
                "SELECT result FROM `automation_case_results` where automation_case_id=%s order by id desc limit 10 " % str(
                    data.automation_case_id))
            successive_pass = 0
            for seq in range(1, 10):
                if recent[seq]["result"] == "pass":
                    successive_pass += 1
                else:
                    break
            if successive_pass > 8:
                prejudge_type = "suspect bug"
        return prejudge_type

    @classmethod
    def extract_error_keyword(cls, error_type, error_message=None):
        error_re = {
            "element not found": cls.element_error_re,
            "execution environment issue": cls.env_issue_re,
            "code error": cls.code_error_re,
            "network issue": cls.net_issue_re
        }
        if error_type in error_re.keys():
            return ",".join([str(i) for i in re.search("|".join(error_re[error_type]), error_message, re.IGNORECASE).groups() if i])
        else:
            return error_type
