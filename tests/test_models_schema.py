from api.models import Category, Dish, NotificationOutbox, Order, User, Venue


def test_models_table_names() -> None:
    assert User.__tablename__ == "users"
    assert Venue.__tablename__ == "venues"
    assert Category.__tablename__ == "categories"
    assert Dish.__tablename__ == "dishes"
    assert Order.__tablename__ == "orders"
    assert NotificationOutbox.__tablename__ == "notification_outbox"
