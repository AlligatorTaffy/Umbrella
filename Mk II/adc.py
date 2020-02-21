from gpiozero import MCP3008
from time import sleep 
wind_sensor = MCP3008(1)
current_sensor = MCP3008(2)
voltage_sensor = MCP3008(3)
adc_correction = 0.0004885197850512668
wind_adc_offset = 0.30566875122 
current_adc_offset = 0
voltage_adc_offset = 0.2789188909
five_three_offset = 0.6467878
twenty_two_offset = 0.0897043833
hall_offset = 2.445761379890371

while True:
    print("RAW values: ", (wind_sensor.value - adc_correction), (current_sensor.value - adc_correction), (voltage_sensor.value - adc_correction))
    #5V offset and Divider correction
    # Wind Speed Sensor results
    corrected = ((wind_sensor.value - adc_correction) / wind_adc_offset) / five_three_offset # Offset
    wind = (corrected / 5) * 45  # Calculation of measure to meters/second
    wind = wind * 2.237 # Conversion of meters/second to MPH
    print("Wind Speed: ","%.3f" % wind, "MPH")
    # Current Sensor results
    corrected = ((current_sensor.value - adc_correction) / wind_adc_offset) #/ five_three_offset # ADC offset
    print(corrected)
    amps = corrected / five_three_offset
    amps = amps - 2.53
    amps = amps / 0.1
    print("Motor Current: ","%.3f" % amps, "A")
    # Battery Voltage results
    #20v offset and Divider correction
    corrected = ((voltage_sensor.value - adc_correction) / voltage_adc_offset) / twenty_two_offset # ADC offset
    print("System Voltage: ","%.3f" % corrected,"V")
    sleep(1)

"""counter = 0
sum = 0
while counter < 60:
    counter = counter + 1
    current = voltage_sensor.value - adc_correction
    #current = current / 0.6467878
    print(counter, current)
    sum = sum + current
    sleep(1)

print("avg", sum / counter)"""
