class Business:
    def __init__(self):
        self.money = 0.0
        self.revenue = 0.0
        self.expenses = 0.0
        self.customers = 0
        self.products = []
        self.sales = []

    def create_product(self, name, price, cost):
        product = {
            "name": name,
            "price": price,
            "cost": cost
        }

        self.products.append(product)
        self.expenses += cost
        self.money -= cost

        return product

    def make_sale(self, product, customer):
        price = product["price"]

        self.revenue += price
        self.money += price
        self.customers += 1

        sale = {
            "product": product["name"],
            "customer": customer,
            "amount": price
        }

        self.sales.append(sale)

        return sale

    def survival_score(self):
        if self.money < 0:
            return 0

        if self.money == 0:
            return 50

        return min(100, 50 + self.money * 5)

    def status(self):
        print("\n========================================")
        print("       AI BUSINESS STATUS")
        print("========================================")
        print(f"Money:       ${self.money:.2f}")
        print(f"Revenue:     ${self.revenue:.2f}")
        print(f"Expenses:    ${self.expenses:.2f}")
        print(f"Customers:   {self.customers}")
        print(f"Products:    {len(self.products)}")
        print(f"Survival:    {self.survival_score():.0f}%")
        print("========================================")