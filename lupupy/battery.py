"""Battery flags from current device rows; never infer charge percentages."""

from collections import namedtuple

BatterySnapshot = namedtuple("BatterySnapshot", "updated_at states")
LOW_BATTERY = "{WEB_MSG_LOW_BATTERY}"


def _flag(value, allow_bool=False):
    if allow_bool and type(value) is bool:
        return int(value)
    if type(value) is int and value in (0, 1):
        return value
    if isinstance(value, str) and value in ("0", "1"):
        return int(value)
    return None


def has_battery_information(row):
    faults = row.get("faults")
    return (
        "battery_ok" in row
        or "battery" in row
        or isinstance(faults, dict)
        and "low_battery" in faults
    )


def battery_low_value(row):
    """Combine explicit modern and legacy flags; absent flags are not normal.

    Empty display text is neutral. A known low-battery token is positive
    evidence. Conflicting or malformed sources make the result unknown.
    """
    values = []
    if "battery_ok" in row:
        flag = _flag(row["battery_ok"])
        if flag is None:
            return None
        values.append(flag == 0)
    if "battery" in row:
        if row["battery"] == LOW_BATTERY:
            values.append(True)
        elif row["battery"] != "":
            return None
    if "faults" in row:
        faults = row["faults"]
        if not isinstance(faults, dict):
            return None
        if "low_battery" in faults:
            flag = _flag(faults["low_battery"], allow_bool=True)
            if flag is None:
                return None
            values.append(bool(flag))
    if not values or any(value != values[0] for value in values):
        return None
    return values[0]


def battery_state_from_snapshot(row):
    """Require usable connectivity information for an available HA state."""
    value = battery_low_value(row)
    if value is None or "{WEB_MSG_OOO}" in str(row.get("cond", "")):
        return None
    connected = False
    if "cond_ok" in row:
        if _flag(row["cond_ok"]) != 1:
            return None
        connected = True
    faults = row.get("faults")
    if isinstance(faults, dict):
        for key in ("no_response", "out_of_order"):
            if key in faults and _flag(faults[key], allow_bool=True) != 0:
                return None
        if all(key in faults for key in ("no_response", "out_of_order")):
            connected = True
    return value if connected else None
