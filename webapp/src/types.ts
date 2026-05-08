export type Dish = {
  id: string;
  name: string;
  price: number;
  modifiers: string[];
};

export type Category = {
  id: string;
  name: string;
  dishes: Dish[];
};

export type Venue = {
  id: string;
  name: string;
  categories: Category[];
};

export type CartItem = {
  venueId: string;
  categoryId: string;
  dishId: string;
  name: string;
  price: number;
};
