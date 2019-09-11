import numpy as np
import time


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def classify(x):
    if x > 0.5:
        return 1
    else:
        return 0


def asc(data_mat, label_mat, step_size=0.001, max_iter=500):
    data_mat_np = np.mat(data_mat)
    label_mat_np = np.mat(label_mat).transpose()
    m, n = np.shape(data_mat_np)
    weights = np.ones((n, 1))
    for _ in range(max_iter):
        h = sigmoid(data_mat_np * weights)
        error = label_mat_np - h
        weights = weights + step_size * data_mat_np.transpose() * error
    return weights.getA()


def asc_with_target(data_mat, label_mat, step_size=0.001, target=0.5, timeout=3600, lean_to_bug=False):
    data_mat_np = np.mat(data_mat)
    label_mat_np = np.mat(label_mat).transpose()
    m, n = np.shape(data_mat_np)
    weights = np.ones((n, 1))
    loop_count = 0
    total = len(data_mat)
    record_match_rate = 0
    record_weights = np.ones((n, 1))
    interval = 0
    start = time.time()
    while True:
        loop_count += 1
        interval += 1
        h = sigmoid(data_mat_np * weights)
        error = label_mat_np - h
        trained_result = []
        for i in h:
            trained_result.append(classify(i[0][0]))
        compare_result = np.unique(np.array(trained_result) - np.array(label_mat), return_counts=True)
        matched_index = compare_result[0].tolist().index(0)
        matched_count = compare_result[1].tolist()[matched_index]
        print("--------------------")
        print("record matched rate is:", record_match_rate)
        if lean_to_bug:
            target *= 2
            bug_compare_result = np.unique(np.array(label_mat) - (np.array(trained_result) - np.array(label_mat)), return_counts=True)
            try:
                bug_matched_index = bug_compare_result[0].tolist().index(1)
                bug_matched_count = bug_compare_result[1].tolist()[bug_matched_index]
            except ValueError:
                bug_matched_count = 0
            bug_total = label_mat.value_counts()[1]
            current_match_rate = (matched_count / total) + (bug_matched_count / bug_total)
            print("current matched rate is:", current_match_rate, matched_count / total, bug_matched_count / bug_total)
        else:
            current_match_rate = matched_count / total
            print("current matched rate is:", current_match_rate)
        print("weight is：", weights.flatten().tolist())
        if record_match_rate > target:
            if record_match_rate > current_match_rate:
                print("loop count: ", loop_count)
                print("duration: ", time.time() - start)
                break
        if interval >= timeout:
            interval = 0
            end = time.time()
            if end - start >= timeout:
                print("loop count: ", loop_count)
                print("duration: ", end - start)
                break
        if record_match_rate < current_match_rate and loop_count > 1:
            record_match_rate = current_match_rate
            record_weights = weights
        weights = weights + step_size * data_mat_np.transpose() * error
    print("======================")
    print("final record matched rate is:", record_match_rate)
    print("final weight is：", record_weights.flatten().tolist())
    return record_weights.getA()
