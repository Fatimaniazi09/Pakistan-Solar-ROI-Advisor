% city_data(City, PeakSunHours, AvgTempSummer).
city_data('Karachi', 5.5, 34).
city_data('Lahore', 5.0, 40).
city_data('Islamabad', 4.5, 36).
city_data('Peshawar', 5.0, 38).
city_data('Quetta', 6.0, 32).
city_data('Multan', 5.5, 42).
city_data('Faisalabad', 5.0, 40).
city_data('Hyderabad', 5.5, 36).
city_data('Rawalpindi', 4.5, 36).

% temperature_derating(TempCategory, Factor).
% (From your TEMP_DERATING dict)
temp_derating('cool', 1.00).
temp_derating('normal', 0.90).
temp_derating('hot', 0.85).
temp_derating('extreme', 0.80).

% get_temperature_factor(City, Factor)
get_temperature_factor(City, Factor) :-
    city_data(City, _, Temp),
    (   Temp =< 32 -> Factor = 1.00
    ;   Temp =< 36 -> Factor = 0.90
    ;   Temp =< 40 -> Factor = 0.85
    ;   Factor = 0.80
    ).