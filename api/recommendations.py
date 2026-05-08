from dataclasses import dataclass

from bot.menu_data import MENU_DATA


@dataclass
class DishRecommendation:
    venue_id: str
    venue_name: str
    category_id: str
    category_name: str
    dish_id: str
    dish_name: str
    price: int
    score: int


def _tokens(text: str) -> set[str]:
    return {token.strip().lower() for token in text.split() if token.strip()}


def recommend_dishes(user_query: str, limit: int = 5) -> list[DishRecommendation]:
    query_tokens = _tokens(user_query)
    recommendations: list[DishRecommendation] = []

    for venue in MENU_DATA:
        for category in venue["categories"]:
            for dish in category["dishes"]:
                haystack = _tokens(f"{dish['name']} {category['name']} {venue['name']}")
                overlap = len(query_tokens & haystack)
                score = overlap * 10 + max(0, 100 - int(dish["price"]))
                recommendations.append(
                    DishRecommendation(
                        venue_id=venue["id"],
                        venue_name=venue["name"],
                        category_id=category["id"],
                        category_name=category["name"],
                        dish_id=dish["id"],
                        dish_name=dish["name"],
                        price=int(dish["price"]),
                        score=score,
                    )
                )

    recommendations.sort(key=lambda item: item.score, reverse=True)
    return recommendations[:limit]


def build_recommendation_text(user_query: str) -> str:
    top = recommend_dishes(user_query=user_query, limit=3)
    if not top:
        return "Поки не знайшов рекомендації. Спробуй інший запит."
    lines = [f"Рекомендації для запиту: {user_query}"]
    for item in top:
        lines.append(f"- {item.dish_name} ({item.venue_name}) - {item.price} грн")
    return "\n".join(lines)
