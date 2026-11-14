
import re
from crew import create_crew


def detect_agent(user_request):

    request = user_request.lower()

    recipe_keywords = [
        "scrape recipe",
        "collect recipe",
        "extract recipe",
        "recipe webpage",
        "recipe ingredients",
        "recipe collection",
        "import recipe"
    ]

    marketing_keywords = [
        "marketing",
        "instagram caption",
        "social media",
        "seo",
        "campaign",
        "influencer",
        "advertisement",
        "email marketing",
        "brand promotion",
        "content strategy"
    ]

    development_keywords = [
        "develop",
        "build",
        "website",
        "web app",
        "application",
        "database",
        "api",
        "coding",
        "debug",
        "software",
        "technical",
        "architecture",
        "prD"
    ]

    if any(keyword in request for keyword in recipe_keywords):
        return "recipe"

    if any(keyword in request for keyword in marketing_keywords):
        return "marketing"

    if any(keyword in request for keyword in development_keywords):
        return "development"

    return None


def run_orchestrator(user_request, recipe_url=None):

    task_type = detect_agent(user_request)

    if task_type is None:
        return {
            "success": False,
            "message": (
                "Could not identify the correct agent. "
                "Please clarify whether this is a marketing, "
                "development or recipe collection task."
            )
        }

    print(f"\nSelected Agent: {task_type.upper()}")

    try:
        crew = create_crew(
            task_type=task_type,
            user_request=user_request,
            recipe_url=recipe_url
        )

        result = crew.kickoff()

        return {
            "success": True,
            "selected_agent": task_type,
            "result": str(result)
        }

    except Exception as error:
        return {
            "success": False,
            "selected_agent": task_type,
            "message": str(error)
        }


if __name__ == "__main__":

    print("AFRODELICIOUS AI ORCHESTRATOR")
    print("--------------------------------")

    user_request = input("\nEnter your request: ")

    recipe_url = None

    if detect_agent(user_request) == "recipe":
        recipe_url = input("Enter recipe webpage URL: ").strip()

    response = run_orchestrator(
        user_request=user_request,
        recipe_url=recipe_url
    )

    print("\n--- ORCHESTRATOR RESPONSE ---")
    print(response)
