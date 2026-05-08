from typing import TypedDict


class Dish(TypedDict):
    id: str
    name: str
    price: int
    modifiers: list[str]


class Category(TypedDict):
    id: str
    name: str
    dishes: list[Dish]


class Venue(TypedDict):
    id: str
    name: str
    categories: list[Category]


MENU_DATA: list[Venue] = [
    {
        "id": "vinson-git",
        "name": "Vinson Git",
        "categories": [
            {
                "id": "pizza",
                "name": "Піца",
                "dishes": [
                    {
                        "id": "pepperoni",
                        "name": "Pepperoni",
                        "price": 265,
                        "modifiers": ["extra_cheese", "spicy_oil", "double_meat"],
                    },
                    {
                        "id": "margarita",
                        "name": "Margarita",
                        "price": 230,
                        "modifiers": ["extra_cheese", "gluten_free"],
                    },
                    {
                        "id": "four_cheese",
                        "name": "Four Cheese",
                        "price": 280,
                        "modifiers": ["extra_cheese", "truffle_oil"],
                    },
                ],
            },
            {
                "id": "drinks",
                "name": "Напої",
                "dishes": [
                    {"id": "cola", "name": "Cola", "price": 60, "modifiers": ["ice", "no_ice"]},
                    {
                        "id": "water",
                        "name": "Water",
                        "price": 40,
                        "modifiers": ["still", "sparkling"],
                    },
                ],
            },
        ],
    },
    {
        "id": "smartmenu-demo",
        "name": "SmartMenu Demo",
        "categories": [
            {
                "id": "sushi",
                "name": "Суші",
                "dishes": [
                    {
                        "id": "california",
                        "name": "California",
                        "price": 320,
                        "modifiers": ["spicy"],
                    },
                    {
                        "id": "philadelphia",
                        "name": "Philadelphia",
                        "price": 350,
                        "modifiers": ["extra_salmon"],
                    },
                ],
            }
        ],
    },
]


def get_venue(venue_id: str) -> Venue | None:
    return next((venue for venue in MENU_DATA if venue["id"] == venue_id), None)


def get_category(venue_id: str, category_id: str) -> Category | None:
    venue = get_venue(venue_id)
    if not venue:
        return None
    return next(
        (category for category in venue["categories"] if category["id"] == category_id), None
    )


def get_dish(venue_id: str, category_id: str, dish_id: str) -> Dish | None:
    category = get_category(venue_id, category_id)
    if not category:
        return None
    return next((dish for dish in category["dishes"] if dish["id"] == dish_id), None)
