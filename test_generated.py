from generated_code import merge_sort, merge

def test_merge_empty_lists():
    assert merge([], []) == []

def test_merge_one_empty_list():
    assert merge([1, 2, 3], []) == [1, 2, 3]
    assert merge([], [4, 5, 6]) == [4, 5, 6]

def test_merge_basic_sorted_lists():
    assert merge([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]

def test_merge_lists_with_overlap():
    assert merge([1, 2, 5], [3, 4, 6]) == [1, 2, 3, 4, 5, 6]

def test_merge_lists_with_duplicates():
    assert merge([1, 2, 2, 5], [2, 3, 5, 6]) == [1, 2, 2, 2, 3, 5, 5, 6]

def test_merge_lists_one_fully_before_other():
    assert merge([1, 2, 3], [4, 5, 6]) == [1, 2, 3, 4, 5, 6]
    assert merge([4, 5, 6], [1, 2, 3]) == [1, 2, 3, 4, 5, 6]

def test_merge_lists_different_lengths():
    assert merge([1, 5, 10], [2, 3]) == [1, 2, 3, 5, 10]
    assert merge([2, 3], [1, 5, 10]) == [1, 2, 3, 5, 10]

def test_merge_lists_with_negative_numbers():
    assert merge([-5, -1, 0], [-3, 2, 4]) == [-5, -3, -1, 0, 2, 4]

def test_merge_lists_with_floats():
    assert merge([1.1, 3.3], [2.2, 4.4]) == [1.1, 2.2, 3.3, 4.4]

def test_merge_lists_all_equal():
    assert merge([5, 5, 5], [5, 5]) == [5, 5, 5, 5, 5]


def test_merge_sort_empty_list():
    assert merge_sort([]) == []

def test_merge_sort_single_element_list():
    assert merge_sort([5]) == [5]

def test_merge_sort_already_sorted_list():
    arr = [1, 2, 3, 4, 5]
    assert merge_sort(arr) == [1, 2, 3, 4, 5]

def test_merge_sort_reverse_sorted_list():
    arr = [5, 4, 3, 2, 1]
    assert merge_sort(arr) == [1, 2, 3, 4, 5]

def test_merge_sort_unsorted_list():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    assert merge_sort(arr) == [1, 1, 2, 3, 4, 5, 6, 9]

def test_merge_sort_list_with_duplicates():
    arr = [5, 2, 8, 2, 5, 1, 8]
    assert merge_sort(arr) == [1, 2, 2, 5, 5, 8, 8]

def test_merge_sort_list_with_negative_numbers():
    arr = [-3, 0, -1, 5, -2, 4]
    assert merge_sort(arr) == [-3, -2, -1, 0, 4, 5]

def test_merge_sort_list_with_mixed_numbers():
    arr = [0, -5, 10, -2, 7, -1, 3]
    assert merge_sort(arr) == [-5, -2, -1, 0, 3, 7, 10]

def test_merge_sort_list_with_floats():
    arr = [3.1, 1.2, 4.5, 2.3]
    assert merge_sort(arr) == [1.2, 2.3, 3.1, 4.5]

def test_merge_sort_large_list():
    arr = [9, 2, 5, 1, 7, 6, 8, 3, 4, 0, 10, -1, 11, -2, 12]
    expected = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    assert merge_sort(arr) == expected

def test_merge_sort_list_all_equal_elements():
    arr = [7, 7, 7, 7, 7]
    assert merge_sort(arr) == [7, 7, 7, 7, 7]

def test_merge_sort_original_list_is_unchanged():
    original_arr = [3, 1, 4, 1, 5, 9, 2, 6]
    arr_copy = list(original_arr)
    merge_sort(arr_copy) # call on a copy to ensure immutability is handled by the return value
    assert original_arr == [3, 1, 4, 1, 5, 9, 2, 6]
    # Also explicitly check the function does not modify the input list
    arr_test = [3, 1, 4]
    _ = merge_sort(arr_test)
    assert arr_test == [3, 1, 4] # `merge_sort` returns a new list, does not modify `arr_test`