
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def scrape_recipe_page(url: str) -> str:
    """
    Fetch a public recipe webpage and extract its structured recipe data.
    This function runs directly in Python, not through LLM tool calling.
    """

    parsed_url = urlparse(url)

    if (
        parsed_url.scheme not in ("http", "https")
        or not parsed_url.netloc
    ):
        return json.dumps({
            "success": False,
            "error": "Please provide a valid HTTP or HTTPS URL."
        })

    headers = {
        "User-Agent": "Mozilla/5.0 AfrodeliciousRecipeCollector/1.0"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )
        response.raise_for_status()

    except requests.RequestException as error:
        return json.dumps({
            "success": False,
            "source_url": url,
            "error": str(error)
        })

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else None

    description_tag = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    description = (
        description_tag.get("content")
        if description_tag else None
    )

    recipe_data = None

    # Find Schema.org Recipe data
    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):
        try:
            data = json.loads(
                script.string or script.get_text()
            )

            items = data if isinstance(data, list) else [data]

            for item in items:
                if not isinstance(item, dict):
                    continue

                item_type = item.get("@type", [])

                if isinstance(item_type, str):
                    item_type = [item_type]

                if "Recipe" in item_type:
                    recipe_data = item
                    break

                for graph_item in item.get("@graph", []):
                    if not isinstance(graph_item, dict):
                        continue

                    graph_type = graph_item.get("@type", [])

                    if isinstance(graph_type, str):
                        graph_type = [graph_type]

                    if "Recipe" in graph_type:
                        recipe_data = graph_item
                        break

                if recipe_data:
                    break

            if recipe_data:
                break

        except (json.JSONDecodeError, TypeError):
            continue

    if recipe_data:

        result = {
            "success": True,
            "source_url": url,
            "title": recipe_data.get("name"),
            "description": recipe_data.get("description"),
            "ingredients": recipe_data.get("recipeIngredient", []),
            "instructions": recipe_data.get("recipeInstructions", []),
            "prep_time": recipe_data.get("prepTime"),
            "cook_time": recipe_data.get("cookTime"),
            "servings": recipe_data.get("recipeYield"),
            "image": recipe_data.get("image"),
            "source": "Schema.org Recipe structured data"
        }

    else:
        for element in soup(
            ["script", "style", "nav", "footer", "header"]
        ):
            element.decompose()

        result = {
            "success": True,
            "source_url": url,
            "title": title,
            "description": description,
            "page_text": soup.get_text(
                separator=" ",
                strip=True
            )[:5000],
            "source": "Basic webpage extraction",
            "note": "Structured recipe data was not found. Manual review required."
        }

    return json.dumps(
        result,
        ensure_ascii=False,
        default=str
    )
