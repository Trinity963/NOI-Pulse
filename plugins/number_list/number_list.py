import re

def run(tool, user_text):
    # Split text by sentences (period, question mark, exclamation) and clean up
    sentences = re.split(r'(?<=[.!?])\s+', user_text.strip())
    
    # Remove empty strings and clean whitespace
    items = [s.strip() for s in sentences if s.strip()]
    
    # Number each item
    numbered_list = []
    for i, item in enumerate(items, 1):
        numbered_list.append(f"{i}. {item}")
    
    return "\n".join(numbered_list)