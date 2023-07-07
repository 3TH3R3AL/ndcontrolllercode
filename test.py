from collections import deque

# Create an empty queue
queue = deque()

# Enqueue elements
queue.append(1)
queue.append(2)
queue.append(3)
print(len(queue))
# Dequeue elements
item = queue.popleft()
print(item)  # Output: 1
print(len(queue))

item = queue.popleft()
print(item)  # Output: 2

# Check if the queue is empty
if not queue:
    print("Queue is empty")