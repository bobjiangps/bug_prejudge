import re


class SimplePrejudgeHelper:

    @classmethod
    def prejudge_case(cls, case):
        log_error_re = [".*in .?logger_error.*"]
        assert_fail_re = [".*Assert -.*- failed.*"]
        element_error_re = [".*Execute - wait \w*::\w* to present.*", ".*The element.*does not exist.*",
                            ".*Execute - open .*::.*- failed.*", ".*Execute - select .*::.*- failed.*"]
        env_issue_re = [".*Driver info:.*", ".*no implicit conversion.*", ".*Internal Server Error.*"]
        net_issue_re = [".*Net::ReadTimeout.*", ".*Request Timeout.*"]
        code_error_re = [".*undefined method.*", ".*undefined local variable.*", ".*uninitialized constant.*"]

        if case.result == "failed":
            if case.error_message:
                message = case.error_message
                if message.str.match("|".join(log_error_re), flags=re.IGNORECASE):
                    if message.str.match("|".join(assert_fail_re), flags=re.IGNORECASE):
                        prejudge_type = "suspect bug"
                    elif message.str.match("|".join(element_error_re), flags=re.IGNORECASE):
                        prejudge_type = "element not found"
                    elif message.str.match("|".join(env_issue_re), flags=re.IGNORECASE):
                        prejudge_type = "execution environment issue"
                    elif message.str.match("|".join(net_issue_re), flags=re.IGNORECASE):
                        prejudge_type = "network issue"
                    else:
                        prejudge_type = "suspect bug"
                elif message.str.match("|".join(net_issue_re), flags=re.IGNORECASE):
                    prejudge_type = "network issue"
                elif message.str.match("|".join(code_error_re), flags=re.IGNORECASE):
                    prejudge_type = "code error"
                else:
                    prejudge_type = "other"
            else:
                prejudge_type = case.eror_message
        else:
            prejudge_type = case.result
        return prejudge_type

    @classmethod
    def prejudge_script(cls, script):
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
        script_prejudge_type = ""
        script_prejudge_priority = 9
        for case in script:
            case_prejudge_type = cls.prejudge_case(case)
            if error_priority[case_prejudge_type] < script_prejudge_priority:
                script_prejudge_type = case_prejudge_type
                script_prejudge_priority = error_priority[case_prejudge_type]
        return script_prejudge_type
