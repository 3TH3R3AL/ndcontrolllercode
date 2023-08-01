import datetime

def log(file,message):
    with open(file,'a') as f:
        print(datetime.datetime.now(),message,file=f)