import datetime
import time
config = {
    'controllers.log': 'temp',
    'main.log': 'temp',
    'perm.log': 'perm'
}

def getTimestamp():
     return datetime.datetime.now().strftime('%m/%d/%y %I:%M %p')

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
        message = ''
        for name, device in devices.items():
            if(device != {}):
                message += f'| {name} - Voltages: {device.voltages}, Currents: {device.currents} ' 
        log('perm.log',message)
                
               