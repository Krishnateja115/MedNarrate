import re

def verify_response_against_source(response: str, source_text: str) -> tuple[str, bool]:
    """
    Verifies that numerical values in the LLM response actually exist in the source text.
    If not, appends a safety disclaimer.
    
    Returns:
        tuple[str, bool]: (Modified response, True if safe else False)
    """
    # Find all decimal or integer numbers in the response (e.g. 12, 5.5, 120.45)
    numbers_in_response = set(re.findall(r'\b\d+(?:\.\d+)?\b', response))
    
    # We don't want to alert on very common non-medical numbers (like years or small counts),
    # but for safety, we check all of them against the source.
    # A more sophisticated approach would only check numbers adjacent to medical units.
    
    unsafe = False
    for num in numbers_in_response:
        if num not in source_text:
            unsafe = True
            break
            
    if unsafe:
        disclaimer = "\n\n⚠️ Note: Some values in this response could not be verified in your report. Please confirm with your healthcare provider."
        if disclaimer not in response:
            response += disclaimer
            
    return response, not unsafe
