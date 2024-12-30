def string_hours(hours: int):
    if hours % 10 == 0 or 10 < hours % 100 < 20 or hours % 10 >= 5:
        return str(hours) + " часов"
    if hours % 10 == 1:
        return str(hours) + " час"
    return str(hours) + " часа"


def string_minutes(minutes: int, *, u: bool = False):
    if minutes % 10 == 0 or 10 < minutes % 100 < 20 or minutes % 10 >= 5:
        return str(minutes) + " минут"
    if minutes % 10 == 1:
        return str(minutes) + (" минуту" if u else " минута")
    return str(minutes) + " минуты"


def string_seconds(seconds: int, *, u: bool = False):
    if seconds % 10 == 0 or 10 < seconds % 100 < 20 or seconds % 10 >= 5:
        return str(seconds) + " секунд"
    if seconds % 10 == 1:
        return str(seconds) + (" секунду" if u else " секунда")
    return str(seconds) + " секунды"


def string_timedelta(seconds: int, *, skip: int = 1, u: bool = False) -> str:
    result = [
        string_hours(seconds // 3600),
        string_minutes((seconds % 3600) // 60, u=u),
        string_seconds(seconds % 60, u=u),
    ]

    result = [x for x in result[:len(result) - skip] if not x.startswith("0")]
    if not result:
        result = ["меньше минуты"]
    return " ".join(result)
