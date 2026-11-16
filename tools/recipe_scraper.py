
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def find_recipe_data(data):
    """Recursively search JSON-LD data for a Schema.org Recipe."""

    if isinstance(data, list):
        for item in data:
            result = find_recipe_data(item)
            if result:
                return result

    elif isinstance(data, dict):
        item_type = data.get("@type", [])

        if isinstance(item_type, str):
            item_type = [item_type]

        if any("Recipe" in str(t) for t in item_type):
            return data

        for value in data.values():
            if isinstance(value, (dict, list)):
                result = find_recipe_data(value)
                if result:
                    return result

    return None


def scrape_recipe_page(url: str) -> str:
    """
    Fetch a recipe webpage and extract Schema.org Recipe data.
    Falls back to page text when structured recipe data is unavailable.
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
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=25,
            allow_redirects=True
        )
        response.raise_for_status()

    except requests.RequestException as error:
        return json.dumps({
            "success": False,
            "source_url": url,
            "error": f"Could not fetch recipe webpage: {str(error)}"
        })

    soup = BeautifulSoup(response.text, "html.parser")

    final_url = response.url
    original_path = parsed_url.path.rstrip("/")
    final_path = urlparse(final_url).path.rstrip("/")

    # Detect redirects from a recipe URL to a homepage.
    if original_path and final_path in ("", "/"):
        return json.dumps({
            "success": False,
            "source_url": url,
            "final_url": final_url,
            "error": (
                "The website redirected the recipe URL "
                "to its homepage. Please try another recipe URL."
            )
        })

    recipe_data = None

    # Search all JSON-LD scripts, including nested @graph objects.
    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):
        try:
            raw_data = script.string or script.get_text()
            data = json.loads(raw_data)

            recipe_data = find_recipe_data(data)

            if recipe_data:
                break

        except (json.JSONDecodeError, TypeError):
            continue

    if recipe_data:
        title = recipe_data.get("name")

        if not title:
            return json.dumps({
                "success": False,
                "source_url": url,
                "error": "Recipe structured data has no title."
            })

        result = {
            "success": True,
            "source_url": url,
            "title": title,
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
        # Remove irrelevant webpage elements.
        for element in soup([
            "script", "style", "nav",
            "footer", "header", "noscript"
        ]):
            element.decompose()

        # Prefer the actual page heading over the website title.
        h1 = soup.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else None

        description_tag = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        description = (
            description_tag.get("content")
            if description_tag else None
        )

        page_text = soup.get_text(
            separator=" ",
            strip=True
        )[:12000]

        if not title:
            return json.dumps({
                "success": False,
                "source_url": url,
                "error": (
                    "Could not identify a recipe title on this page. "
                    "Please try another recipe URL."
                )
            })

        result = {
            "success": True,
            "source_url": url,
            "title": title,
            "description": description,
            "page_text": page_text,
            "source": "Basic webpage extraction",
            "note": (
                "Structured recipe data was not found. "
                "Manual review required."
            )
        }

    return json.dumps(
        result,
        ensure_ascii=False,
        default=str
    )
