```python
import redis
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NexusWorker:
    def __init__(self, redis_host='localhost', redis_port=6379, queue_name='nexus_tasks'):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.queue_name = queue_name
        self.redis_client = redis.Redis(host=self.redis_host, port=self.redis_port)

    def process_task(self, task_data):
        try:
            task = json.loads(task_data)
            logging.info(f"Received task: {task}")
            # Simulate task processing - replace with actual logic
            result = f"Task {task['id']} processed by worker"
            logging.info(f"Task result: {result}")
            return result
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON received: {task_data}")
            return None
        except Exception as e:
            logging.exception(f"Error processing task: {e}")
            return None

    def consume_task(self):
        try:
            # Blocking pop from the queue
            task_data = self.redis_client.blpop(self.queue_name, timeout=1)
            if task_data:
                _, task = task_data
                task = task.decode('utf-8')
                result = self.process_task(task)
                if result:
                    self.redis_client.delete(task) # Clean up
                    return result
                else:
                    return None
            else:
                return None
        except Exception as e:
            logging.exception(f"Error consuming task: {e}")
            return None

if __name__ == '__main__':
    # Example Usage (for testing - remove in production)
    worker = NexusWorker()
    result = worker.consume_task()
    if result:
        print(f"Result: {result}")
```

