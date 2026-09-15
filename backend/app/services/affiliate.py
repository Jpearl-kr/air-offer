"""Turns a raw provider deep-link into a trackable affiliate redirect URL.

`Provider.affiliate_base_url` is a template with `{deep_link}` and `{click_id}`
placeholders, e.g. "https://tp.media/click?...&sub_id={click_id}&url={deep_link}".
Until a provider's affiliate program is approved, affiliate_base_url stays NULL
and we fall back to tagging the original deep_link with a plain UTM + click_id
so click-through can still be measured.
"""

from urllib.parse import quote

from app.models import Provider


def build_redirect_url(provider: Provider, deep_link: str, click_id: int) -> str:
    if provider.affiliate_base_url:
        return provider.affiliate_base_url.format(deep_link=quote(deep_link, safe=""), click_id=click_id)

    separator = "&" if "?" in deep_link else "?"
    return f"{deep_link}{separator}utm_source=air-offer&click_id={click_id}"
