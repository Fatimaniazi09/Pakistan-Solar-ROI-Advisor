% ========== SOLAR ADVISOR ENGINE - SIMPLIFIED WORKING VERSION ==========

% ========== DIRECT CALCULATION (NO COMPLEX PREDICATES) ==========

% Main predicate - call this directly
calculate_solar(City, MonthlyBill, TargetPercent, SystemKW, PanelsNeeded, PanelBrand, InverterSize, BatteryAH, TotalCost, PaybackYears) :-
    % Calculate units from bill (simplified)
    (   MonthlyBill =< 625 -> Units = MonthlyBill / 12.50
    ;   MonthlyBill =< 1535 -> Units = 50 + (MonthlyBill - 625) / 18.20
    ;   MonthlyBill =< 4185 -> Units = 100 + (MonthlyBill - 1535) / 26.50
    ;   MonthlyBill =< 7465 -> Units = 200 + (MonthlyBill - 4185) / 32.80
    ;   MonthlyBill =< 11715 -> Units = 300 + (MonthlyBill - 7465) / 42.50
    ;   MonthlyBill =< 16605 -> Units = 400 + (MonthlyBill - 11715) / 48.90
    ;   MonthlyBill =< 22135 -> Units = 500 + (MonthlyBill - 16605) / 55.30
    ;   MonthlyBill =< 28010 -> Units = 600 + (MonthlyBill - 22135) / 58.60
    ;   Units = 700 + (MonthlyBill - 28010) / 62.70
    ),
    
    % Daily kWh
    DailyKwh is Units / 30,
    
    % Target daily generation
    TargetDailyKwh is DailyKwh * (TargetPercent / 100),
    
    % Get peak sun hours based on city
    (   City = 'Karachi' -> SunHours = 5.5
    ;   City = 'Lahore' -> SunHours = 5.0
    ;   City = 'Islamabad' -> SunHours = 4.5
    ;   City = 'Rawalpindi' -> SunHours = 4.5
    ;   City = 'Peshawar' -> SunHours = 5.0
    ;   City = 'Quetta' -> SunHours = 6.0
    ;   City = 'Multan' -> SunHours = 5.5
    ;   SunHours = 5.0
    ),
    
    % Calculate system size (with 80% efficiency)
    RawSystemKW is (TargetDailyKwh / SunHours) / 0.80,
    
    % Round to nearest 0.5
    RawSystemKW2 is RawSystemKW * 2,
    round(RawSystemKW2, Rounded),
    SystemKW is Rounded / 2,
    
    % Temperature factor based on city
    (   City = 'Karachi' -> Temp = 34
    ;   City = 'Lahore' -> Temp = 40
    ;   City = 'Islamabad' -> Temp = 36
    ;   City = 'Rawalpindi' -> Temp = 36
    ;   City = 'Peshawar' -> Temp = 38
    ;   City = 'Quetta' -> Temp = 32
    ;   City = 'Multan' -> Temp = 42
    ;   Temp = 36
    ),
    
    (   Temp =< 32 -> TempFactor = 1.00
    ;   Temp =< 36 -> TempFactor = 0.95
    ;   Temp =< 40 -> TempFactor = 0.90
    ;   TempFactor = 0.85
    ),
    
    AdjustedSystemKW is SystemKW / TempFactor,
    
    % Panel calculation (550W panels)
    PanelWatts = 550,
    PanelPrice = 22000,  % Trina 550W price
    
    PanelsNeededTemp is (AdjustedSystemKW * 1000) / PanelWatts,
    PanelsNeeded is integer(ceil(PanelsNeededTemp)),
    
    % Panel brand selection
    (   PanelsNeeded > 0 -> PanelBrand = 'Trina 550W'
    ;   PanelBrand = 'Trina 550W'
    ),
    
    % Panel cost
    PanelTotalCost is PanelsNeeded * PanelPrice,
    
    % Inverter size based on system KW
    (   SystemKW =< 3 -> InverterSize = 3, InverterCost = 50000
    ;   SystemKW =< 5 -> InverterSize = 5, InverterCost = 85000
    ;   SystemKW =< 8 -> InverterSize = 8, InverterCost = 140000
    ;   SystemKW =< 10 -> InverterSize = 10, InverterCost = 180000
    ;   InverterSize = 15, InverterCost = 265000
    ),
    
    % Load shedding hours based on city
    (   City = 'Karachi' -> ShedHours = 2
    ;   City = 'Lahore' -> ShedHours = 4
    ;   City = 'Islamabad' -> ShedHours = 2
    ;   City = 'Rawalpindi' -> ShedHours = 3
    ;   City = 'Peshawar' -> ShedHours = 8
    ;   City = 'Quetta' -> ShedHours = 10
    ;   City = 'Multan' -> ShedHours = 6
    ;   ShedHours = 4
    ),
    
    % Battery sizing
    RequiredBatteryKwh is (TargetDailyKwh / 24) * ShedHours * 1.2,
    RequiredBatteryAh is ceil(RequiredBatteryKwh * 1000 / 12),
    
    (   RequiredBatteryAh =< 150 -> BatteryAH = 150, BatteryCost = 36000
    ;   RequiredBatteryAh =< 180 -> BatteryAH = 180, BatteryCost = 43000
    ;   RequiredBatteryAh =< 200 -> BatteryAH = 200, BatteryCost = 45000
    ;   BatteryAH = 250, BatteryCost = 55000
    ),
    
    % Installation and other costs
    InstallationCost is PanelTotalCost * 0.15,
    BalanceCost is PanelTotalCost * 0.10,
    
    % Total cost
    TotalCost is PanelTotalCost + InverterCost + BatteryCost + InstallationCost + BalanceCost,
    
    % Payback period
    MonthlySavings is MonthlyBill * (TargetPercent / 100),
    PaybackYears is TotalCost / (MonthlySavings * 12).