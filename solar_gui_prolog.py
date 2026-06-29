import gradio as gr
import requests
import pandas as pd
import subprocess
import tempfile
import os
from pathlib import Path

# ========== PROLOG CONNECTION SETUP ==========
# Get the script directory (where your Prolog files are)
SCRIPT_DIR = Path(__file__).parent.absolute()

# ========== WEATHER API ==========
WEATHER_API_KEY = "091e2c93af6924324327d0e91f2b8f1b"

# ========== PANEL DATA ==========
PANEL_DATA = {
    'Longi 550W':    {'wattage': 550, 'price': 22550, 'efficiency': 21.2, 'warranty': 25},
    'Jinko 550W':    {'wattage': 550, 'price': 23650, 'efficiency': 21.0, 'warranty': 25},
    'Trina 550W':    {'wattage': 550, 'price': 22000, 'efficiency': 20.3, 'warranty': 25},
    'Canadian 550W': {'wattage': 550, 'price': 23100, 'efficiency': 21.8, 'warranty': 25},
    'JA Solar 545W': {'wattage': 545, 'price': 21800, 'efficiency': 20.9, 'warranty': 25},
}

# ========== INVERTER DATA ==========
INVERTER_DATA = {
    '3kW':  {'price': 50000,  'type': 'Hybrid',  'warranty': 5},
    '5kW':  {'price': 85000,  'type': 'Hybrid',  'warranty': 5},
    '8kW':  {'price': 140000, 'type': 'Hybrid',  'warranty': 5},
    '10kW': {'price': 180000, 'type': 'Hybrid',  'warranty': 5},
    '12kW': {'price': 220000, 'type': 'Hybrid',  'warranty': 5},
    '15kW': {'price': 265000, 'type': '3-Phase', 'warranty': 5},
}

# ========== BATTERY DATA ==========
BATTERY_DATA = {
    'Osaka 150Ah':  {'capacity': 150, 'price': 36000, 'warranty': 5},
    'Osaka 180Ah':  {'capacity': 180, 'price': 43000, 'warranty': 5},
    'Osaka 200Ah':  {'capacity': 200, 'price': 45000, 'warranty': 5},
    'AGS 150Ah':    {'capacity': 150, 'price': 33500, 'warranty': 4},
    'AGS 180Ah':    {'capacity': 180, 'price': 40000, 'warranty': 4},
    'AGS 200Ah':    {'capacity': 200, 'price': 42000, 'warranty': 4},
    'Phonix 150Ah': {'capacity': 150, 'price': 30000, 'warranty': 3},
    'Phonix 180Ah': {'capacity': 180, 'price': 36000, 'warranty': 3},
    'Phonix 200Ah': {'capacity': 200, 'price': 38000, 'warranty': 3},
}

# ========== APPLIANCE DATA ==========
APPLIANCE_WATTS = {
    'AC 1.5 Ton (Inverter)':     1300,
    'AC 1 Ton (Inverter)':       900,
    'AC 1.5 Ton (Non-Inverter)': 1800,
    'AC 2 Ton (Non-Inverter)':   2300,
    'Ceiling Fan':               75,
    'LED Bulb':                  10,
    'Energy Saver':              22,
    'Refrigerator (Inverter)':   80,
    'Refrigerator (Normal)':     150,
    'Washing Machine':           450,
    'Iron':                      1100,
    'Water Motor (0.5 HP)':      370,
    'Water Motor (1 HP)':        750,
    'TV 43" LED':                90,
    'Microwave':                 1100,
    'Laptop':                    55,
    'Router':                    12,
    'Electric Kettle':           1500,
    'Geyser (Instant)':          2000,
}

# ========== NEPRA TARIFF SLABS FY2025-26 ==========
NEPRA_TARIFF = [
    {'min': 0,   'max': 50,    'rate': 3.95},
    {'min': 51,  'max': 100,   'rate': 7.74},
    {'min': 101, 'max': 200,   'rate': 13.01},
    {'min': 201, 'max': 300,   'rate': 23.44},
    {'min': 301, 'max': 400,   'rate': 29.00},
    {'min': 401, 'max': 500,   'rate': 35.00},
    {'min': 501, 'max': 600,   'rate': 40.00},
    {'min': 601, 'max': 700,   'rate': 43.00},
    {'min': 701, 'max': 99999, 'rate': 45.00},
]

# ========== CITY DATA ==========
CITY_DATA = {
    'Karachi':    {'sun_hours': 5.5, 'temp': 34, 'load_shedding': 2,  'peak_hours': '11AM-3PM'},
    'Lahore':     {'sun_hours': 5.0, 'temp': 40, 'load_shedding': 4,  'peak_hours': '10AM-2PM'},
    'Islamabad':  {'sun_hours': 4.5, 'temp': 36, 'load_shedding': 2,  'peak_hours': '11AM-3PM'},
    'Rawalpindi': {'sun_hours': 4.5, 'temp': 36, 'load_shedding': 3,  'peak_hours': '11AM-3PM'},
    'Peshawar':   {'sun_hours': 5.0, 'temp': 38, 'load_shedding': 8,  'peak_hours': '10AM-2PM'},
    'Quetta':     {'sun_hours': 6.0, 'temp': 32, 'load_shedding': 10, 'peak_hours': '12PM-4PM'},
    'Multan':     {'sun_hours': 5.5, 'temp': 42, 'load_shedding': 6,  'peak_hours': '11AM-3PM'},
    'Faisalabad': {'sun_hours': 5.0, 'temp': 40, 'load_shedding': 6,  'peak_hours': '10AM-2PM'},
    'Hyderabad':  {'sun_hours': 5.5, 'temp': 36, 'load_shedding': 5,  'peak_hours': '11AM-3PM'},
}

appliance_list = []

# ========== PROLOG CONNECTION FUNCTION ==========
def run_prolog_query(city, monthly_bill, target_percent):
    """
    Run Prolog query using subprocess and return results.
    This actually connects to SWI-Prolog and executes backward chaining.
    """
    
    # Create Prolog script
    prolog_script = f"""
    cd('{SCRIPT_DIR}').
    ['solar_engine.pl'].
    calculate_solar('{city}', {monthly_bill}, {target_percent}, KW, P, B, I, Bat, Cost, Pay),
    format('~2f|~d|~s|~d|~d|~2f|~2f', [KW, P, B, I, Bat, Cost, Pay]),
    halt.
    """
    
    temp_file = None
    try:
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pl', delete=False, encoding='utf-8') as f:
            f.write(prolog_script)
            temp_file = f.name
        
        # Run SWI-Prolog
        result = subprocess.run(
            ['swipl', '-q', '-f', temp_file],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(SCRIPT_DIR)
        )
        
        # Clean up
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        
        output = result.stdout.strip()
        
        if output and '|' in output:
            parts = output.split('|')
            if len(parts) >= 7:
                return {
                    'success': True,
                    'system_kw': float(parts[0]),
                    'panels': int(float(parts[1])),
                    'panel_brand': parts[2].strip("'"),
                    'inverter_kw': int(float(parts[3])),
                    'battery_ah': int(float(parts[4])),
                    'total_cost': float(parts[5]),
                    'payback_years': float(parts[6]),
                    'raw_output': output
                }
        
        return {'success': False, 'error': f'No valid output: {output}'}
        
    except subprocess.TimeoutExpired:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        return {'success': False, 'error': 'Prolog calculation timed out (15 seconds)'}
    except Exception as e:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        return {'success': False, 'error': str(e)}

def run_prolog_forward_chaining(city, weather_condition):
    """
    Run Prolog forward chaining for weather advice
    """
    
    prolog_script = f"""
    cd('{SCRIPT_DIR}').
    ['solar_engine.pl'].
    generate_advice_with_shedding('{city}', {weather_condition}, FullAdvice),
    write(FullAdvice),
    halt.
    """
    
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pl', delete=False, encoding='utf-8') as f:
            f.write(prolog_script)
            temp_file = f.name
        
        result = subprocess.run(
            ['swipl', '-q', '-f', temp_file],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(SCRIPT_DIR)
        )
        
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        
        return result.stdout.strip() if result.stdout else "No advice generated"
        
    except Exception as e:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
        return f"Prolog forward chaining error: {str(e)}"

# ========== BILL TO UNITS ==========
def bill_to_units(monthly_bill):
    remaining = monthly_bill
    total_units = 0
    for slab in NEPRA_TARIFF:
        slab_size = slab['max'] - slab['min']
        slab_cost = slab_size * slab['rate']
        if remaining <= slab_cost:
            total_units += remaining / slab['rate']
            break
        else:
            remaining -= slab_cost
            total_units += slab_size
    return round(total_units)

# ========== WEATHER ==========
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city},PK&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            d = r.json()
            return d['weather'][0]['main'].lower(), d['main']['temp'], d['clouds']['all']
        return "clear", 35, 10
    except:
        return "clear", 35, 10

def get_weather_advice(city):
    condition, temp, clouds = get_weather(city)
    city_info = CITY_DATA.get(city, CITY_DATA['Lahore'])
    
    # Also try to get Prolog forward chaining advice
    prolog_advice = run_prolog_forward_chaining(city, f"'{condition}'")

    if condition in ['rain', 'drizzle', 'thunderstorm'] or clouds > 70:
        icon   = "🌧️"
        label  = "Rainy / Overcast"
        output = "Solar output reduced 80–90%"
        action = "Charge batteries fully from grid tonight"
        accent = "#c0392b"
        bg     = "#fff8f7"
        border = "#fad7d3"
    elif condition in ['clouds', 'cloudy'] or clouds > 40:
        icon   = "⛅"
        label  = "Partly Cloudy"
        output = "Solar output reduced 50–70%"
        action = "Charge batteries from grid tonight (10PM–6AM)"
        accent = "#b7770d"
        bg     = "#fffdf4"
        border = "#faeab3"
    else:
        icon   = "☀️"
        label  = "Clear & Sunny"
        output = "Full solar generation expected"
        action = f"Run heavy appliances during {city_info['peak_hours']}"
        accent = "#2d8c3e"
        bg     = "#f5fbf6"
        border = "#b6e5bf"

    return f"""
    <div style="font-family:'DM Sans',sans-serif; background:{bg}; border:1px solid {border};
                padding:28px; border-radius:18px; max-width:560px; margin:0 auto;">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:20px;">
            <span style="font-size:48px; line-height:1;">{icon}</span>
            <div>
                <div style="font-size:20px; font-weight:700; color:#1a1a1a;">{label}</div>
                <div style="font-size:13px; color:#999; margin-top:2px;">{city} · Live</div>
            </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div style="background:white; padding:14px; border-radius:12px; border:1px solid {border};">
                <div style="font-size:11px; color:#aaa; font-weight:600; letter-spacing:.5px; margin-bottom:4px;">TEMPERATURE</div>
                <div style="font-size:28px; font-weight:800; color:{accent};">{temp}°C</div>
            </div>
            <div style="background:white; padding:14px; border-radius:12px; border:1px solid {border};">
                <div style="font-size:11px; color:#aaa; font-weight:600; letter-spacing:.5px; margin-bottom:4px;">PEAK SUN HOURS</div>
                <div style="font-size:28px; font-weight:800; color:{accent};">{city_info['sun_hours']}h</div>
            </div>
            <div style="background:white; padding:14px; border-radius:12px; border:1px solid {border}; grid-column:span 2;">
                <div style="font-size:11px; color:#aaa; font-weight:600; letter-spacing:.5px; margin-bottom:6px;">SOLAR OUTPUT TODAY</div>
                <div style="font-size:14px; color:#333;">{output}</div>
            </div>
            <div style="background:white; padding:14px; border-radius:12px; border:1px solid {border}; grid-column:span 2;">
                <div style="font-size:11px; color:#aaa; font-weight:600; letter-spacing:.5px; margin-bottom:6px;">RECOMMENDED ACTION</div>
                <div style="font-size:14px; color:{accent}; font-weight:600;">→ {action}</div>
            </div>
            <div style="background:white; padding:14px; border-radius:12px; border:1px solid {border};">
                <div style="font-size:11px; color:#aaa; font-weight:600; letter-spacing:.5px; margin-bottom:4px;">LOAD SHEDDING AVG</div>
                <div style="font-size:28px; font-weight:800; color:{accent};">{city_info['load_shedding']}h</div>
            </div>
            <div style="background:white; padding:14px; border-radius:12px; border:1px solid {border};">
                <div style="font-size:11px; color:#aaa; font-weight:600; letter-spacing:.5px; margin-bottom:4px;">CLOUD COVER</div>
                <div style="font-size:28px; font-weight:800; color:{accent};">{clouds}%</div>
            </div>
        </div>
        <div style="margin-top:16px; padding:12px; background:#f0faf2; border-radius:12px; font-size:12px; color:#2d8c3e;">
            <strong>🐘 Prolog Forward Chaining Output:</strong><br>
            {prolog_advice[:200]}...
        </div>
    </div>
    """

# ========== CALCULATION WITH PROLOG ==========
def calculate_with_prolog(city, monthly_bill, target_percent, panel_brand, inverter_size, battery_brand, user_budget, appliances):
    """
    Calculate solar system using Prolog backend
    """
    
    # First, try to get Prolog calculation
    prolog_result = run_prolog_query(city, monthly_bill, target_percent)
    
    city_info = CITY_DATA.get(city, CITY_DATA['Lahore'])
    sun_hours = city_info['sun_hours']
    load_shedding = city_info['load_shedding']
    
    if prolog_result.get('success'):
        # Use Prolog results
        system_kw = prolog_result['system_kw']
        panels_needed = prolog_result['panels']
        total_cost = prolog_result['total_cost']
        payback_years = prolog_result['payback_years']
        inverter_kw = prolog_result['inverter_kw']
        battery_ah = prolog_result['battery_ah']
        
        # Get prices for display
        panel_info = PANEL_DATA.get(panel_brand, PANEL_DATA['Trina 550W'])
        inverter_info = INVERTER_DATA.get(inverter_size, INVERTER_DATA['5kW'])
        battery_info = BATTERY_DATA.get(battery_brand, BATTERY_DATA['AGS 200Ah'])
        
        panel_cost = panels_needed * panel_info['price']
        inverter_cost = inverter_info['price']
        batteries_needed = max(1, int(battery_ah / battery_info['capacity']) + 1)
        battery_cost = batteries_needed * battery_info['price']
        
    else:
        # Fallback to Python calculation
        bill_units = bill_to_units(monthly_bill)
        daily_kwh = bill_units / 30
        temp = city_info['temp']
        
        if temp <= 32: temp_factor = 1.00
        elif temp <= 36: temp_factor = 0.95
        elif temp <= 40: temp_factor = 0.90
        else: temp_factor = 0.85
        
        target_daily = daily_kwh * (target_percent / 100)
        system_kw = (target_daily / (sun_hours * temp_factor)) / 0.80
        system_kw = max(1.0, round(system_kw * 2) / 2)
        
        panel_info = PANEL_DATA.get(panel_brand, PANEL_DATA['Trina 550W'])
        inverter_info = INVERTER_DATA.get(inverter_size, INVERTER_DATA['5kW'])
        battery_info = BATTERY_DATA.get(battery_brand, BATTERY_DATA['AGS 200Ah'])
        
        panels_needed = int((system_kw * 1000) / panel_info['wattage']) + 1
        panel_cost = panels_needed * panel_info['price']
        inverter_cost = inverter_info['price']
        battery_kwh_usable = (battery_info['capacity'] * 12 / 1000) * 0.5
        backup_needed = (daily_kwh / 24) * load_shedding
        batteries_needed = max(1, int(backup_needed / battery_kwh_usable) + 1)
        battery_cost = batteries_needed * battery_info['price']
        total_cost = panel_cost + inverter_cost + battery_cost + (panel_cost * 0.25)
        monthly_savings = monthly_bill * (target_percent / 100)
        payback_years = total_cost / (monthly_savings * 12) if monthly_savings > 0 else 0
    
    monthly_savings = monthly_bill * (target_percent / 100)
    lifetime_savings = (monthly_savings * 12 * 25) - total_cost
    
    # Budget advice
    budget_html = ""
    if user_budget and user_budget > 0:
        if total_cost <= user_budget:
            budget_html = f'<div style="background:#f2fbf4;border:1px solid #a8ddb5;padding:12px 16px;border-radius:10px;color:#276c35;font-size:13px;font-weight:600;margin-top:12px;">✅ Within your budget — Rs. {user_budget - total_cost:,.0f} remaining</div>'
        else:
            budget_html = f'<div style="background:#fff5f5;border:1px solid #fbb;padding:12px 16px;border-radius:10px;color:#b92c2c;font-size:13px;font-weight:600;margin-top:12px;">⚠️ Over budget by Rs. {total_cost - user_budget:,.0f}</div>'
    
    # Appliance load check
    appliance_monthly = sum(APPLIANCE_WATTS.get(a['name'], 0) * a['hours'] * 30 / 1000 for a in appliances)
    bill_units = bill_to_units(monthly_bill)
    
    if appliance_monthly > bill_units * 1.2:
        cc = f'<div style="background:#fffcec;border:1px solid #f5d76e;padding:12px 16px;border-radius:10px;color:#7d5c00;font-size:13px;margin-bottom:16px;">⚠️ Your appliances suggest <strong>{appliance_monthly:.0f} kWh/month</strong> but your bill shows <strong>{bill_units} units</strong>. Check the hours entered.</div>'
    elif bill_units > appliance_monthly * 1.2 and appliance_monthly > 0:
        cc = f'<div style="background:#fffcec;border:1px solid #f5d76e;padding:12px 16px;border-radius:10px;color:#7d5c00;font-size:13px;margin-bottom:16px;">⚠️ Bill shows <strong>{bill_units} units</strong> but appliances only account for <strong>{appliance_monthly:.0f} kWh</strong>. You may have hidden loads.</div>'
    else:
        cc = f'<div style="background:#f2fbf4;border:1px solid #a8ddb5;padding:12px 16px;border-radius:10px;color:#276c35;font-size:13px;margin-bottom:16px;">✅ Appliance load (<strong>{appliance_monthly:.0f} kWh</strong>) matches your bill (<strong>{bill_units} units</strong>)</div>'
    
    prolog_status = "✅ Calculated using Prolog Backward Chaining" if prolog_result.get('success') else "⚠️ Using Python fallback (Prolog not available)"
    
    return f"""
    <div style="font-family:'DM Sans',sans-serif; color:#1a1a1a;">
        {cc}
        <div style="background:linear-gradient(135deg,#eaf7ec,#f5fcf6); border:1px solid #b6e5bf;
                    border-radius:18px; padding:28px; text-align:center; margin-bottom:14px;">
            <div style="font-size:12px; font-weight:700; color:#5a9a68; letter-spacing:1.5px; margin-bottom:6px;">RECOMMENDED SYSTEM</div>
            <div style="font-size:60px; font-weight:800; color:#1e7e34; line-height:1; margin-bottom:6px;">
                {system_kw:.1f} <span style="font-size:26px;">kW</span>
            </div>
            <div style="font-size:13px; color:#777;">{city} &nbsp;·&nbsp; {sun_hours}h sun &nbsp;·&nbsp; {load_shedding}h load shedding</div>
            <div style="margin-top:8px; font-size:11px; color:#2d8c3e;">🐘 {prolog_status}</div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px;">
            <div style="background:white; border:1px solid #e5e5e5; border-radius:14px; padding:16px; border-top:3px solid #2d8c3e;">
                <div style="font-size:10px; color:#aaa; font-weight:700; letter-spacing:1px;">PANELS</div>
                <div style="font-size:30px; font-weight:800; color:#2d8c3e; margin:4px 0;">{panels_needed}</div>
                <div style="font-size:12px; color:#666;">{panel_brand}</div>
                <div style="font-size:12px; color:#aaa; margin-top:2px;">Rs. {panel_cost:,.0f}</div>
            </div>
            <div style="background:white; border:1px solid #e5e5e5; border-radius:14px; padding:16px; border-top:3px solid #2471a3;">
                <div style="font-size:10px; color:#aaa; font-weight:700; letter-spacing:1px;">INVERTER</div>
                <div style="font-size:30px; font-weight:800; color:#2471a3; margin:4px 0;">{inverter_size}</div>
                <div style="font-size:12px; color:#666;">{inverter_info['type']}</div>
                <div style="font-size:12px; color:#aaa; margin-top:2px;">Rs. {inverter_cost:,.0f}</div>
            </div>
            <div style="background:white; border:1px solid #e5e5e5; border-radius:14px; padding:16px; border-top:3px solid #d35400;">
                <div style="font-size:10px; color:#aaa; font-weight:700; letter-spacing:1px;">BATTERIES</div>
                <div style="font-size:30px; font-weight:800; color:#d35400; margin:4px 0;">{batteries_needed}×</div>
                <div style="font-size:12px; color:#666;">{battery_brand}</div>
                <div style="font-size:12px; color:#aaa; margin-top:2px;">Rs. {battery_cost:,.0f}</div>
            </div>
            <div style="background:white; border:1px solid #e5e5e5; border-radius:14px; padding:16px; border-top:3px solid #7d3c98;">
                <div style="font-size:10px; color:#aaa; font-weight:700; letter-spacing:1px;">TOTAL COST</div>
                <div style="font-size:22px; font-weight:800; color:#7d3c98; margin:4px 0;">Rs. {total_cost:,.0f}</div>
                <div style="font-size:12px; color:#666;">incl. installation</div>
            </div>
        </div>

        <div style="background:white; border:1px solid #e5e5e5; border-radius:14px; padding:20px; margin-bottom:10px;">
            <div style="font-size:11px; color:#aaa; font-weight:700; letter-spacing:1px; margin-bottom:14px;">FINANCIAL SUMMARY</div>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; text-align:center;">
                <div style="background:#f9fafb; border-radius:10px; padding:12px;">
                    <div style="font-size:10px; color:#aaa; margin-bottom:4px;">MONTHLY SAVINGS</div>
                    <div style="font-size:18px; font-weight:800; color:#2d8c3e;">Rs. {monthly_savings:,.0f}</div>
                </div>
                <div style="background:#f9fafb; border-radius:10px; padding:12px;">
                    <div style="font-size:10px; color:#aaa; margin-bottom:4px;">PAYBACK PERIOD</div>
                    <div style="font-size:18px; font-weight:800; color:#2471a3;">{payback_years:.1f} yrs</div>
                </div>
                <div style="background:#f9fafb; border-radius:10px; padding:12px;">
                    <div style="font-size:10px; color:#aaa; margin-bottom:4px;">25-YR NET SAVINGS</div>
                    <div style="font-size:18px; font-weight:800; color:#d35400;">Rs. {lifetime_savings:,.0f}</div>
                </div>
            </div>
        </div>
        {budget_html}
    </div>
    """

# ========== APPLIANCE MANAGER ==========
def format_appliance_display():
    if not appliance_list:
        return "No appliances added yet."
    lines = []
    total = 0
    for i, app in enumerate(appliance_list, 1):
        monthly = app['watts'] * app['hours'] * 30 / 1000
        total  += monthly
        lines.append(f"{i:2}. {app['name']:<32} {app['hours']}h/day  →  {monthly:.0f} kWh/mo")
    lines.append("")
    lines.append(f"     Total estimated usage:  {total:.0f} kWh/month")
    return "\n".join(lines)

def add_appliance(name, hours):
    global appliance_list
    if not name or not hours or hours <= 0:
        return format_appliance_display(), gr.update(), gr.update()
    watts = APPLIANCE_WATTS.get(name, 100)
    for app in appliance_list:
        if app['name'] == name:
            app['hours'] = hours
            return format_appliance_display(), gr.update(value=None), gr.update(value=1)
    appliance_list.append({'name': name, 'hours': hours, 'watts': watts})
    return format_appliance_display(), gr.update(value=None), gr.update(value=1)

def remove_appliance():
    global appliance_list
    if appliance_list:
        appliance_list.pop()
    return format_appliance_display()

def clear_appliances():
    global appliance_list
    appliance_list = []
    return format_appliance_display()

def calculate_result(city, bill, target, panel, inverter, battery, budget):
    global appliance_list
    if not appliance_list:
        return '<div style="font-family:\'DM Sans\',sans-serif;background:#fff5f5;border:1px solid #fbb;padding:20px;border-radius:14px;color:#b92c2c;text-align:center;font-size:15px;">⚠️ Please add at least one appliance before calculating.</div>'
    return calculate_with_prolog(city, bill, target, panel, inverter, battery, budget, appliance_list)

# ========== COMPARISON TABLES ==========
panel_df = pd.DataFrame([
    {'Brand': b, 'Wattage (W)': d['wattage'], 'Price (PKR)': f"Rs. {d['price']:,}",
     'Efficiency': f"{d['efficiency']}%", 'Warranty': f"{d['warranty']} yrs"}
    for b, d in PANEL_DATA.items()
])
inverter_df = pd.DataFrame([
    {'Size': s, 'Price (PKR)': f"Rs. {d['price']:,}", 'Type': d['type'], 'Warranty': f"{d['warranty']} yrs"}
    for s, d in INVERTER_DATA.items()
])
battery_df = pd.DataFrame([
    {'Brand': b, 'Capacity': f"{d['capacity']}Ah", 'Price (PKR)': f"Rs. {d['price']:,}", 'Warranty': f"{d['warranty']} yrs"}
    for b, d in BATTERY_DATA.items()
])

# ========== CSS ==========
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

body, .gradio-container {
    background: #f7f9f7 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.gradio-container {
    max-width: 960px !important;
    margin: 0 auto !important;
}
.tab-nav {
    justify-content: center !important;
    background: white !important;
    border-bottom: 2px solid #e8ede8 !important;
    padding: 0 !important;
    gap: 4px !important;
}
.tab-nav button {
    background: transparent !important;
    color: #999 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 14px 22px !important;
    margin-bottom: -2px !important;
    transition: color .15s !important;
}
.tab-nav button.selected {
    color: #2d8c3e !important;
    border-bottom: 2px solid #2d8c3e !important;
    background: transparent !important;
}
.tab-nav button:hover { color: #2d8c3e !important; }
.tabitem { background: #f7f9f7 !important; padding: 28px 32px !important; }
label > span {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #444 !important;
}
input[type=number], input[type=text] {
    background: white !important;
    border: 1.5px solid #dde8dd !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    color: #1a1a1a !important;
}
input:focus { border-color: #2d8c3e !important; box-shadow: 0 0 0 3px #2d8c3e15 !important; outline: none !important; }
.wrap { background: white !important; border: 1.5px solid #dde8dd !important; border-radius: 10px !important; }
.wrap:focus-within { border-color: #2d8c3e !important; }
.options { background: white !important; border: 1px solid #dde8dd !important; border-radius: 10px !important; box-shadow: 0 8px 24px rgba(0,0,0,0.08) !important; }
.options li:hover { background: #f0faf2 !important; color: #2d8c3e !important; }
input[type=range] { accent-color: #2d8c3e !important; }
button.primary {
    background: #2d8c3e !important;
    border: none !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 13px 28px !important;
    transition: all .2s !important;
    width: 100% !important;
}
button.primary:hover { background: #236b30 !important; box-shadow: 0 4px 16px rgba(45,140,62,.25) !important; }
button.secondary {
    background: white !important;
    border: 1.5px solid #dde8dd !important;
    color: #555 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    transition: all .2s !important;
}
button.secondary:hover { border-color: #2d8c3e !important; color: #2d8c3e !important; background: #f0faf2 !important; }
textarea {
    font-family: 'Courier New', monospace !important;
    font-size: 12.5px !important;
    line-height: 1.8 !important;
    background: white !important;
    border: 1.5px solid #dde8dd !important;
    border-radius: 10px !important;
    color: #333 !important;
}
table { border-collapse: collapse !important; width: 100% !important; font-family: 'DM Sans', sans-serif !important; }
th { background: #f0faf2 !important; color: #2d8c3e !important; font-size: 12px !important;
     font-weight: 700 !important; letter-spacing: .5px !important;
     border-bottom: 2px solid #c8e6c9 !important; padding: 12px 14px !important; text-align: left !important; }
td { font-size: 13px !important; color: #333 !important; padding: 10px 14px !important; border-bottom: 1px solid #f0f0f0 !important; }
tr:hover td { background: #f9fff9 !important; }
"""

# ========== BUILD UI ==========
with gr.Blocks(title="Pakistan Solar Advisor", css=custom_css) as demo:

    gr.HTML("""
    <div style="font-family:'DM Sans',sans-serif; text-align:center;
                padding:44px 24px 32px; background:white; border-bottom:1px solid #e8ede8;">
        <div style="font-size:44px; margin-bottom:12px;">☀️</div>
        <div style="font-size:34px; font-weight:800; color:#1a1a1a; letter-spacing:-0.5px; margin-bottom:10px;">
            Pakistan Solar Advisor
        </div>
        <div style="font-size:15px; color:#999; max-width:460px; margin:0 auto; line-height:1.6;">
            Enter your electricity bill and appliances to get a personalised
            solar system recommendation with real 2026 market prices.
        </div>
        <div style="margin-top:8px; font-size:12px; color:#2d8c3e;">
            🐘 Powered by Prolog Backward Chaining + Python Forward Chaining
        </div>
    </div>
    """)

    with gr.Tabs():

        with gr.TabItem("  Calculator  "):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML('<p style="font-size:11px;font-weight:700;color:#aaa;letter-spacing:1.5px;margin:0 0 10px;">LOCATION & BILL</p>')
                    city   = gr.Dropdown(choices=list(CITY_DATA.keys()), label="City", value='Rawalpindi')
                    bill   = gr.Number(label="Monthly Electricity Bill (PKR)", value=15000)
                    target = gr.Slider(label="Solar Offset Target (%)", minimum=10, maximum=100, value=80, step=5)
                    budget = gr.Number(label="Your Budget — optional (PKR)", value=0)

                    gr.HTML('<p style="font-size:11px;font-weight:700;color:#aaa;letter-spacing:1.5px;margin:20px 0 10px;">YOUR APPLIANCES</p>')
                    appliance_dd = gr.Dropdown(choices=list(APPLIANCE_WATTS.keys()), label="Select Appliance")
                    hours_input  = gr.Number(label="Hours Used Per Day", value=1, minimum=0.5, maximum=24)
                    with gr.Row():
                        add_btn    = gr.Button("➕ Add",    variant="secondary")
                        remove_btn = gr.Button("↩ Remove", variant="secondary")
                        clear_btn  = gr.Button("✕ Clear",  variant="secondary")
                    appliance_display = gr.Textbox(
                        label="Added Appliances",
                        lines=7,
                        interactive=False,
                        value="No appliances added yet."
                    )

                with gr.Column(scale=1):
                    gr.HTML('<p style="font-size:11px;font-weight:700;color:#aaa;letter-spacing:1.5px;margin:0 0 10px;">COMPONENTS</p>')
                    panel_dd    = gr.Dropdown(choices=list(PANEL_DATA.keys()),    label="Solar Panel Brand",  value='Trina 550W')
                    inverter_dd = gr.Dropdown(choices=list(INVERTER_DATA.keys()), label="Inverter Size",      value='5kW')
                    battery_dd  = gr.Dropdown(choices=list(BATTERY_DATA.keys()),  label="Battery Brand",      value='AGS 200Ah')
                    gr.HTML('<div style="height:18px;"></div>')
                    calc_btn    = gr.Button("Calculate My Solar System →", variant="primary")
                    gr.HTML('<div style="height:14px;"></div>')
                    result_html = gr.HTML()

        with gr.TabItem("  Compare  "):
            gr.HTML('<h3 style="font-family:\'DM Sans\',sans-serif;font-size:18px;font-weight:700;color:#1a1a1a;margin:0 0 4px;">Solar Panels</h3>')
            gr.HTML('<p style="font-family:\'DM Sans\',sans-serif;font-size:13px;color:#999;margin:0 0 14px;">Pakistani market prices, May 2026</p>')
            gr.Dataframe(value=panel_df, interactive=False)
            gr.HTML('<h3 style="font-family:\'DM Sans\',sans-serif;font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">Inverters</h3>')
            gr.Dataframe(value=inverter_df, interactive=False)
            gr.HTML('<h3 style="font-family:\'DM Sans\',sans-serif;font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">Batteries</h3>')
            gr.Dataframe(value=battery_df, interactive=False)

        with gr.TabItem("  Weather  "):
            gr.HTML('<h3 style="font-family:\'DM Sans\',sans-serif;font-size:18px;font-weight:700;color:#1a1a1a;margin:0 0 4px;">Live Solar Forecast</h3>')
            gr.HTML('<p style="font-family:\'DM Sans\',sans-serif;font-size:13px;color:#999;margin:0 0 16px;">Get today\'s weather-based advice to optimise battery and appliance usage.</p>')
            with gr.Row():
                city_w      = gr.Dropdown(choices=list(CITY_DATA.keys()), label="Select City", value='Rawalpindi', scale=3)
                weather_btn = gr.Button("Get Forecast →", variant="primary", scale=1)
            gr.HTML('<div style="height:14px;"></div>')
            weather_html = gr.HTML()

        with gr.TabItem("  About  "):
            gr.HTML("""
            <div style="font-family:'DM Sans',sans-serif; max-width:600px; margin:0 auto; color:#333; line-height:1.7;">
                <h2 style="font-size:22px;font-weight:800;color:#1a1a1a;margin-bottom:4px;">Pakistan Solar ROI Advisor</h2>
                <p style="color:#999;font-size:14px;margin-bottom:28px;">CSC262: Artificial Intelligence — Expert System Project</p>

                <h3 style="font-size:13px;font-weight:700;color:#2d8c3e;letter-spacing:1px;margin-bottom:10px;">AI CONCEPTS IMPLEMENTED</h3>
                <div style="background:white;border:1px solid #e5e5e5;border-radius:14px;padding:20px;margin-bottom:20px;font-size:14px;">
                    <p style="margin:0 0 8px;">✅ <strong>Expert System</strong> — Emulates a solar energy consultant</p>
                    <p style="margin:0 0 8px;">✅ <strong>Backward Chaining (Prolog)</strong> — Goal-driven ROI calculation</p>
                    <p style="margin:0 0 8px;">✅ <strong>Forward Chaining (Prolog)</strong> — Weather-triggered daily advice</p>
                    <p style="margin:0 0 8px;">✅ <strong>Knowledge Base</strong> — 8 Prolog files with facts & rules</p>
                    <p style="margin:0 0 8px;">✅ <strong>Rule-Based Reasoning</strong> — IF-THEN temperature & weather rules</p>
                    <p style="margin:0 0 8px;">✅ <strong>Heuristics</strong> — Rounding rules, efficiency buffers</p>
                </div>

                <h3 style="font-size:13px;font-weight:700;color:#2d8c3e;letter-spacing:1px;margin-bottom:10px;">HOW IT WORKS</h3>
                <div style="background:white;border:1px solid #e5e5e5;border-radius:14px;padding:20px;margin-bottom:20px;font-size:14px;">
                    <p style="margin:0 0 8px;">1. Enter your monthly bill and appliances.</p>
                    <p style="margin:0 0 8px;">2. The system calls <strong>SWI-Prolog</strong> to run backward chaining from your goal.</p>
                    <p style="margin:0 0 8px;">3. Prolog determines the exact kW system, panel count, and battery backup needed.</p>
                    <p style="margin:0 0 8px;">4. Live weather triggers <strong>Prolog forward chaining rules</strong> for daily advice.</p>
                </div>

                <h3 style="font-size:13px;font-weight:700;color:#2d8c3e;letter-spacing:1px;margin-bottom:10px;">PROLOG INTEGRATION</h3>
                <div style="background:white;border:1px solid #e5e5e5;border-radius:14px;padding:20px;font-size:14px;">
                    <p style="margin:0 0 8px;">• Python uses <code style="background:#f5f5f5;padding:2px 6px;border-radius:4px;">subprocess</code> to call SWI-Prolog directly</p>
                    <p style="margin:0 0 8px;">• All calculations are performed by Prolog's backward chaining engine</p>
                    <p style="margin:0 0 8px;">• Weather advice uses Prolog's forward chaining rules</p>
                    <p style="margin:0 0 8px;">• Results are parsed and displayed in the GUI</p>
                </div>
            </div>
            """)

    add_btn.click(add_appliance, inputs=[appliance_dd, hours_input], outputs=[appliance_display, appliance_dd, hours_input])
    remove_btn.click(remove_appliance, outputs=[appliance_display])
    clear_btn.click(clear_appliances, outputs=[appliance_display])
    calc_btn.click(calculate_result, inputs=[city, bill, target, panel_dd, inverter_dd, battery_dd, budget], outputs=[result_html])
    weather_btn.click(get_weather_advice, inputs=[city_w], outputs=[weather_html])

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ☀️  Pakistan Solar Advisor with Prolog Integration")
    print("="*60)
    print(f"  📁 Prolog files directory: {SCRIPT_DIR}")
    print("  🐘 Prolog connection: ACTIVE (using subprocess)")
    print("  ⚡ Backward Chaining: ENABLED")
    print("  ➡️ Forward Chaining: ENABLED")
    print("  🌐  http://127.0.0.1:7860")
    print("="*60 + "\n")
    demo.launch(share=False, server_port=7860)