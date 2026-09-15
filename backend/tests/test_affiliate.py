from app.models import Provider
from app.services.affiliate import build_redirect_url


def test_falls_back_to_utm_tag_when_no_affiliate_program():
    provider = Provider(id=1, name="ke_official", provider_type="airline_official", affiliate_base_url=None)
    url = build_redirect_url(provider, "https://www.koreanair.com/booking", click_id=42)
    assert url == "https://www.koreanair.com/booking?utm_source=air-offer&click_id=42"


def test_appends_utm_tag_when_deep_link_already_has_query_params():
    provider = Provider(id=1, name="skyscanner", provider_type="meta_search", affiliate_base_url=None)
    url = build_redirect_url(provider, "https://example.com/flights?x=1", click_id=7)
    assert url == "https://example.com/flights?x=1&utm_source=air-offer&click_id=7"


def test_uses_affiliate_template_when_configured():
    provider = Provider(
        id=2,
        name="tripcom",
        provider_type="ota",
        affiliate_base_url="https://tp.media/click?sub_id={click_id}&url={deep_link}",
    )
    url = build_redirect_url(provider, "https://trip.com/flight?a=b", click_id=99)
    assert url == "https://tp.media/click?sub_id=99&url=https%3A%2F%2Ftrip.com%2Fflight%3Fa%3Db"
