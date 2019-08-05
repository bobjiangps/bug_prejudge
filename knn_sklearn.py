from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import os
import datetime


start_time = datetime.datetime.now()
triage_history = pd.read_csv(os.path.join(os.getcwd(), "data", "temp_new_triage_Endurance.csv"))
round_error = pd.read_csv(os.path.join(os.getcwd(), "data", "temp_new_round_error_Endurance.csv"))
features = ["duration", "env_LV-PERF", "env_LV-QA", "env_LV-REG", "browser_chrome",	"browser_ie", "error_type_code error", "error_type_element not found", "error_type_execution environment issue", "error_type_network issue", "error_type_other", "error_type_suspect bug"]
triage = triage_history[features]
labels = triage_history["triage_type"]
knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(triage, labels)
label_values = knn.classes_
print(label_values)
predict = knn.predict([[0.121712295350082,0,0,1,1,0,0,0,1,0,0,0]])
predict_possibility = knn.predict_proba([[0.121712295350082,0,0,1,1,0,0,0,1,0,0,0]])
# predict = knn.predict([round_error.loc[0]])
print(predict)
print(predict_possibility)
# print(round_error.iloc[[0]])
# print(round_error.iloc[0,[0,1,2,3,4,5,6,7,8,9,10,11]])
# print(knn.predict([round_error.iloc[0,[0:11]]]))
for seq in range(len(round_error)):
    print(seq)
    # print(round_error.iloc[seq, [1,2,3,4,5,6,7,8,9,10,11.12]])
    print(knn.predict([round_error.iloc[seq, [1,2,3,4,5,6,7,8,9,10,11,12]]]))
    print(knn.predict_proba([round_error.iloc[seq, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,12]]]))

# for seq in range(len(triage_history)):
#     print(seq)
#     print(triage_history.iloc[[seq]])
#     print(knn.predict([triage_history.iloc[seq, [2,3,4,5,6,7,8,9,10,11,12,13]]]))
#     print(knn.predict_proba([triage_history.iloc[seq, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11,12,13]]]))

end_time = datetime.datetime.now()
print("duration: ", end_time - start_time)
