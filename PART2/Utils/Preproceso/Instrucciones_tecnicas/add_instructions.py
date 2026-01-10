"""
Script to fetch cooking instructions from Spoonacular API and add them to cbr_menu_database.json
"""
import json
import os
import time
import spoonacular
from spoonacular.rest import ApiException

def get_recipe_instructions(api_instance, recipe_id):
    """
    Fetch analyzed instructions for a recipe from Spoonacular API
    
    Args:
        api_instance: Spoonacular RecipesApi instance
        recipe_id: Recipe ID to fetch instructions for
        
    Returns:
        List of instruction steps (strings) or empty list if not available
    """
    try:
        # Get recipe information with instructions
        recipe_info = api_instance.get_recipe_information(
            id=recipe_id,
            include_nutrition=False
        )
        
        # Check if instructions exist
        if hasattr(recipe_info, 'instructions') and recipe_info.instructions:
            # Return plain text instructions
            return recipe_info.instructions
        
        # Alternative: Try to get analyzed instructions (structured steps)
        if hasattr(recipe_info, 'analyzed_instructions') and recipe_info.analyzed_instructions:
            instructions = []
            for instruction_set in recipe_info.analyzed_instructions:
                if hasattr(instruction_set, 'steps'):
                    for step in instruction_set.steps:
                        if hasattr(step, 'step'):
                            instructions.append(f"{step.number}. {step.step}")
            return "\n".join(instructions) if instructions else "No instructions available"
        
        return "No instructions available"
        
    except ApiException as e:
        print(f"  ⚠️  API error for recipe {recipe_id}: {e}")
        return "Instructions not available"
    except Exception as e:
        print(f"  ⚠️  Error fetching instructions for recipe {recipe_id}: {e}")
        return "Instructions not available"


def add_instructions_to_database(json_path, api_key):
    """
    Read cbr_menu_database.json, fetch instructions for each recipe, and update the file
    
    Args:
        json_path: Path to cbr_menu_database.json
        api_key: Spoonacular API key
    """
    # Configure Spoonacular API
    configuration = spoonacular.Configuration(host="https://api.spoonacular.com")
    configuration.api_key['apiKeyScheme'] = api_key
    
    # Load existing database
    print(f"📖 Loading database from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        database = json.load(f)
    
    total_recipes = 0
    total_menus = len(database.get('menus', []))
    
    # Process each menu
    with spoonacular.ApiClient(configuration) as api_client:
        api_instance = spoonacular.RecipesApi(api_client)
        
        for menu_idx, menu in enumerate(database.get('menus', []), 1):
            print(f"\n🍽️  Menu {menu_idx}/{total_menus}: {menu.get('menu_name')}")
            
            # Process each course (starter, main, dessert)
            for course_type in ['starter', 'main', 'dessert']:
                course = menu.get('courses', {}).get(course_type)
                
                if course and 'recipe_id' in course:
                    recipe_id = course['recipe_id']
                    recipe_title = course.get('title', 'Unknown')
                    
                    # Check if instructions already exist
                    if 'instructions' in course:
                        print(f"  ✓ {course_type.capitalize()}: {recipe_title} (instructions already exist)")
                        continue
                    
                    print(f"  🔍 {course_type.capitalize()}: Fetching instructions for {recipe_title} (ID: {recipe_id})...")
                    
                    # Fetch instructions from API
                    instructions = get_recipe_instructions(api_instance, recipe_id)
                    
                    # Add instructions to course
                    course['instructions'] = instructions
                    total_recipes += 1
                    
                    print(f"  ✓ Added ({len(instructions)} chars)")
                    
                    # Rate limiting: wait 0.5s between requests (to avoid hitting API limits)
                    time.sleep(0.5)
    
    # Save updated database
    backup_path = json_path.replace('.json', '_backup.json')
    print(f"\n💾 Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Saving updated database: {json_path}")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Done! Added instructions to {total_recipes} recipes across {total_menus} menus")


if __name__ == "__main__":
    # Configuration
    JSON_PATH = r'filtered_recipes111.json'
    
    # Get API key from environment variable
    api_key = os.environ.get("API_KEY")
    if not api_key:
        print("❌ Error: API_KEY environment variable not set")
        print("   Set it with: $env:API_KEY='your_api_key_here' (PowerShell)")
        exit(1)
    
    print("🚀 Starting to fetch and add instructions to recipes...")
    print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
    
    add_instructions_to_database(JSON_PATH, api_key)
