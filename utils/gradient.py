import numpy as np


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


def asc_with_target(data_mat, label_mat, step_size=0.1, target=0.7891):
    data_mat_np = np.mat(data_mat)
    label_mat_np = np.mat(label_mat).transpose()
    m, n = np.shape(data_mat_np)
    weights = np.ones((n, 1))
    record_weights = np.ones((n, 1))
    loop_count = 0
    total = len(data_mat)
    temp_match_rate = 0
    while True:
        loop_count += 1
        h = sigmoid(data_mat_np * weights)
        error = label_mat_np - h
        trained_result = []
        for i in h:
            trained_result.append(classify(i[0][0]))
        compare_result = np.unique(np.array(trained_result) - np.array(label_mat), return_counts=True)
        matched_index = compare_result[0].tolist().index(0)
        matched_count = compare_result[1].tolist()[matched_index]
        current_match_rate = matched_count / total
        if current_match_rate > target:
            if temp_match_rate > current_match_rate:
                print("loop count: ", loop_count)
                break
        record_weights = weights
        temp_match_rate = current_match_rate
        weights = weights + step_size * data_mat_np.transpose() * error
    return record_weights.getA()
