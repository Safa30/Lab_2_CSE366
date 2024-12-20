import random
import matplotlib.pyplot as plt


# Utility function for random sampling from a distribution
def select_from_dist(item_prob_dist):
    ranreal = random.random()
    for item, prob in item_prob_dist.items():
        if ranreal < prob:
            return item
        ranreal -= prob
    raise RuntimeError(f"{item_prob_dist} is not a valid probability distribution")


# Plotting Class
class PlotHistory:
    def __init__(self, agent, environment):
        self.agent = agent
        self.environment = environment

    def plot_history(self):
        plt.figure(figsize=(12, 8))

        # Price history plot
        plt.subplot(2, 1, 1)
        plt.plot(self.environment.price_history, label="Price", color="blue", linewidth=2)
        plt.axhline(
            self.agent.average_price, color="green", linestyle="--", label="Average Price"
        )
        plt.title("Smartphone Price Trend Over Time")
        plt.ylabel("Price (BDT)")
        plt.legend()

        # Stock levels and purchases plot
        plt.subplot(2, 1, 2)
        plt.plot(
            self.environment.stock_history,
            label="Stock Level",
            color="blue",
            linewidth=2,
        )
        plt.bar(
            range(len(self.agent.buy_history)),
            self.agent.buy_history,
            label="Units Purchased",
            color="orange",
            alpha=0.7,
        )
        plt.title("Stock Levels and Purchases Over Time")
        plt.ylabel("Stock / Purchases")
        plt.xlabel("Time Step")
        plt.legend()

        plt.tight_layout()
        plt.show()


# Environment Class
class SmartphoneEnvironment:
    price_delta = [10, -80, 20, -60, 5, 50, -100, 30, -20, 0]  # Enhanced price drops
    noise_sd = 20  # Increased standard deviation for more variation

    def __init__(self):
        self.time = 0
        self.stock = 50
        self.price = 600
        self.stock_history = [self.stock]
        self.price_history = [self.price]

    def initial_percept(self):
        return {"price": self.price, "stock": self.stock}

    def do_action(self, action):
        daily_sales = select_from_dist({3: 0.2, 5: 0.3, 7: 0.3, 10: 0.2})
        bought = action.get("buy", 0)
        self.stock = max(0, self.stock + bought - daily_sales)
        self.time += 1
        self.price += (
            self.price_delta[self.time % len(self.price_delta)]
            + random.gauss(0, self.noise_sd)
        )
        self.price = max(100, self.price)  # Ensure price doesn't drop too low
        self.stock_history.append(self.stock)
        self.price_history.append(self.price)
        return {"price": self.price, "stock": self.stock}


# Controller Classes
class PriceMonitoringController:
    def __init__(self, agent, discount_threshold=0.2):
        self.agent = agent
        self.discount_threshold = discount_threshold

    def monitor(self, percept):
        current_price = percept["price"]
        discount_price_threshold = (1 - self.discount_threshold) * self.agent.average_price
        print(f"Checking price: {current_price:.2f}, Discount threshold: {discount_price_threshold:.2f}")
        if current_price < discount_price_threshold:
            return True
        return False


class InventoryMonitoringController:
    def __init__(self, threshold=10):
        self.threshold = threshold

    def monitor(self, percept):
        return percept["stock"] < self.threshold


class OrderingController:
    def __init__(self, price_controller, inventory_controller):
        self.price_controller = price_controller
        self.inventory_controller = inventory_controller

    def order(self, percept, price_discount, low_stock):
        current_price = percept["price"]

        # Use precomputed monitoring results
        if price_discount and not low_stock:
            discount_ratio = (self.price_controller.agent.average_price - current_price) / self.price_controller.agent.average_price
            tobuy = int(15 * (1 + discount_ratio))  # Buy more based on discount size
            print(f"Discount detected! Discount ratio: {discount_ratio:.2f}. Ordering {tobuy} units.\n")
            return tobuy
        elif low_stock:
            print("Low stock detected. Ordering 10 units.\n")
            return 10
        print("No action taken. No significant discount or stock issue.\n")
        return 0


# Agent Class
class SmartphoneAgent:
    def __init__(self):
        self.average_price = 600  # Initial average price
        self.buy_history = []  # Tracks buying decisions
        self.total_spent = 0  # Tracks total expenditure

        # Controllers
        self.price_controller = PriceMonitoringController(self)
        self.inventory_controller = InventoryMonitoringController()
        self.ordering_controller = OrderingController(self.price_controller, self.inventory_controller)

    def select_action(self, percept):
        current_price = percept["price"]
        self.average_price += (current_price - self.average_price) * 0.1

        # Determine monitoring results (calculate once)
        price_discount = self.price_controller.monitor(percept)
        low_stock = self.inventory_controller.monitor(percept)

        # Use the ordering controller to decide how many units to buy
        tobuy = self.ordering_controller.order(percept, price_discount, low_stock)

        # Track expenditure and decisions
        self.total_spent += tobuy * current_price
        self.buy_history.append(tobuy)

        # Print detailed decision log
        print(f"Time: {len(self.buy_history) - 1}")
        print(f"Price: {current_price:.0f}, Stock: {percept['stock']}")
        print(
            f"Price Monitoring: {'Discount detected' if price_discount else 'No discount'} "
            f"(Price: {current_price}, Average: {self.average_price:.0f})"
        )
        print(
            f"Inventory Monitoring: {'Low stock detected' if low_stock else 'Sufficient stock'} "
            f"(Stock: {percept['stock']})"
        )
        print(f"Action: Order {tobuy} units\n")

        return {"buy": tobuy}


# Simulation Class
class Simulation:
    def __init__(self, agent, environment):
        self.agent = agent
        self.environment = environment
        self.percept = self.environment.initial_percept()

    def run(self, steps):
        for step in range(steps):
            action = self.agent.select_action(self.percept)
            self.percept = self.environment.do_action(action)


# Main Simulation
if __name__ == "__main__":
    environment = SmartphoneEnvironment()
    agent = SmartphoneAgent()
    simulation = Simulation(agent, environment)
    simulation.run(20)
    plotter = PlotHistory(agent, environment)
    plotter.plot_history()
