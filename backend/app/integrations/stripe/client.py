"""Stripe client for CUSTOMER-facing invoice payments.

This is distinct from platform B2B billing (subscriptions) which lives in
``app/api/v1/billing`` and uses its own Stripe handling. This module creates
one-time payment checkout sessions for customer invoices and renders QR codes
of the payment URL.

We use a Stripe **Checkout Session** in ``mode="payment"`` rather than a
Payment Link because a one-time invoice payment maps directly to a checkout
session: the session accepts inline ``line_items`` with ``price_data`` (no
separate Product/Price object needed) and, on completion, fires the canonical
``checkout.session.completed`` event — the natural webhook signal that an
invoice was paid.
"""

import io

import stripe

from app.core.config import settings


class IntegrationNotConnectedError(Exception):
    """Raised when no Stripe secret key is configured."""


class IntegrationAuthError(Exception):
    """Raised when Stripe rejects the API request or authentication."""


def _api_key() -> str:
    key = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not key:
        raise IntegrationNotConnectedError(
            "Stripe isn't configured — set STRIPE_SECRET_KEY in Settings first."
        )
    return key


def _configure() -> None:
    stripe.api_key = _api_key()


def create_payment_link(
    amount_cents: int,
    currency: str,
    description: str,
    metadata: dict,
    success_url: str,
    cancel_url: str,
) -> dict:
    """Create a hosted Stripe Checkout Session for a one-time payment.

    Returns ``{"url": str, "id": str}``. Raises ``IntegrationNotConnectedError``
    when Stripe isn't configured and ``IntegrationAuthError`` when Stripe
    rejects the call — the caller converts these into a structured tool error.
    """
    _configure()

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": currency,
                        "unit_amount": int(amount_cents),
                        "product_data": {"name": description or "Invoice payment"},
                    },
                }
            ],
            metadata=metadata,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except stripe.error.StripeError as exc:
        raise IntegrationAuthError(
            f"Stripe request failed: {exc.__class__.__name__}: {exc}"
        )
    return {"url": session.url, "id": session.id}


def generate_qr_code_png(url: str) -> bytes:
    """Render a QR code (PNG bytes) encoding ``url`` via the ``qrcode`` library."""
    import qrcode
    from qrcode.image.pil import PilImage

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url or "")
    qr.make(fit=True)
    img = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()