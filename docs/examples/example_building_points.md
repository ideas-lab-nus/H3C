# Example cooling-case points

The example contains one office zone.

| Variable | Description | Unit |
|---|---|---|
| `office_temperature_y` | Office-zone air temperature measurement | K |
| `office_cooling_setpoint_u` | Office-zone cooling setpoint input | K |
| `office_occupancy_y` | Office-zone occupancy forecast | people |
| `outdoor_temperature_y` | Outdoor dry-bulb forecast | K |
| `global_solar_y` | Global horizontal solar irradiation forecast | W/m2 |
| `electricity_price_y` | Electricity price forecast | currency/J |
| `cooling_power_y` | Cooling equipment electrical power | W |
| `fan_power_y` | Supply fan electrical power | W |

The two power measurements are summed for site energy accounting. The case operator,
not the Mapping Agent, owns all static controls, protocol dates, comfort parameters,
occupancy policy, and testcase selection.
