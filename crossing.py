# crossing.py
# This file checks if any target has crossed the mental line.
# It matches current targets to previous ones based on proximity and checks for crossing.

def check_crossing(current_targets, previous_targets, line_x):
    if not previous_targets:
        return False
    crossings = False
    for curr in current_targets:
        curr_center_x = curr[0] + curr[2] / 2
        curr_center_y = curr[1] + curr[3] / 2
        min_dist = float('inf')
        prev_center_x = None
        prev_center_y = None
        for prev in previous_targets:
            p_center_x = prev[0] + prev[2] / 2
            p_center_y = prev[1] + prev[3] / 2
            dist = ((curr_center_x - p_center_x) ** 2 + (curr_center_y - p_center_y) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                prev_center_x = p_center_x
                prev_center_y = p_center_y
        # Assume targets move from left to right; adjust inequality if direction is opposite
        if prev_center_x and prev_center_x < line_x <= curr_center_x:
            crossings = True
    return crossings
