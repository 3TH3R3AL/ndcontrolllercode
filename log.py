import datetime
import time
import random
config = {
    'controllers.log': 'temp',
    'main.log': 'temp',
    'perm.log': 'temp'
}

def getTimestamp():
     return datetime.datetime.now().strftime('%m/%d/%y %I:%M %p')
def getFileName():
     return datetime.datetime.now().strftime('%m-%d-%y_%I-%M_%p')+"_"+str(random.randint(0,1000))+".log"

for file,value in config.items():
    if(value == 'temp'):
        with open(file,'w') as f:
                print(file,file=f)
                print('One Session Logging',file=f)
    elif(value == 'perm'):
        with open(file,'a') as f:
                print(f'\n\n-----------------------\nNew Session, started {getTimestamp()}\n',file=f)


def log(file,message):
    with open(file,'a') as f:
        print(getTimestamp(),message,file=f)

def startLogging(devices):
    while(True):
        time.sleep(20)
        message = '\n'
        for name, device in devices.items():
            if(device != {}):
                message += f'\n{name} - Voltages: {device.voltages}, Currents: {device.currents} ' 
        message = '\n\n'
        log('perm.log',message)
                
               
def savePermLog():
     
    with open('perm.log','r') as f:
        logContents = f.read()
    with open('logs/'+getFileName(),'w') as f:
         f.write(logContents)