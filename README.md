## Scheduled API

Scheduled API

## Feature List

1. **Asynchronous task execution**: The module utilizes Frappe's background job system to enqueue and execute tasks asynchronously.
2. **Schedule Request processing**: The module processes "Schedule Request" documents and determines whether to create a new document or call a specified method based on the request.
3. **Error handling and retries**: The module gracefully handles exceptions during request execution, updates the status accordingly, and retries failed requests.
4. **Schedule Response creation**: The module creates "Schedule Response" documents based on the outcome of the request execution, including success, errors, and traceback information.
5. **Callback URL support**: The module supports sending responses to specified callback URLs, with configurable headers and automatic retries upon failure.
6. **Pending and Failed request processing**: The module provides a function to process all pending and failed "Schedule Request" documents, allowing for easier recovery and rescheduling.
7. **Modular design**: The module is organized into separate functions for enqueueing, executing, and sending responses, which promotes readability and maintainability.

These features collectively enable the module to handle scheduled API requests effectively, manage their execution and responses, and provide a robust mechanism for communication with external systems.

#### License

MIT
