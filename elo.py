import math

def probability(rating1, rating2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))

def EloRating(Ra, Rb, K, d):
    # To calculate the Winning
    # Probability of Player B
    Pb = probability(Ra, Rb)
    # To calculate the Winning
    # Probability of Player A
    Pa = probability(Rb, Ra)
    # Case -1 When Player A wins
    # Updating the Elo Ratings
    if (d == 1):
        Ra = Ra + K * (1 - Pa)
        Rb = Rb + K * (0 - Pb)
    # Case -2 When Player B wins
    # Updating the Elo Ratings
    elif (d == 0):
        Ra = Ra + K * (0 - Pa)
        Rb = Rb + K * (1 - Pb)
    # Case -3 When Player A and Player B ties
    else:
        Ra = Ra + K * (0.5 - Pa)
        Rb = Rb + K * (0.5 - Pb)
    return Ra, Rb