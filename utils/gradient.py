import numpy as np


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


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


def asc_with_target(data_mat, label_mat, step_size=0.01, target=0.2):
    data_mat_np = np.mat(data_mat)
    label_mat_np = np.mat(label_mat).transpose()
    m, n = np.shape(data_mat_np)
    weights = np.ones((n, 1))
    temp_offset = None
    loop_count = 0
    while True:
        loop_count += 1
        h = sigmoid(data_mat_np * weights)
        error = label_mat_np - h
        offset = np.sum(np.abs(error))
        if not temp_offset:
            temp_offset = offset
        if offset < target:
            if temp_offset < offset:
                print("loop count: ", loop_count)
                break
            else:
                temp_offset = offset
        else:
            temp_offset = offset
        weights = weights + step_size * data_mat_np.transpose() * error
    return weights.getA()
