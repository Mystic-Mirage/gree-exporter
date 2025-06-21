from prometheus_client import Gauge

GAUGE_MAP = {
    Gauge(name := f"gree_{prop}", name, ["mac"]): prop
    for prop in [
        "power",
        "mode",
        "target_temperature",
        "temperature_units",
        "current_temperature",
        "fan_speed",
        "fresh_air",
        "xfan",
        "anion",
        "sleep",
        "light",
        "horizontal_swing",
        "vertical_swing",
        "quiet",
        "turbo",
        "steady_heat",
        "power_save",
        "target_humidity",
        "dehumidifier_mode",
        "current_humidity",
        "clean_filter",
        "water_full",
    ]
}
