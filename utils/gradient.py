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
