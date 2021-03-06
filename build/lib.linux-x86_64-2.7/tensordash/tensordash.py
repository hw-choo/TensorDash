import requests
import json
import keras
class FirebaseError(Exception):
    pass
class SendDataToFirebase(object):

    def __init__(self, key = None):
        response = None

    def sendMessage(self, key = None, params = None, ModelName = 'Sample Model'):
        epoch, loss, acc, val_loss, val_acc = params
        
        if(acc == None and val_loss == None):
            data = '{"Epoch":' +  str(epoch+1) + ', "Loss" :' + str(loss) + '}'
        elif(acc == None):
            data = '{"Epoch":' +  str(epoch+1) + ', "Loss" :' + str(loss) + ', "Validation Loss":' + str(val_loss) + '}'
        elif(val_loss == None):
            data = '{"Epoch":' +  str(epoch+1) + ', "Loss" :' + str(loss) + ', "Accuracy" :' + str(acc) + '}'
        else:
            data = '{"Epoch":' +  str(epoch+1) + ', "Loss" :' + str(loss) + ', "Accuracy" :' + str(acc) + ', "Validation Loss":' + str(val_loss) + ', "Validation Accuracy" :' + str(val_acc) + '}'

        response = requests.post('https://cofeeshop-tensorflow.firebaseio.com/{}/{}.json'.format(key, ModelName), data=data)

    def updateRunningStatus(self, key = None, ModelName = 'Sample Model'):
        data = '{"Status" : "RUNNING"}'
        response = requests.put('https://cofeeshop-tensorflow.firebaseio.com/{}/{}.json'.format(key, ModelName), data = data)

        notif_data = '{"Key":' + '"' + str(key) + '"' + ', "Status" : "Running"}'
        response = requests.post('https://cofeeshop-tensorflow.firebaseio.com/notification.json', data = notif_data)

    def updateCompletedStatus(self, key = None, ModelName = 'Sample Model'):
        data = '{"Status" : "COMPLETED"}'
        response = requests.patch('https://cofeeshop-tensorflow.firebaseio.com/{}/{}.json'.format(key, ModelName), data = data)


        notif_data = notif_data = '{"Key":' + '"' + str(key) + '"' + ', "Status" : "Completed"}'
        #notif_data = '{"Key" : "Sample Key", "Status" : "Running"}'
        response = requests.post('https://cofeeshop-tensorflow.firebaseio.com/notification.json', data = notif_data)

    def crashAnalytics(self, key = None, ModelName = 'Sample Model'):
        data = '{"Status" : "CRASHED"}'
        response = requests.patch('https://cofeeshop-tensorflow.firebaseio.com/{}/{}.json'.format(key, ModelName), data = data)


        notif_data = '{"Key":' + '"' + str(key) + '"' + ', "Status" : "Crashed"}'
        #notif_data = '{"Key" : "Sample Key", "Status" : "Running"}'
        response = requests.post('https://cofeeshop-tensorflow.firebaseio.com/notification.json', data = notif_data)

SendData = SendDataToFirebase()
class Tensordash(keras.callbacks.Callback):

    def __init__(self, email = 'None', password = 'None',  ModelName = 'Sample_model'):

        self.ModelName = ModelName
        self.email = email
        self.password = password

        headers = {'Content-Type': 'application/json',}
        params = (('key', 'AIzaSyDU4zqFpa92Jf64nYdgzT8u2oJfENn-2f8'),)
        val = {
            "email" : self.email,
            "password": self.password,
            "returnSecureToken": "false"
        }
        data = str(val)

        try:
            response = requests.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword', headers=headers, params=params, data=data)
            output = response.json()
            self.key = output['localId']

        except:
            raise FirebaseError("Authentication Failed. Kindly create an account on the companion app")
    
    def on_train_begin(self, logs = {}):
        self.losses = []
        self.accuracy = []
        self.val_losses = []
        self.val_accuracy = []
        self.num_epochs = []

        SendData.updateRunningStatus(key = self.key, ModelName = self.ModelName)
        SendData.sendMessage(key = self.key, params = (-1, 0, 0, 0, 0), ModelName = self.ModelName)

    def on_epoch_end(self, epoch, logs = {}):

        self.losses.append(logs.get('loss'))
        self.accuracy.append(logs.get('accuracy'))
        self.val_losses.append(logs.get('val_loss'))
        self.val_accuracy.append(logs.get('val_accuracy'))
        self.num_epochs.append(epoch)

        self.loss = float("{0:.6f}".format(self.losses[-1]))

        if self.accuracy[-1] == None:
            self.acc = None
        else:
            self.acc = float("{0:.6f}".format(self.accuracy[-1]))

        if self.val_losses[-1] == None:
            self.val_loss = None
        else:
            self.val_loss = float("{0:.6f}".format(self.val_losses[-1]))

        if self.val_accuracy[-1] == None:
            self.val_acc = None
        else:
            self.val_acc = float("{0:.6f}".format(self.val_accuracy[-1]))
    
        values = [epoch, self.loss, self.acc, self.val_loss, self.val_acc]
        SendData.sendMessage(key = self.key, params = values, ModelName = self.ModelName)

    def on_train_end(self, epoch, logs = {}):

        SendData.updateCompletedStatus(key = self.key, ModelName = self.ModelName)

    def sendCrash(self):
        SendData.crashAnalytics(key = self.key, ModelName = self.ModelName)