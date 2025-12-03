def get_simple_token_length(text: str) -> int:
    """Returns the number of tokens based on whitespace splitting."""
    return len(text.split())

if __name__ == '__main__':
    example_text = "Transformer models are powerful."
    token_count = get_simple_token_length(example_text)
    print(f"The text '{example_text}' has {token_count} simple tokens.")
    # Expected output: The text 'Transformer models are powerful.' has 4 simple tokens.