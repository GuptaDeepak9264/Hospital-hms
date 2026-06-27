"""
Custom DRF exception handler.
Ensures all errors are returned as consistent JSON envelopes:
  { "success": false, "message": "...", "errors": { ... } }
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Override DRF's default exception handler to produce a uniform error
    envelope across the entire API surface.
    """
    # Let DRF do its default handling first
    response = exception_handler(exc, context)

    if response is not None:
        # Reshape the DRF-generated response
        error_detail = response.data

        # Extract a human-readable top-level message
        if isinstance(error_detail, dict):
            # e.g. {"detail": "Authentication credentials were not provided."}
            message = error_detail.get("detail", "An error occurred.")
            errors = {k: v for k, v in error_detail.items() if k != "detail"}
        elif isinstance(error_detail, list):
            message = " ".join(str(e) for e in error_detail)
            errors = {}
        else:
            message = str(error_detail)
            errors = {}

        response.data = {
            "success": False,
            "message": str(message),
            "errors": errors,
        }
    else:
        # Unhandled server errors — log and return 500
        logger.exception("Unhandled exception: %s", exc)
        response = Response(
            {
                "success": False,
                "message": "An internal server error occurred.",
                "errors": {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
