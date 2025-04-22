import random
import time

def main():
    random.seed(time.time())
    n = random.randint(1, 1000)
    print("Guess the number (1-1000): ", end="")
    while True:
        g = int(input())
        if g == n:
            print("Congratulations! You guessed the right number.")
            break
        elif g < n:
            print("Your guess is too low! Try again: ", end="")
        else:
            print("Your guess too high! Try again: ", end="")

if __name__ == "__main__":
    main()
