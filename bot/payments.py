from dataclasses import dataclass

from aiogram.types import LabeledPrice


@dataclass(frozen=True)
class Product:
    product_id: str
    title: str
    description: str
    amount: int
    currency: str = "UAH"


PRODUCTS: dict[str, Product] = {
    "hoodie": Product(
        product_id="hoodie",
        title="SmartMenu Hoodie",
        description="Брендова худі SmartMenu",
        amount=180000,
    ),
    "event-ticket": Product(
        product_id="event-ticket",
        title="Event Ticket",
        description="Квиток на дегустаційний івент",
        amount=120000,
    ),
}


def list_products_text() -> str:
    lines = ["Доступні товари для оплати:"]
    for product in PRODUCTS.values():
        lines.append(
            f"- {product.product_id}: {product.title} "
            f"({product.amount / 100:.2f} {product.currency})"
        )
    return "\n".join(lines)


def get_product(product_id: str) -> Product | None:
    return PRODUCTS.get(product_id)


def product_prices(product: Product) -> list[LabeledPrice]:
    return [LabeledPrice(label=product.title, amount=product.amount)]
