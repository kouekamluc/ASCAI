"""
Utility functions for events app.
"""

import logging

logger = logging.getLogger(__name__)


def safe_task_execute(task_func, *args, **kwargs):
    """
    Safely execute a Celery task with fallback to synchronous execution.
    
    This function tries to execute the task asynchronously via Celery.
    If Celery/Redis is not available, it falls back to synchronous execution.
    
    Args:
        task_func: The Celery task function to execute
        *args: Positional arguments for the task
        **kwargs: Keyword arguments for the task
    
    Returns:
        The task result (AsyncResult if async, direct result if sync)
    """
    try:
        # Try to execute asynchronously via Celery
        result = task_func.delay(*args, **kwargs)
        logger.debug(f"Task {task_func.__name__} queued successfully via Celery")
        return result
    except Exception as e:
        # Check if it's a connection-related error
        error_str = str(e).lower()
        is_connection_error = (
            "operationalerror" in error_str or
            "connection" in error_str or
            "refused" in error_str or
            "no connection" in error_str or
            isinstance(e, (ConnectionError, OSError))
        )
        
        if is_connection_error:
            # Celery broker (Redis/RabbitMQ) is not available
            # Fall back to synchronous execution
            logger.warning(
                f"Celery broker unavailable. Executing {task_func.__name__} synchronously. "
                f"Error: {str(e)}"
            )
            try:
                # Execute the task function directly (synchronously)
                result = task_func(*args, **kwargs)
                logger.info(f"Task {task_func.__name__} executed successfully (synchronous)")
                return result
            except Exception as sync_error:
                # Log the error but don't fail the main request
                logger.error(
                    f"Error executing {task_func.__name__} synchronously: {str(sync_error)}",
                    exc_info=True
                )
                # Return None to indicate task failed but don't raise
                return None
        else:
            # Re-raise if it's not a connection error
            logger.error(
                f"Unexpected error executing {task_func.__name__}: {str(e)}",
                exc_info=True
            )
            raise

