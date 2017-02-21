"""
.. module:: ConvoTrain

ConvoTrain
*************

:Description: ConvoTrain

    

:Authors: bejar
    

:Version: 

:Created on: 20/12/2016 14:16 

"""

from keras import backend as K
from keras.optimizers import SGD, Adagrad, Adadelta, Adam
from keras.utils import np_utils
from DataGenerators import dayGenerator
from numpy.random import shuffle
import numpy as np

def transweights(weights):
    wtrans = {}
    for v in weights:
        wtrans[str(v)] = weights[v]
    return wtrans


def detransweights(weights):
    wtrans = {}
    for v in weights:
        wtrans[int(v)] = weights[v]
    return wtrans


def train_model_batch(model, config, test, test_labels, acctrain=False):
    """
    Trains the model using Keras batch method

    :param model:
    :param config:
    :param test:
    :param test_labels:
    :return:
    """

    if config['optimizer']['method'] == 'adagrad':
        optimizer = Adagrad()
    elif config['optimizer']['method'] == 'adadelta':
        optimizer = Adadelta()
    elif config['optimizer']['method'] == 'adam':
        optimizer = Adam()
    else:  # default SGD
        params = config['optimizer']['params']
        optimizer = SGD(lr=params['lrate'], momentum=params['momentum'], decay=params['lrate'] / params['momentum'],
                        nesterov=False)

    model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])

    classweight = detransweights(config['train']['classweight'])

    ldaysTr = config['traindata']
    reb = config['rebalanced']
    # Train Epochs
    logs = {'loss':0.0, 'acc':0.0, 'val_loss':0.0, 'val_acc':0.0}
    for epoch in range(config['train']['epochs']):
        shuffle(ldaysTr)
        tloss = []
        tacc = []

        # Train Batches
        for day in ldaysTr:
            x_train, y_train, perm = dayGenerator(config['datapath'], day, config['zfactor'], config['num_classes'], config['train']['batchsize'], reb=reb, imgord=config['imgord'])
            for p in perm:
                loss = model.train_on_batch(x_train[p], y_train[p], class_weight=classweight)
                tloss.append(loss[0])
                tacc.append(loss[1])

        # If acctrain is true then test all the train with the retrained model to obtain the real loss and acc after training
        # los and accuracy during the training is not accurate, but, in the end, the real measure of generalization
        #  is obtained with the independent test
        if acctrain:
            tloss = []
            tacc = []
            # Test Batches
            for day in ldaysTr:
                x_train, y_train, perm = dayGenerator(config['datapath'], day, config['zfactor'], config['num_classes'],
                                                      config['train']['batchsize'], reb=reb, imgord=config['imgord'])
                for p in perm:
                    loss = model.test_on_batch(x_train[p], y_train[p])
                    tloss.append(loss[0])
                    tacc.append(loss[1])

        logs['loss'] = float(np.mean(tloss))
        logs['acc'] = float(np.mean(tacc))

        scores = model.evaluate(test[0], test[1], verbose=0)
        logs['val_loss'] = scores[0]
        logs['val_acc'] = scores[1]
        print scores
        print '%d over' % epoch
    if config['savepath']:
        model.save(config['savepath'] + '/model' + '.h5')
    scores = model.evaluate(test[0], test[1], verbose=0)
    y_pred = model.predict_classes(test[0], verbose=0)
    print scores
    print y_pred


def load_dataset(config, only_test=False, imgord='tf'):
    """
    Loads the train and test dataset

    :return:
    """
    ldaysTr = config['traindata']
    ldaysTs = config['testdata']
    z_factor = config['zfactor']
    datapath = config['datapath']

    if not only_test:
        x_train, y_trainO = load_generated_dataset(datapath, ldaysTr, z_factor)
        # Data already generated in theano order
        # if imgord == 'th':
        #     x_train = x_train.transpose((0,3,1,2))
        y_train = np_utils.to_categorical(y_trainO, 5)
    else:
        x_train = None,
        y_train = None

    x_test, y_testO = load_generated_dataset(datapath, ldaysTs, z_factor)

    # Data already generated in theano order
    # if imgord == 'th':
    #     x_test = x_test.transpose((0,3,1,2))
    y_test = np_utils.to_categorical(y_testO, 5)
    num_classes = y_test.shape[1]
    return (x_train, y_train), (x_test, y_test), y_testO, num_classes


def load_generated_dataset(datapath, ldaysTr, z_factor):
    """
    Load the already generated datasets

    :param ldaysTr:
    :param z_factor:
    :return:
    """
    ldata = []
    y_train = []
    for day in ldaysTr:
        data = np.load(datapath + 'data-D%s-Z%0.2f.npy' % (day, z_factor))
        ldata.append(data)
        y_train.extend(np.load(datapath + 'labels-D%s-Z%0.2f.npy' % (day, z_factor)))
    x_train = np.concatenate(ldata)
    return x_train, y_train
