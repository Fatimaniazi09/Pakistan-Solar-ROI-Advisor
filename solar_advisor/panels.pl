% panel(Brand, Wattage, PricePKR, PricePerWatt).
% Using your formula: price = wattage * price_per_watt
panel('Longi 550W', 550, 22550, 41).    % 550 * 41
panel('Jinko 550W', 550, 23650, 43).    % 550 * 43
panel('Trina 550W', 550, 22000, 40).    % 550 * 40
panel('Canadian 550W', 550, 23100, 42). % 550 * 42

% panel_price(Brand, Price)
panel_price(Brand, Price) :-
    panel(Brand, _, Price, _).