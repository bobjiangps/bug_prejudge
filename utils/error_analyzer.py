from collections import Counter
import re


class ErrorAnalyzer:

    @classmethod
    def check_network_issue_percentage(cls, errors):
        network_error_keyword = ["Net::ReadTimeout", "Request Timeout"]
        network_errors = errors[errors["error_message"].str.contains("|".join(network_error_keyword), flags=re.IGNORECASE, regex=True)]
        network_error_percentage = network_errors.id.count() / errors.id.count()
        print("network error percentage is:", "%.2f%%" % (network_error_percentage * 100))
        return network_error_percentage

    @classmethod
    def check_element_caused_most_failures(cls, errors):
        element_error_keyword = [".*Execute - wait (\w*::\w*) to present.*", ".*Execute - open .* (\w*::\w*) .*- failed.*",
                                 ".*Execute - select .* (\w*::\w*) .*- failed.*", ".*Execute - get .* (\w*::\w*) .*- failed.*"]
        element_errors_match = errors[errors["error_message"].str.match("|".join(element_error_keyword), flags=re.IGNORECASE)]
        element_errors_extract = element_errors_match.error_message.str.extract("|".join(element_error_keyword), flags=re.IGNORECASE, expand=False)
        element_errors_record = []
        for seq in element_errors_extract:
            for item in element_errors_extract[seq]:
                if str(item) != "nan":
                    element_errors_record.append(item)
        most_failure_element = Counter(element_errors_record).most_common(1)[0]
        print("The element '%s' has most failures: %d times" % (most_failure_element[0], most_failure_element[1]))
        return most_failure_element
