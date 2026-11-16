
import os
import json

from dotenv import load_dotenv
from crewai import LLM, Agent, Crew, Task, Process

from agents.marketing_agent import create_marketing_agent
from agents.sam_agent import create_sam_agent
from agents.recipe_collector_agent import create_recipe_collector_agent

from tools.recipe_scraper import scrape_recipe_page
from brand_context import BRAND_CONTEXT


load_dotenv()


def create_crew(task_type, user_request, recipe_url=None, agent_config=None):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env")

    llm = LLM(
        model="groq/openai/gpt-oss-120b",
        api_key=api_key,
        temperature=0.2
    )

    scraped_data = None

    # Create the agent using saved configuration when available.
    def build_configured_agent(default_factory):

        if not agent_config:
            return default_factory(llm)

        role = agent_config.get("role")
        goal = agent_config.get("goal")
        backstory = agent_config.get("backstory")
        instructions = agent_config.get("instructions", "")

        if not role or not goal or not backstory:
            raise ValueError(
                "Agent configuration is incomplete. "
                "Please update its role, goal and backstory."
            )

        if instructions and instructions.strip():
            backstory = (
                backstory
                + "\n\nADDITIONAL ADMIN INSTRUCTIONS:\n"
                + instructions
            )

        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

    # Select the appropriate specialist.
    if task_type == "marketing":

        agent = build_configured_agent(create_marketing_agent)

        expected_output = (
            "A structured marketing response with strategies, "
            "content ideas and recommendations. All external content "
            "must be labelled as a draft requiring human approval."
        )

    elif task_type == "development":

        agent = build_configured_agent(create_sam_agent)

        expected_output = (
            "A structured technical response with requirements, "
            "architecture, implementation plans or code drafts. "
            "Clearly identify assumptions and untested code."
        )

    elif task_type == "recipe":

        if not recipe_url:
            raise ValueError(
                "A recipe_url is required for Recipe Collector."
            )

        print("\n--- FETCHING RECIPE WEBPAGE ---")

        scraped_result = scrape_recipe_page(recipe_url)
        scraped_data = json.loads(scraped_result)

        if not scraped_data.get("success"):
            raise RuntimeError(
                f"Recipe scraping failed: {scraped_data.get('error')}"
            )

        print("\n--- RECIPE DATA EXTRACTED ---")
        print(json.dumps(scraped_data, indent=2, ensure_ascii=False))

        agent = build_configured_agent(create_recipe_collector_agent)

        expected_output = (
            "A structured recipe JSON response with source attribution, "
            "ingredients, instructions and missing fields."
        )

    else:
        raise ValueError(
            "Invalid task_type. Choose marketing, development or recipe."
        )

    # Only Recipe Collector receives Afrodelicious brand context.
    if task_type == "recipe":

        task_description = f"""
        AFRODELICIOUS RECIPE WORKFLOW CONTEXT:

        {BRAND_CONTEXT}

        User request:
        {user_request}

        Extracted webpage information:
        {json.dumps(scraped_data, ensure_ascii=False, indent=2)}

        Organize the supplied information into the required
        Afrodelicious recipe JSON format.

        Do not invent missing information.
        Preserve the original source URL.
        Mark missing fields clearly.
        Require human review before any production import.
        """

    else:

        # Brendy and SAM are standalone assistants.
        # They do not receive Afrodelicious brand context.
        task_description = f"""
        User request:
        {user_request}

        Complete this request according to your role,
        responsibilities and safety instructions.

        Be transparent about missing information.
        Do not claim actions that were not performed.
        Clearly label assumptions and hypothetical examples.
        """

    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    return crew


if __name__ == "__main__":

    task_type = "recipe"

    user_request = (
        "Extract and organize this recipe for Afrodelicious. "
        "Return structured JSON and identify missing information."
    )

    recipe_url = (
        "https://www.bbcgoodfood.com/recipes/easy-pancakes"
    )

    result = create_crew(
        task_type=task_type,
        user_request=user_request,
        recipe_url=recipe_url
    ).kickoff()

    print("\n--- AFRODELICIOUS AI OUTPUT ---")
    print(result)
