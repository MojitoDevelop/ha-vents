"""Short descriptions keyed by A21 manual V55-8EN-03 alarm numbers.

Codes 46–52 are present in the Modbus map but are not described in that
edition of the controller manual. Preserve those codes without guessing.
"""

ALARM_DESCRIPTIONS = (
    ("Supply fan fault", "Usterka wentylatora nawiewu"),
    ("Extract fan fault", "Usterka wentylatora wywiewu"),
    ("Outdoor temperature sensor missing", "Brak czujnika temperatury czerpni"),
    ("Outdoor temperature sensor shorted", "Zwarcie czujnika temperatury czerpni"),
    ("Supply temperature sensor missing", "Brak czujnika temperatury nawiewu"),
    ("Supply temperature sensor shorted", "Zwarcie czujnika temperatury nawiewu"),
    ("Extract temperature sensor missing", "Brak czujnika temperatury wywiewu"),
    ("Extract temperature sensor shorted", "Zwarcie czujnika temperatury wywiewu"),
    ("Exhaust temperature sensor missing", "Brak czujnika temperatury wyrzutni"),
    ("Exhaust temperature sensor shorted", "Zwarcie czujnika temperatury wyrzutni"),
    ("Preheater thermostat trip", "Zadziałanie termostatu nagrzewnicy wstępnej"),
    ("Main heater thermostat trip", "Zadziałanie termostatu nagrzewnicy głównej"),
    (
        "Preheater frost protection failed",
        "Nieskuteczna ochrona przed mrozem przez nagrzewnicę wstępną",
    ),
    ("Main humidity sensor missing", "Brak głównego czujnika wilgotności"),
    ("Main CO2 sensor missing", "Brak głównego czujnika CO₂"),
    ("Main PM2.5 sensor missing", "Brak głównego czujnika PM2.5"),
    ("Main VOC sensor missing", "Brak głównego czujnika LZO"),
    ("External humidity sensor missing", "Brak zewnętrznego czujnika wilgotności"),
    ("External CO2 sensor missing", "Brak zewnętrznego czujnika CO₂"),
    ("External PM2.5 sensor missing", "Brak zewnętrznego czujnika PM2.5"),
    ("External VOC sensor missing", "Brak zewnętrznego czujnika LZO"),
    ("Room temperature sensor unavailable", "Brak odczytu temperatury pomieszczenia"),
    ("Heat exchanger frost risk", "Ryzyko obmarzania wymiennika"),
    ("Clock battery low", "Niskie napięcie baterii zegara"),
    ("Supply filter needs replacement", "Wymagana wymiana filtra nawiewu"),
    ("Fire alarm input triggered", "Aktywny alarm pożarowy"),
    ("Supply temperature too low", "Zbyt niska temperatura nawiewu"),
    ("Return water sensor missing", "Brak czujnika temperatury wody powrotnej"),
    ("Return water sensor shorted", "Zwarcie czujnika temperatury wody powrotnej"),
    ("Extract filter needs replacement", "Wymagana wymiana filtra wywiewu"),
    ("Water pressure absent", "Brak ciśnienia wody"),
    ("Water flow absent", "Brak przepływu wody"),
    ("Return water temperature too low", "Zbyt niska temperatura wody powrotnej"),
    (
        "Supply fan frost protection failed",
        "Nieskuteczna ochrona przed mrozem przez wentylator",
    ),
    (
        "Bypass frost protection failed",
        "Nieskuteczna ochrona przed mrozem przez bypass",
    ),
    ("Frost protection disabled", "Wyłączona ochrona przed obmarzaniem"),
    ("Main heater in manual mode", "Nagrzewnica główna w trybie ręcznym"),
    ("Cooler in manual mode", "Chłodnica w trybie ręcznym"),
    ("Bypass in manual mode", "Bypass w trybie ręcznym"),
    ("Rotor in manual mode", "Wirnik w trybie ręcznym"),
    ("Filter replacement timer expired", "Upłynął czas wymiany filtrów"),
    ("Rotor operation fault", "Nieprawidłowa praca wirnika"),
    ("Preheater in manual mode", "Nagrzewnica wstępna w trybie ręcznym"),
    ("Water warm-up timed out", "Przekroczony czas wstępnego ogrzewania wody"),
    (
        "Frost protection changed to supply fan",
        "Ochrona przed mrozem przełączona na wentylator",
    ),
    ("Fireplace mode locked", "Zablokowany tryb Kominek"),
)


def alarm_description(code: int, language: str = "en") -> str:
    if 0 <= code < len(ALARM_DESCRIPTIONS):
        return ALARM_DESCRIPTIONS[code][int(language.startswith("pl"))]
    return f"Alarm {code}"
