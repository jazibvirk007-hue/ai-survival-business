class AIBrain:

    def __init__(self):
        self.memory = []

    def analyze_market(self):
        opportunities = [
            {
                "name": "Social Media Content Pack",
                "demand": 85,
                "competition": 55,
                "price": 20,
                "difficulty": 20,
                "risk": 15
            },
            {
                "name": "Resume Optimization Service",
                "demand": 80,
                "competition": 50,
                "price": 30,
                "difficulty": 25,
                "risk": 10
            },
            {
                "name": "Small Business Content Service",
                "demand": 90,
                "competition": 45,
                "price": 25,
                "difficulty": 30,
                "risk": 15
            },
            {
                "name": "Short Video Script Service",
                "demand": 88,
                "competition": 50,
                "price": 25,
                "difficulty": 20,
                "risk": 10
            }
        ]

        return opportunities

    def score_opportunity(self, opportunity):

        demand = opportunity["demand"]
        competition = opportunity["competition"]
        price = opportunity["price"]
        difficulty = opportunity["difficulty"]
        risk = opportunity["risk"]

        score = (
            demand * 0.35
            + (100 - competition) * 0.20
            + min(price * 2, 100) * 0.20
            + (100 - difficulty) * 0.15
            + (100 - risk) * 0.10
        )

        return round(score, 2)

    def choose_opportunity(self, opportunities):

        scored = []

        for opportunity in opportunities:

            score = self.score_opportunity(opportunity)

            opportunity["score"] = score

            scored.append(opportunity)

        scored.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return scored[0], scored

    def choose_customer(self, opportunity):

        customers = {
            "Social Media Content Pack":
                "Small businesses with weak social media content",

            "Resume Optimization Service":
                "Job seekers with outdated resumes",

            "Small Business Content Service":
                "Small businesses that need regular marketing content",

            "Short Video Script Service":
                "Creators and businesses making short-form videos"
        }

        return customers[opportunity["name"]]

    def decide_price(self, opportunity):

        base_price = opportunity["price"]

        if opportunity["demand"] >= 90:
            return base_price + 5

        return base_price

    def remember(self, event):

        self.memory.append(event)

    def show_memory(self):

        print("\n🧠 AI MEMORY")

        if not self.memory:
            print("No previous experience.")

        for item in self.memory:
            print("-", item)