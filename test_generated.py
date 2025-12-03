import pytest
import random
from attention_model import get_simple_token_length, calculate_attention_weights

@pytest.mark.parametrize(
    "text, expected_count",
    [
        ("A simple sentence with five tokens", 5),
        ("one", 1),
        ("", 0),
        ("  leading and trailing spaces  ", 4),
        ("multiple   spaces    between", 3),
        ("words\nwith\tdifferent\rwhitespace", 4),
    ],
)
def test_get_simple_token_length(text, expected_count):
    """Tests the token counting function with various inputs."""
    assert get_simple_token_length(text) == expected_count

def test_calculate_attention_weights_empty_string():
    """Tests that an empty string results in an empty dictionary."""
    assert calculate_attention_weights("") == {}

def test_calculate_attention_weights_single_token():
    """Tests that a single token gets an attention weight of 1.0."""
    weights = calculate_attention_weights("transformer")
    assert len(weights) == 1
    assert weights["transformer"] == pytest.approx(1.0)

def test_calculate_attention_weights_is_deterministic_with_seed():
    """Tests that the function produces a predictable output with a fixed seed."""
    random.seed(42)
    text = "the quick brown fox"
    weights = calculate_attention_weights(text)

    # Check that all unique tokens are present as keys
    assert set(weights.keys()) == {"the", "quick", "brown", "fox"}

    # Check that the weights sum to 1.0
    assert sum(weights.values()) == pytest.approx(1.0)

    # Check against pre-calculated values for the given seed
    expected = {
        "the": 0.3871791142542571,
        "quick": 0.015144262143097103,
        "brown": 0.4432296115995574,
        "fox": 0.1544470120030884,
    }
    assert weights == pytest.approx(expected)

def test_calculate_attention_weights_with_repeated_tokens():
    """
    Tests the behavior with repeated tokens. The resulting dictionary should
    only contain the attention weight of the last occurrence of a token.
    """
    random.seed(101)
    text = "a rose is a rose"  # tokens: ['a', 'rose', 'is', 'a', 'rose']
    weights = calculate_attention_weights(text)

    # The dictionary should have one entry for each unique token
    assert set(weights.keys()) == {"a", "rose", "is"}
    assert len(weights) == 3

    # The sum of the values in the dictionary will NOT be 1.0 because
    # the weights for the first 'a' and 'rose' were overwritten.
    assert sum(weights.values()) != pytest.approx(1.0)

    # Check against pre-calculated values for the given seed and text
    # The final dict should map 'is' to its weight, the second 'a' to its
    # weight, and the second 'rose' to its weight.
    expected = {
        "is": 0.3867262445859187,
        "a": 0.04688599426913702,
        "rose": 0.10579536434656487,
    }
    assert weights == pytest.approx(expected)