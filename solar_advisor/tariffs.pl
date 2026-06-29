% tariff(MinUnits, MaxUnits, RatePerUnit).
% NEPRA FY2025-26 (including all charges - verified)
tariff(0,   50,  12.50).
tariff(51,  100, 18.20).
tariff(101, 200, 26.50).
tariff(201, 300, 32.80).
tariff(301, 400, 42.50).
tariff(401, 500, 48.90).
tariff(501, 600, 55.30).
tariff(601, 700, 58.60).
tariff(701, 100000, 62.70).  % Above 700 units

% net_metering_rate (export rate - from your data)
net_metering_rate(21).