"""
Script to fetch cooking instructions from Spoonacular API and add them to the CBR recipe database.
Adapted for the new CBR format structure.
"""
import json
import os
import time
import spoonacular
from spoonacular.rest import ApiException

def get_recipe_instructions(api_instance, recipe_id: int) -> str:
    """
    Fetch analyzed instructions for a recipe from Spoonacular API
    
    Args:
        api_instance: Spoonacular RecipesApi instance
        recipe_id: Recipe ID to fetch instructions for
        
    Returns:
        Instructions as string or empty string if not available
    """
    try:
        # Get recipe information with instructions
        recipe_info = api_instance.get_recipe_information(
            id=recipe_id,
            include_nutrition=False
        )
        
        # Check if instructions exist
        if hasattr(recipe_info, 'instructions') and recipe_info.instructions:
            return recipe_info.instructions
        
        # Alternative: Try to get analyzed instructions (structured steps)
        if hasattr(recipe_info, 'analyzed_instructions') and recipe_info.analyzed_instructions:
            instructions = []
            for instruction_set in recipe_info.analyzed_instructions:
                if hasattr(instruction_set, 'steps'):
                    for step in instruction_set.steps:
                        if hasattr(step, 'step'):
                            instructions.append(f"{step.number}. {step.step}")
            return "\n".join(instructions) if instructions else ""
        
        return ""
        
    except ApiException as e:
        print(f"  ⚠️  API error for recipe {recipe_id}: {e}")
        return ""
    except Exception as e:
        print(f"  ⚠️  Error fetching instructions for recipe {recipe_id}: {e}")
        return ""


def add_instructions_to_cbr_database(json_path: str, api_key: str, 
                                      batch_size: int = 50,
                                      start_from: int = 0):
    """
    Read CBR recipe database, fetch instructions for each recipe, and update the file.
    Processes in batches to handle large databases and API rate limits.
    
    Args:
        json_path: Path to the CBR recipe database JSON file
        api_key: Spoonacular API key
        batch_size: Number of recipes to process before saving (default: 50)
        start_from: Index to start processing from (for resume functionality)
    """
    # Configure Spoonacular API
    configuration = spoonacular.Configuration(host="https://api.spoonacular.com")
    configuration.api_key['apiKeyScheme'] = api_key
    
    # Load existing database
    print(f"📖 Loading database from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        database = json.load(f)
    
    recipes = database.get('recipes', [])
    total_recipes = len(recipes)
    recipes_updated = 0
    recipes_skipped = 0
    recipes_failed = 0
    
    print(f"   Found {total_recipes} recipes")
    print(f"   Starting from index: {start_from}")
    print(f"   Batch size: {batch_size}")
    
    # Create backup before starting
    backup_path = json_path.replace('.json', '_backup_before_instructions.json')
    print(f"\n💾 Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    # Process recipes
    with spoonacular.ApiClient(configuration) as api_client:
        api_instance = spoonacular.RecipesApi(api_client)
        
        for i, recipe in enumerate(recipes[start_from:], start=start_from):
            recipe_id = recipe.get('recipe_id')
            recipe_title = recipe.get('title', 'Unknown')
            
            # Check if instructions already exist and are not empty
            existing_instructions = recipe.get('instructions', '')
            if existing_instructions and len(existing_instructions) > 10:
                recipes_skipped += 1
                if (i + 1) % 100 == 0:
                    print(f"  [{i + 1}/{total_recipes}] Skipping (already has instructions)")
                continue
            
            print(f"  [{i + 1}/{total_recipes}] Fetching: {recipe_title[:40]}... (ID: {recipe_id})")
            
            # Fetch instructions from API
            instructions = get_recipe_instructions(api_instance, recipe_id)
            
            if instructions:
                recipe['instructions'] = instructions
                recipes_updated += 1
                print(f"    ✓ Added ({len(instructions)} chars)")
            else:
                recipes_failed += 1
                print(f"    ✗ No instructions found")
            
            # Rate limiting: wait between requests
            time.sleep(0.6)  # ~100 requests per minute
            
            # Save progress every batch_size recipes
            if (recipes_updated + 1) % batch_size == 0:
                print(f"\n💾 Saving progress ({recipes_updated} updated so far)...")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(database, f, ensure_ascii=False, indent=2)
                print("   Saved!\n")
    
    # Final save
    print(f"\n💾 Saving final database: {json_path}")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"   Total recipes: {total_recipes}")
    print(f"   ✓ Updated with instructions: {recipes_updated}")
    print(f"   → Skipped (already had): {recipes_skipped}")
    print(f"   ✗ Failed to fetch: {recipes_failed}")
    print(f"\n✅ Done!")


def check_missing_instructions(json_path: str) -> dict:
    """
    Check how many recipes are missing instructions.
    
    Args:
        json_path: Path to the CBR recipe database JSON file
        
    Returns:
        Statistics dictionary
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        database = json.load(f)
    
    recipes = database.get('recipes', [])
    
    with_instructions = 0
    without_instructions = 0
    
    for recipe in recipes:
        instructions = recipe.get('instructions', '')
        if instructions and len(instructions) > 10:
            with_instructions += 1
        else:
            without_instructions += 1
    
    print(f"\n📊 Instructions Status:")
    print(f"   ✓ With instructions: {with_instructions}")
    print(f"   ✗ Missing instructions: {without_instructions}")
    print(f"   Total: {len(recipes)}")
    
    return {
        "with_instructions": with_instructions,
        "without_instructions": without_instructions,
        "total": len(recipes)
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch instructions from Spoonacular API')
    parser.add_argument('--file', '-f', default='filtered_recipes_cbr.json',
                       help='Path to the CBR recipe database JSON file')
    parser.add_argument('--check', '-c', action='store_true',
                       help='Only check status, do not fetch')
    parser.add_argument('--start', '-s', type=int, default=0,
                       help='Start from this recipe index (for resume)')
    parser.add_argument('--batch', '-b', type=int, default=50,
                       help='Save every N recipes')
    
    args = parser.parse_args()
    
    if args.check:
        check_missing_instructions(args.file)
    else:
        # Get API key from environment variable
        api_key = os.environ.get("API_KEY")
        if not api_key:
            print("❌ Error: API_KEY environment variable not set")
            print("   Set it with: $env:API_KEY='your_api_key_here' (PowerShell)")
            exit(1)
        
        print("🚀 Starting to fetch and add instructions to recipes...")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
        
        add_instructions_to_cbr_database(
            args.file, 
            api_key, 
            batch_size=args.batch,
            start_from=args.start
        )
