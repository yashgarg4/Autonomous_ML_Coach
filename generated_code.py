"""An implementation of the merge sort algorithm."""

def merge_sort(arr):
    """Sorts a list using the merge sort algorithm.

    Args:
        arr: The list to be sorted.

    Returns:
        A new list containing the sorted elements.
    """ # Closing triple quotes for the docstring
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left_half = arr[:mid]
    right_half = arr[mid:]

    left_half = merge_sort(left_half)
    right_half = merge_sort(right_half)

    return merge(left_half, right_half)

def merge(left, right):
    """Merges two sorted lists into a single sorted list.

    Args:
        left: The first sorted list.
        right: The second sorted list.

    Returns:
        A new sorted list containing all elements from both input lists.
    """ # Closing triple quotes for the docstring
    merged_list = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            merged_list.append(left[i])
            i += 1
        else:
            merged_list.append(right[j])
            j += 1

    while i < len(left):
        merged_list.append(left[i])
        i += 1
    while j < len(right):
        merged_list.append(right[j])
        j += 1

    return merged_list