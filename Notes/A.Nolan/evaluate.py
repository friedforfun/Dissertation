from openvino.inference_engine import IENetwork, IEPlugin
import cv2
import os
import time
import numpy as np
from numpy import genfromtxt
from sklearn.metrics import accuracy_score
# import matplotlib.pyplot as plt
import time
import torch
import torchvision
import torchvision.transforms as transforms
import csv


tp_arr = []
lat_arr =[]


model_dir = os.environ['HOME'] + "/Documents/NCS2_C100/IR/"
model_xml = model_dir + "model.xml"
model_bin = model_dir + "model.bin"





# Loading Data
transform = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Normalize((0.5071, 0.4867, 0.4408), (0.2675, 0.2565, 0.2761))])

trainset = torchvision.datasets.CIFAR100(root='/home/andy/Documents/MSc_Project/data/', train=True,
                                        download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=4,
                                          shuffle=True, num_workers=1)

testset = torchvision.datasets.CIFAR100(root='/home/andy/Documents/MSc_Project/data/', train=False,
                                       download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=4,
                                         shuffle=False, num_workers=1)



def sync():

    pred = []
    y_test = []

    plugin = IEPlugin(device="MYRIAD")
    net = IENetwork(model=model_xml, weights=model_bin)
    input_blob = next(iter(net.inputs))
    out_blob = next(iter(net.outputs))
    n, c, h, w = net.inputs[input_blob].shape
    exec_net = plugin.load(network=net, num_requests=1)
    time_arr =[]
    image_number = 10000
    
    image_array=[]
    for i in range(image_number):
        
        image = testset[i][0]
        image = image.reshape((n, c, h, w))
        image_array.append(image)
        y_test.append(testset[i][1])
        
    
    for j in range(image_number):
        start_time = time.time()
        
        # TODO: Try / Catch
        res = exec_net.infer(inputs={input_blob: image_array[j]})
        value = list(res)[0]
        res = res.get(value)
        duration = time.time() - start_time
        time_arr.append(duration)
        pred.append(np.argmax(res))
    
    tp_arr.append(image_number/sum(time_arr))
    lat_arr.append(np.mean(time_arr))

    # Top 1 accuracy 
    pred = np.array(pred)
    a = accuracy_score(y_test, pred)*100

    t = round(np.mean(tp_arr),1)
    l = round(np.mean(lat_arr)*1000,1)

    print("Throughput:" + str(t))
    print("Latancy:" + str(l))
    print("Accuracy:" + str(a))
  

    del exec_net
    del net
    del plugin


    with open('CSV/metrics.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([a, l])

    return (l, a)
    
# Run Sync
sync()
