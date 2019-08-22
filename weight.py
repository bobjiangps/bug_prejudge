from utils.gradient import *
from configuration.config import Config
import pandas as pd
import os


if __name__ == "__main__":
    specified_project = None
    projects = []
    if specified_project:
        projects.append(specified_project)
    else:
        triage_history_file = os.path.join(os.getcwd(), "data", "triage_history.csv")
        triage_history = pd.read_csv(triage_history_file)
        for p in triage_history["project"].unique():
            project_history = triage_history[triage_history["project"] == p]
            if len(project_history) >= Config.load_env("triage_trigger_ml"):
                projects.append(p)

    for project in projects:
        project_triage_history_file = os.path.join(os.getcwd(), "data", "triage_history_%s.csv" % project)
        project_triage_history = pd.read_csv(project_triage_history_file, index_col=0)
        project_triage_history["offset"] = 1
        project_triage_history["is_bug"] = project_triage_history["triage_type"].apply(lambda x: 1 if x.lower() == "product error" else 0)
        project_triage_history.drop(columns=["triage_type"], inplace=True)
        weight = asc_with_target(project_triage_history.iloc[:, :-1], project_triage_history["is_bug"], step_size=0.001, target=0.7, timeout=360)
        weight = weight.flatten().tolist()
        columns = list(project_triage_history.iloc[:, :-1].columns.values)
        project_parameter_file = os.path.join(os.getcwd(), "data", "parameter_%s.csv" % project)
        with open(project_parameter_file, "w") as f:
            f.write(",".join(columns))
            f.write("\n")
            f.write(str(weight)[1:-1])
