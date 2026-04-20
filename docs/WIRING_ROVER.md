# Relay to Rover Wiring

## Per-channel rule
- COM -> rover control pin
- NO -> Orange
- NC -> Gray

## Channel mapping
- CH1 -> Green
- CH2 -> Blue
- CH3 -> Yellow
- CH4 -> White

## Wheel behavior discovered during testing

Right wheel pair:
- Orange -> Blue and Gray -> Green = forward
- Orange -> Green and Gray -> Blue = reverse

Left wheel pair:
- same pattern using White and Yellow

## Deployed software mapping

The physical Pi-to-relay wiring is still `IN1` through `IN4` as documented, but
the final deployed rover behavior uses this command mapping after empirical
testing:

- `forward`: IN1 LOW, IN2 HIGH, IN3 HIGH, IN4 LOW
- `reverse`: IN1 HIGH, IN2 LOW, IN3 LOW, IN4 HIGH
- `left`: IN1 LOW, IN2 HIGH, IN3 LOW, IN4 HIGH
- `right`: IN1 HIGH, IN2 LOW, IN3 HIGH, IN4 LOW
- `stop`: IN1 HIGH, IN2 HIGH, IN3 HIGH, IN4 HIGH
