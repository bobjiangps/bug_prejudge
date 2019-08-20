import numpy as np
import matplotlib.pyplot as plt
import random


def loadData(): #打开读入数据
    dataMat = [] #样本数据列表
    labelMat = [] #标签列表
    fr = open('debug/logistic_regression/data-logistic.txt') #打开文件
    for line in fr.readlines(): #逐行读取
        lineArr = line.strip().split(",") #去掉回车（换行）
        dataMat.append([1.0,float(lineArr[0]),float(lineArr[1])]) #添加
        labelMat.append(int(lineArr[2]))
    fr.close() #关闭文件
    return dataMat,labelMat

# def loadData(): #打开读入数据
#     dataMat = [] #样本数据列表
#     labelMat = [] #标签列表
#     for i in range(500):
#         dataMat.append([1.0, random.uniform(-10, 10), random.uniform(-10, 10)]) #添加
#         labelMat.append(random.randint(0, 1))
#     return dataMat,labelMat


def sigmoid(a):                              #sigmoid函数
    return 1.0 / (1 + np.exp(-a))


# def gradRise(dataMat1,labelMat1): #梯度上升函数
#     dataMat_np = np.mat(dataMat1) #转换为np矩阵
#     labelMat_np = np.mat(labelMat1).transpose() #同上
#     m,n = np.shape(dataMat_np) #返回行数列数
#     alpha = 0.001 #学习步长
#     Maxiteration = 10 #最大迭代次数
#     w = np.ones((n,1)) #系数（及权重）
#     #print(labelMat_np.shape)
#     temp_error = None
#     loop_count = 0
#     while True:
#         loop_count += 1
#     # for k in range(Maxiteration): #梯度上升函数矢量化
#         h = sigmoid(dataMat_np * w)
#         error = labelMat_np - h #误差
#         print("--=-=-error-=-=-=")
#         print(np.sum(error))
#         w = w + alpha * dataMat_np.transpose() * error
#         if not temp_error:
#             temp_error = np.sum(error)
#         print("-----")
#         print(temp_error)
#         print(np.sum(error))
#         if abs(temp_error) < abs(np.sum(error)):
#             break
#         else:
#             temp_error = np.sum(error)
#     print("-=-final-==-=")
#     print(error)
#     print(np.sum(temp_error))
#     print(loop_count)
#     return w.getA(), error #矩阵转数组


def gradRise(dataMat1,labelMat1): #梯度上升函数
    dataMat_np = np.mat(dataMat1) #转换为np矩阵
    labelMat_np = np.mat(labelMat1).transpose() #同上
    m,n = np.shape(dataMat_np) #返回行数列数
    alpha = 0.001 #学习步长
    Maxiteration = 500 #最大迭代次数
    w = np.ones((n,1)) #系数（及权重）
    #print(labelMat_np.shape)
    for k in range(Maxiteration): #梯度上升函数矢量化
        h = sigmoid(dataMat_np * w)
        error = labelMat_np - h #误差
        w = w + alpha * dataMat_np.transpose() * error
    return w.getA(), error #矩阵转数组


def show(w): #绘图
    dataMat,labelMat = loadData()
    dataArr = np.array(dataMat)
    n = np.shape(dataMat)[0]
    x_positive = [] #正样本
    y_positive = []
    x_negative = [] #负样本
    y_negative = []
    for i in range(n): #分类
        if int(labelMat[i]) == 1:
            x_positive.append(dataArr[i,1])
            y_positive.append(dataArr[i,2])
        else:
            x_negative.append(dataArr[i,1])
            y_negative.append(dataArr[i,2])
    fig = plt.figure() #创建空白画布
    ax = fig.add_subplot(111) #创建并选中子图
    ax.scatter(x_positive,y_positive,s = 20,c = 'red',marker = 's',alpha = 0.5) #散点图
    ax.scatter(x_negative,y_negative,s = 20,c = 'black',alpha = 0.5)
    x = np.arange(-3.0,3.0,0.1)
    #print(w.shape)
    #print(x.shape)
    y = (-w[0] - w[1]*x) / w[2] #决策边界由0 = w0x0 + w1x1 + w2x2 推导出
    ax.plot(x,y)
    plt.title("Best")
    plt.xlabel('X1')
    plt.ylabel('X2')
    plt.show()


if __name__ == "__main__":
    dataMat,labelMat = loadData()
    w,e = gradRise(dataMat,labelMat)
    print(w)
    print(e)
    show(w)