from bot.payments import get_product, list_products_text, product_prices


def test_products_list_text_contains_ids() -> None:
    text = list_products_text()
    assert "hoodie" in text
    assert "event-ticket" in text


def test_product_price_payload() -> None:
    product = get_product("hoodie")
    assert product is not None
    prices = product_prices(product)
    assert len(prices) == 1
    assert prices[0].amount == product.amount
