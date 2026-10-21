# Firmware

The robot runs **grbl-Mega-5X** (<https://github.com/fra589/grbl-Mega-5X>) on an Arduino Mega 2560 with a RAMPS 1.4 shield. Each joint is one axis measured in degrees: X = J1, Y = J2, Z = J3, A = J4, B = J5.

- `grbl_settings.txt` holds the `$` settings generated from `config/robot.json`. Regenerate it after changing gear ratios, microsteps, speeds or limits:

  ```bash
  python Ravi.py grbl-settings > firmware/grbl_settings.txt
  python Ravi.py grbl-settings --port /dev/ttyACM0     # upload directly
  ```

- Build options (`config.h` changes), wiring, bring-up and calibration are in [docs/ELECTRONICS.md](../docs/ELECTRONICS.md).
