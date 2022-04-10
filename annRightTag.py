import os
import statistics as stats
import torch
import random
import torch.optim as optim
from torch.autograd import Variable
import torch.nn.functional as F
import torch.nn as nn
import json


train_data_list = []
target_list = []
train_data = []
ann_dataset_file = open("annDatasetTrain.json", "r")
ann_dataset_dict = json.loads(ann_dataset_file.read())
ann_dataset_file.close()
for index in range(len(ann_dataset_dict)):
    key, value = random.choice(list(ann_dataset_dict.items()))
    del ann_dataset_dict[key]
    value_tensor = torch.Tensor(value)
    train_data_list.append(value_tensor)
    target = [1 if "r" in key else 0, 1 if "f" in key else 0]
    target_list.append(target)
    if len(train_data_list) >= 20:
        train_data.append((torch.stack(train_data_list), target_list))
        train_data_list = []
        target_list = []


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.linear1 = nn.Linear(51, 50)
        self.linear2 = nn.Linear(50, 48)
        self.linear3 = nn.Linear(48, 46)
        self.linear4 = nn.Linear(46, 44)
        self.linear5 = nn.Linear(44, 2)

    def forward(self, data):
        data = F.relu(self.linear1(data))
        data = F.relu(self.linear2(data))
        data = F.relu(self.linear3(data))
        data = F.relu(self.linear4(data))
        data = self.linear5(data)
        return torch.sigmoid(data)


model = Net()
#  model.cuda()


if os.path.isfile('savedNet.pt'):
    model = torch.load('savedNet.pt', map_location=torch.device('cpu'))  # , map_location=torch.device('cpu')

optimizer = optim.Adam(model.parameters(), lr=0.001)


def train(epoch):
    model.train()
    batch_id = 0
    for data, target in train_data:
        #  data = data.cuda()
        target = torch.Tensor(target)  # .cuda()
        data = Variable(data)
        target = Variable(target)
        optimizer.zero_grad()
        out = model(data)
        criterion = F.binary_cross_entropy
        loss = criterion(out, target)
        #   print(loss)
        loss.backward()
        optimizer.step()
        batch_id = batch_id + 1


def test():
    model.eval()
    correct = ([])
    ann_dataset_file = open("annDatasetTest.json", "r")
    ann_dataset_dict = json.loads(ann_dataset_file.read())
    ann_dataset_file.close()
    for index in range(len(ann_dataset_dict)):
        key, value = random.choice(list(ann_dataset_dict.items()))
        del ann_dataset_dict[key]
        eval_tensor = torch.Tensor(value)
        data = Variable(eval_tensor)  # value.cuda()
        out = model(data)
        result = 0
        print(key, " is ", "right" if out.data.max(0, keepdim=True)[1] == 0 else "false")
        if (((out.data.max(0, keepdim=True)[1]) == 0) and ('r' in key)) or (
                ((out.data.max(0, keepdim=True)[1]) == 1) and ('f' in key)):
            result = 1
        else:
            result = 0
        correct.append(result)
    hit_rate = stats.mean(correct)
    print("Trefferquote: ", (hit_rate * 100), "%")
    return hit_rate


test_best_result = 0
for epoch in range(0, 50):
    optimizer = optim.Adam(model.parameters(), lr=0.002)  # lr=0.01 - epoch * 0.0001
    train(epoch)
    print("Epoche ", epoch, "abgeschlossen!")
    test_result = test()
    if test_result > test_best_result:
        # torch.save(model, 'savedNet.pt')
        print("save..... \n")
        test_best_result = test_result

print("Bestes Gesamtergebnis: ", test_best_result * 100)
