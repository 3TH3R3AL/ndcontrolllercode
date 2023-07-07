import threading
import time
test = ['test',"test2"]
# Define a function that will be executed in a separate thread
def thread_function():
    # Code to be executed in the thread
    time.sleep(2)
    print("This is running in a separate thread",test)
    
    test.pop()

# Create a thread object
thread = threading.Thread(target=thread_function)
# Start the thread
print('test')
thread.start()

# Code to be executed in the main thread
print("This is running in the main thread",test)

# Wait for the thread to finish
thread.join()

# Code after the thread has finished
print("Thread has finished",test)