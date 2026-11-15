from celery import shared_task


@shared_task(name="core.ping")
def ping() -> str:
    """Trivial task used to verify the Celery worker/broker wiring."""
    return "pong"
