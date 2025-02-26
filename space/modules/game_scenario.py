def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 2000
    elif year < 1981:
        return 1400
    elif year < 1995:
        return 500
    elif year < 2010:
        return 250
    elif year < 2020:
        return 60
    else:
        return 20
