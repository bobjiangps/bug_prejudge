import re


class SimplePrejudgeHelper:

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

    log_error_re = [".*in .?logger_error.*"]
    assert_fail_re = [".*Assert -.*- failed.*"]
    element_error_re = [".*Execute - wait \w*::\w* to present.*", ".*The element.*does not exist.*",
                        ".*Execute - open .*::.*- failed.*", ".*Execute - select .*::.*- failed.*"]
    env_issue_re = [".*Driver info:.*", ".*no implicit conversion.*", ".*Internal Server Error.*"]
    net_issue_re = [".*Net::ReadTimeout.*", ".*Request Timeout.*"]
    code_error_re = [".*undefined method.*", ".*undefined local variable.*", ".*uninitialized constant.*"]

    @classmethod
    def prejudge_case(cls, case):
        index = case.index.values[0]
        if case.result[index] == "failed":
            if case.error_message[index]:
                message = case.error_message
                if message.str.match("|".join(cls.log_error_re), flags=re.IGNORECASE)[index]:
                    if message.str.match("|".join(cls.assert_fail_re), flags=re.IGNORECASE)[index]:
                        prejudge_type = "suspect bug"
                    elif message.str.match("|".join(cls.element_error_re), flags=re.IGNORECASE)[index]:
                        prejudge_type = "element not found"
                    elif message.str.match("|".join(cls.env_issue_re), flags=re.IGNORECASE)[index]:
                        prejudge_type = "execution environment issue"
                    elif message.str.match("|".join(cls.net_issue_re), flags=re.IGNORECASE)[index]:
                        prejudge_type = "network issue"
                    else:
                        prejudge_type = "suspect bug"
                elif message.str.match("|".join(cls.net_issue_re), flags=re.IGNORECASE)[index]:
                    prejudge_type = "network issue"
                elif message.str.match("|".join(cls.code_error_re), flags=re.IGNORECASE)[index]:
                    prejudge_type = "code error"
                else:
                    prejudge_type = "other"
            else:
                prejudge_type = case.error_message[index]
        else:
            prejudge_type = case.result[index]
        return prejudge_type

    @classmethod
    def prejudge_all(cls, cases):
        script_result = {}
        if len(cases) > 1:
            for index in range(len(cases)):
                case = cases.iloc[[index]]
                script_result_id = str(case.automation_script_result_id[index])
                case_prejudge_result = cls.prejudge_case(case)
                if script_result_id not in script_result.keys():
                    script_result[script_result_id] = {"result": case_prejudge_result, "cases": {str(case.id[index]): case_prejudge_result}}
                else:
                    script_result[script_result_id]["cases"][str(case.id[index])] = case_prejudge_result
                    if cls.error_priority[case_prejudge_result] < cls.error_priority[script_result[script_result_id]["result"]]:
                        script_result[script_result_id]["result"] = case_prejudge_result
        else:
            case = cases.iloc[[0]]
            script_result_id = str(case.automation_script_result_id[0])
            case_prejudge_result = cls.prejudge_case(case)
            script_result[script_result_id] = {"result": None, "cases": {str(case.id[0]): case_prejudge_result}}
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
            elif re.search("|".join(cls.net_issue_re), error_message, re.IGNORECASE):
                prejudge_type = "network issue"
            elif re.search("|".join(cls.code_error_re), error_message, re.IGNORECASE):
                prejudge_type = "code error"
            else:
                prejudge_type = "other"
        else:
            prejudge_type = error_message
        return prejudge_type
