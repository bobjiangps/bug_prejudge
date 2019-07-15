class FileHelper:

    @classmethod
    def save_db_query_result_to_csv(cls, result, file_path):
        with open(file_path, "w") as f:
            f.write(",".join(result[0].keys()) + "\n")
            for row in result:
                new_row = [str(x).replace("\r", " ").replace("\n", " ").replace(",", " ") for x in row.values()]
                f.write(",".join(new_row) + "\n")
