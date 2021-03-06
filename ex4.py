import torch
from torch.utils.data import Dataset, DataLoader
from torch.utils.data.sampler import SubsetRandomSampler
from torchvision import datasets, transforms
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D

# Hyper-parameters
BATCH_SIZE = 50
IMAGESIZE = 28 * 28
LEARN_RATE = 0.01
EPOCHS = 10
FIRST_HIDDEN_LAYER_SIZE = 100
SECOND_HIDDEN_LAYER_SIZE = 50
NUMBER_OF_CLASSES = 10

class FashionMnistModelTrainer(object):

    def __init__(self, train_loader, validation_loader, test_loader, model, optimizer):
        self.train_loader = train_loader
        self.validation_loader = validation_loader
        self.test_loader = test_loader
        self.model = model
        self.optimizer = optimizer

    def run(self):
        avg_train_loss_per_epoch_dict = {}
        avg_validation_loss_per_epoch_dict = {}
        for epoch in range(1, EPOCHS + 1):
            self.train(epoch, avg_train_loss_per_epoch_dict)
            self.validation(epoch, avg_validation_loss_per_epoch_dict)
            plotTrainAndValidationGraphs(avg_train_loss_per_epoch_dict, avg_validation_loss_per_epoch_dict)


        self.test()

    def train(self, epoch, avg_train_loss_per_epoch_dict):
        self.model.train()
        train_loss = 0
        correct = 0

        for batch_idx, (data, labels) in enumerate(self.train_loader):
            self.optimizer.zero_grad()
            output = self.model(data)
            pred = output.data.max(1, keepdim=True)[1]
            correct += pred.eq(labels.data.view_as(pred)).cpu().sum().item()
            # negative log likelihood loss
            loss = F.nll_loss(output, labels)
            train_loss += loss
            # calculate gradients
            loss.backward()
            # update parameters
            self.optimizer.step()

        train_loss /= (len(self.train_loader))
        avg_train_loss_per_epoch_dict[epoch] = train_loss
        print("Epoch: {} Train set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)".format(epoch, train_loss, correct, len(self.train_loader) * BATCH_SIZE,
                                                                                            100. * correct / (len(self.train_loader) * BATCH_SIZE)))

    def validation(self, epoch_num, avg_validation_loss_per_epoch_dict):
        self.model.eval()
        validation_loss = 0
        correct = 0

        for data, target in self.validation_loader:
            output = self.model(data)
            validation_loss += F.nll_loss(output, target, size_average=False).item()
            pred = output.data.max(1, keepdim=True)[1]
            correct += pred.eq(target.data.view_as(pred)).cpu().sum().item()

        validation_loss /= len(self.validation_loader)
        avg_validation_loss_per_epoch_dict[epoch_num] = validation_loss
        print('\n Epoch:{} Validation set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
            epoch_num, validation_loss, correct, len(self.validation_loader),
            100. * correct / len(self.validation_loader)))

    def test(self):
        self.model.eval()
        test_loss = 0
        correct = 0
        pred_string_list = []
        for data, target in self.test_loader:
            output = self.model(data)
            test_loss += F.nll_loss(output, target, size_average=False).item()
            pred = output.data.max(1, keepdim=True)[1]
            pred_string_list.append(str(pred.item()))
            correct += pred.eq(target.data.view_as(pred)).cpu().sum().item()

        test_loss /= len(self.test_loader.dataset)
        print('\n Test set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
            test_loss, correct, len(self.test_loader),
            100. * correct / len(self.test_loader)))

        with open("test.pred", 'w') as test_pred_file:
            test_pred_file.write('\n'.join(pred_string_list))
        pass


class FirstNet(nn.Module):
    def __init__(self, image_size):
        super(FirstNet, self).__init__()
        self.image_size = image_size
        self.fc0 = nn.Linear(image_size, FIRST_HIDDEN_LAYER_SIZE)
        self.fc1 = nn.Linear(FIRST_HIDDEN_LAYER_SIZE, SECOND_HIDDEN_LAYER_SIZE)
        self.fc2 = nn.Linear(SECOND_HIDDEN_LAYER_SIZE, NUMBER_OF_CLASSES)

    def forward(self, x):
        x = x.view(-1, self.image_size)
        x = F.relu(self.fc0(x))
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


class SecondNet(nn.Module):
    def __init__(self, image_size):
        super(SecondNet, self).__init__()
        self.image_size = image_size
        self.fc0 = nn.Linear(image_size, FIRST_HIDDEN_LAYER_SIZE)
        self.fc1 = nn.Linear(FIRST_HIDDEN_LAYER_SIZE, SECOND_HIDDEN_LAYER_SIZE)
        self.fc2 = nn.Linear(SECOND_HIDDEN_LAYER_SIZE, NUMBER_OF_CLASSES)

    def forward(self, x):
        x = x.view(-1, self.image_size)
        x = F.relu(self.fc0(x))
        x = F.dropout(x, training=self.training)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


class ThirdNet(nn.Module):
    def __init__(self, image_size):
        super(ThirdNet, self).__init__()
        self.image_size = image_size
        self.fc0 = nn.Linear(image_size, FIRST_HIDDEN_LAYER_SIZE)
        self.fc1 = nn.Linear(FIRST_HIDDEN_LAYER_SIZE, SECOND_HIDDEN_LAYER_SIZE)
        self.fc2 = nn.Linear(SECOND_HIDDEN_LAYER_SIZE, NUMBER_OF_CLASSES)
        self.bn1 = nn.BatchNorm1d(FIRST_HIDDEN_LAYER_SIZE)
        self.bn2 = nn.BatchNorm1d(SECOND_HIDDEN_LAYER_SIZE)

    def forward(self, x):
        x = x.view(-1, self.image_size)
        x = self.bn1(F.relu(self.fc0(x)))
        x = self.bn2(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


def plotTrainAndValidationGraphs(avg_train_loss_per_epoch_dict, avg_validation_loss_per_epoch_dict):
    line1, = plt.plot(avg_train_loss_per_epoch_dict.keys(), avg_train_loss_per_epoch_dict.values(), "orange",
                      label='Train average loss')
    line2, = plt.plot(avg_validation_loss_per_epoch_dict.keys(), avg_validation_loss_per_epoch_dict.values(), "purple",
                      label='Validation average loss')
    # drawing name of the graphs
    plt.legend(handler_map={line1: HandlerLine2D(numpoints=4)})
    plt.show()


def main():
    ## Define our MNIST Datasets (Images and Labels) for training and testing
    train_dataset = datasets.FashionMNIST(root='./data',
                                          train=True,
                                          transform=transforms.ToTensor(),
                                          download=True)

    test_dataset = datasets.FashionMNIST(root='./data',
                                         train=False,
                                         transform=transforms.ToTensor())

    # spliting to training set and validation set

    ## We need to further split our training dataset into training and validation sets.

    # Define the indices
    indices = list(range(len(train_dataset)))  # start with all the indices in training set
    split = int(len(train_dataset) * 0.2)  # define the split size

    # Random, non-contiguous split
    validation_idx = np.random.choice(indices, size=split, replace=False)
    train_idx = list(set(indices) - set(validation_idx))

    # Contiguous split
    # train_idx, validation_idx = indices[split:], indices[:split]

    # define our samplers -- we use a SubsetRandomSampler because it will return
    # a random subset of the split defined by the given indices without replacement
    train_sampler = SubsetRandomSampler(train_idx)
    validation_sampler = SubsetRandomSampler(validation_idx)

    # Create the train_loader -- use your real batch_size which you
    # I hope have defined somewhere above
    train_loader = torch.utils.data.DataLoader(dataset=train_dataset,
                                                    batch_size=BATCH_SIZE, sampler = train_sampler)

    # You can use your above batch_size or just set it to 1 here.  Your validation
    # operations shouldn't be computationally intensive or require batching.
    validation_loader = torch.utils.data.DataLoader(dataset=train_dataset,
                                                         batch_size=1, sampler=validation_sampler)

    # You can use your above batch_size or just set it to 1 here.  Your test set
    # operations shouldn't be computationally intensive or require batching.  We
    # also turn off shuffling, although that shouldn't affect your test set operations
    # either
    test_loader = torch.utils.data.DataLoader(dataset=test_dataset,
                                                   batch_size=1,
                                                   shuffle=False)
    ## done splitting

    model = ThirdNet(image_size=IMAGESIZE)
    optimizer = optim.Adagrad(model.parameters(), lr=LEARN_RATE)

    trainer = FashionMnistModelTrainer(train_loader, validation_loader, test_loader, model, optimizer)
    trainer.run()

if __name__ == "__main__":
    main()
