
# Pure Python Logic Test for Rank Transition
# No Django required as we testing the comparison logic string-to-string

def test_logic(prev_rank_name, new_rank_name):
    print(f"\nTesting Transition: {prev_rank_name} -> {new_rank_name}")
    
    # -------------------------------------------------------------
    # LOGIC FROM SERVICES.PY
    # -------------------------------------------------------------
    
    # Check explicitly for Tier Name match
    def get_tier_name(rank_name):
        # Normalized lookup
        rank_lower = rank_name.lower()
        
        # Special Case: Grandmaster-5
        if 'grandmaster-5' in rank_lower or 'grandmaster 5' in rank_lower:
            return 'Grandmaster-5'
        
        # Standard Tiers
        tiers = [
            'Bronze', 'Silver', 'Emberlaure', 'Tome', 'Eternal', 
            'Arcane', 'Mystic', 'Verdant', 'Frostheart', 'Crystal', 
            "Inferno's", 'Infernos', 'Stellar', 'Crown', 'Lunar', 
            'Galactic', 'Grandmaster'
        ]
        
        for tier in tiers:
            if tier.lower() in rank_lower:
                # Return standard key
                return "Infernos" if "inferno" in tier.lower() else tier
                
        return 'Bronze' # Default fallback
    
    prev_tier = get_tier_name(prev_rank_name) if prev_rank_name else None
    new_tier = get_tier_name(new_rank_name)
    
    is_major_rank_up = False
    if prev_tier != new_tier:
        is_major_rank_up = True
        
    print(f"  Prev Tier: {prev_tier}")
    print(f"  New Tier:  {new_tier}")
    print(f"  MAJOR RANK UP: {is_major_rank_up}")

# Test Cases based on user report
test_logic(None, "Bronze 1")
test_logic("Bronze 5", "Silver 1")
test_logic("Silver 5", "Emberlaure 1")
test_logic("Emberlaure 5", "Tome 1")
test_logic("Tome 5", "Arcane 1")
test_logic("Emberlaure 5", "Tome 2") # Skipped rank case

