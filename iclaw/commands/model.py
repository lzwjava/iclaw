import sys
from iclaw.github_api import get_models

def handle_model_command(copilot_token, current_model):
    try:
        model_data = get_models(copilot_token)
    except Exception as e:
        print(f"Error fetching models: {e}\n", file=sys.stderr)
        return current_model
        
    groups = {}
    for m in model_data:
        owner = m.get("owned_by", "unknown")
        groups.setdefault(owner, []).append(m["id"])
    
    flat_models = [m["id"] for m in model_data]
    print(f"\nCurrent model: {current_model}")
    print("Available models:")
    
    idx = 1
    model_index = {}
    for owner, ids in groups.items():
        print(f"  [{owner}]")
        for mid in ids:
            marker = "*" if mid == current_model else " "
            print(f"  {marker} {idx}. {mid}")
            model_index[idx] = mid
            idx += 1
            
    try:
        choice = input("Select model (number or name, Enter to keep current): ").strip()
        if choice:
            if choice.isdigit():
                n = int(choice)
                if n in model_index:
                    print(f"Model set to: {model_index[n]}\n")
                    return model_index[n]
                else:
                    print("Invalid selection.\n")
            elif choice in flat_models:
                print(f"Model set to: {choice}\n")
                return choice
            else:
                print(f"Unknown model '{choice}'. Keeping {current_model}\n")
    except (EOFError, KeyboardInterrupt):
        print()
        
    return current_model
