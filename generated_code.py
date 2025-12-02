def get_simple_token_length(text: str) -> int:
    """
    Returns the number of whitespace-separated tokens in a given string.
    """
    if not text.strip():
        return 0
    return len(text.split())

if __name__ == '__main__':
    sample_text = "This is a sample sentence for token counting."
    token_count = get_simple_token_length(sample_text)
    print(f"The text '{sample_text}' has {token_count} tokens.")

    empty_text = ""
    print(f"The text '{empty_text}' has {get_simple_token_length(empty_text)} tokens.")

    whitespace_only = "   "
    print(f"The text '{whitespace_only}' has {get_simple_token_length(whitespace_only)} tokens.")