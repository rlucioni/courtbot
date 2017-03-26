def conversational_join(items, conjunction='and'):
    """
    Join the given items so they can be used in a sentence.
    """
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f' {conjunction} '.join(items)
    else:
        all_but_last = ', '.join(items[:-1])
        last = items[-1]
        return f', {conjunction} '.join([all_but_last, last])
