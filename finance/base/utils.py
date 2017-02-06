def split_list(list_, number):
    length = len(list_)
    if number > length:
        number = length
    return [list_[i * length // number:(i + 1) * length // number] for i in range(number)]
