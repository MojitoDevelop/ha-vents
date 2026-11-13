# Vents dla Home Assistant

![Vents](custom_components/vents_a21/brand/logo.png)

Lokalna integracja Modbus TCP dla sterowników **Vents A21**, przygotowana dla mapy **VUT 400 HBE EC A21**. Konfiguracja z interfejsu HA, bez konta w chmurze.

## Instalacja HACS

1. W **HACS → ⋮ → Repozytoria niestandardowe** dodaj `https://github.com/MojitoDevelop/ha-vents`, kategoria **Integracja**.
2. Pobierz **Vents** i uruchom ponownie Home Assistant.
3. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację → Vents**.
4. Podaj IP centrali, port (zwykle `502`) i adres urządzenia Modbus (zwykle `1`).

Wymagany **Home Assistant 2026.10.0 lub nowszy**. Repozytorium można dodawać jako niestandardowe; nie oznacza to obecności w domyślnym katalogu HACS.

Instalacja ręczna: rozpakuj archiwum wydania do katalogu konfiguracji HA, tak aby powstał plik `/config/custom_components/vents_a21/manifest.json`, i uruchom ponownie HA.

## Nazwy i język

Domyślnym językiem jest angielski. Przy polskim języku systemu Home Assistant nazwy wyświetlane, stany, formularze i opisy alarmów są po polsku. **Identyfikatory encji pozostają angielskie**, np.:

- `sensor.vents_outdoor_air_temperature` — temperatura czerpni;
- `sensor.vents_supply_air_temperature` — temperatura nawiewu;
- `sensor.vents_extract_air_temperature` — temperatura wywiewu;
- `sensor.vents_exhaust_air_temperature` — temperatura wyrzutni;
- `fan.vents_ventilation` — wentylacja;
- `climate.vents_climate` — regulacja temperatury.

Przy zajętym identyfikatorze HA może dopisać `_2` itd. Ręczna zmiana nazwy encji przez użytkownika jest zachowywana przez rejestr HA.

## Funkcje

Sterowanie włączeniem, biegami i prędkością ręczną; temperatura 15–30°C w pełnych stopniach; tryby wentylacji, grzania, chłodzenia i automatyczny; bypass zależnie od typu siłownika; timer z czasem, biegiem i temperaturą; włączanie istniejącego harmonogramu tygodniowego.

Odczyty obejmują cztery temperatury powietrza i temperaturę czujnika regulacyjnego, wysterowanie obu wentylatorów, raportowany stan bypassu, pracę i sygnał nagrzewnicy, filtry, czas do wymiany, czas pracy oraz alarmy z kodami i opisami. Dostępne są przyciski resetu licznika filtrów i kasowania alarmów.

W **Konfiguruj** można włączyć encje dodatkowych czujników wilgotności, CO₂, PM2.5, LZO, przepływu, ciśnienia, obrotów i dodatkowych temperatur. Włączaj tylko zamontowane wyposażenie. Opcja HA udostępnia encje i nie aktywuje wejścia czujnika w sterowniku.

Nastawy nawiewu i wywiewu dla poszczególnych biegów są domyślnie wyłączone w rejestrze encji. Nastawy procentowe działają w trybie procentowym, a nastawy przepływu w trybie stałej wydajności.

## Migracja z obecnego YAML

Sterownik obsługuje **jedno połączenie Modbus TCP na interfejs**. Usuń dotychczasowy hub `reku` z YAML i uruchom ponownie HA przed dodaniem integracji. Zachowaj inne urządzenia Modbus. Zatrzymaj automatyzacje zapisujące do starego huba.

Nowa integracja używa własnych encji. [Tabela migracji](docs/migration.md) podaje zamienniki sensorów, helperów i bezpośrednich zapisów Modbus. Gotowa prosta karta znajduje się w [examples/dashboard.yaml](examples/dashboard.yaml). Poprzednie karty wymagają przepięcia encji i akcji według tabeli.

## Istotne zachowanie

- Przy uruchamianiu i konfiguracji wykonywane są wyłącznie odczyty. Wszystkie polecenia i odczyty korzystają z jednej kolejki. Po zapisie następuje odczyt stanu, bez automatycznego ponawiania niejednoznacznych zapisów.
- Domyślny odczyt co 10 sekund. Interwał, limit odpowiedzi i opóźnienie po połączeniu można zmienić w opcjach. Dane połączenia zmienia się przez **Zmień konfigurację**.
- Niedostępne czujniki i błędy komunikacji nie są zamieniane na zera. Po poprawnym odczycie encje wracają do działania.
- Nastawa prędkości i bypassu jest oddzielona od raportowanego wysterowania i stanu. Temperatura bieżąca termostatu pochodzi z czujnika wybranego w sterowniku do regulacji (Input 0).
- Boost i Kominek są statusami tylko do odczytu. Czasowe przewietrzanie zapewnia timer. Priorytety trybów i ochrona sterownika mogą zmienić wynik zwykłej nastawy prędkości.
- Tryb chłodzenia może wykorzystywać chłodne powietrze zewnętrzne. Nie oznacza obecności dodatkowej chłodnicy.
- Sygnał nagrzewnicy nie jest pomiarem mocy elektrycznej. Wartości powyżej 100% oznaczają dodatkową regulację wentylatorami. Integracja nie tworzy fikcyjnych pomiarów energii ani sprawności odzysku ciepła.
- Starszy firmware może nie udostępniać Input 51–53; odpowiadające im encje będą niedostępne, a podstawowe odczyty pozostaną aktywne.

## Weryfikacja

Testy uruchamiają rzeczywisty Home Assistant i klienta PyModbus przeciwko niezależnemu, lokalnemu symulatorowi TCP. Sprawdzają ramki, polecenia, skalowanie, ujemne temperatury, błędy czujników, timery, awarie komunikacji, odzyskanie połączenia i tłumaczenia.

**Pozostaje sprawdzenie na fizycznej centrali.** Wydanie powstało z dokumentacji i podanej mapy YAML, bez połączenia z urządzeniem użytkownika. Podczas uruchomienia porównaj czas timera, licznik filtrów i czas pracy z aplikacją centrali. Inne urządzenia A21 mogą obsługiwać inną część wyposażenia.

Źródła i instrukcja uruchamiania testów znajdują się w [README.md](README.md). Jest to niezależna integracja społecznościowa.
