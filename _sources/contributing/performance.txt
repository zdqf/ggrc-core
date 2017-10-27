Performance
===========

When reviewing a pull request we must always check for potential performance issues and bottlenecks. Note that we should try to stick to these guidelines also when writing the code.



Here are a few general things we should pay attention to:

- Avoid searching for multiple items in a list. This can always be avoided by using a js object, or a python set or a python dict.
- When working with multiple objects, preprocessing is a good way of simplifying and speeding up operations.

For the frontend part:

- Avoid fetching data that is not needed

  - Always first check the frontend cache if the data is available and only then fetch it from the backend. Note that in some cases the frontend cache should be avoided, such as, opening a modal window or opening an assessment info pane.
  - Check if the required data has already been sent with any of the other requests (assignees of an assessment are sent with the assessment and do not need to be fetched again.
  - When using the query API try to include all queries in a single request.

- Reduce the amount of data that is fetched. Some of these might need additional work on the backend, but mostly that will be less expensive than a full additional request. Examples would be:

  - Avoid fetching entire objects to read a single property (fetching an Audit to get the audit folder)
  - Fetching the original snapshot object just to check if it exists.


For the backend part:

- Aim to have only constant number of sql queries for every request.
- Check for proper use of eager query and index query.
