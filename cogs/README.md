## Details of Barrel Spam Rules

### To be updated each time the logic is changed

Barrelbot will count a run as over if any of the following conditions are met:
1. A message is sent with the wrong number
2. A message is sent without a :barrel: emoji after the number
3. A message is sent that does not match the general formatting rules
4. A message in the channel (any message, no matter how old) is edited

The number can be in either base 2 or base 10, with any number of leading zeros. The emoji can be any :barrel: emoji; as long as the emoji name contains the word "barrel," it will work.

When the run is over,
* If the run lasted long enough to get to spam number 10: 
    * Each team's total is counted up
    * Whichever team got the most points for the run "wins" and gets all of those points added to their team score
    * The "losing" team gets half of their earned points
    * If there is a tie, both teams get 3/4 of their earned points
    * The team of the person who ended the run gets a penalty of `ceil(spam number / 5)` taken from their score
    * The spam number is reset to 0
* If the run did not last long enough to get to spam number 10:
    * Each person who spammed in that run gets their points rolled back (i.e. if you spammed twice, got four points, and the run ended before 10, you would not get those points added to your total score)
    * The spam number is reset to 0

On a valid :barrel: spam,
* If your spam number is part of the following sequences of special numbers, you will gain extra points as follows:
    * Prime numbers: `ceil(spam number / 4)`
    * Mersenne prime numbers: `ceil(spam number / 1.5)`, overriding the usual prime number score
    * Fibonacci numbers, palindromic numbers, powers of two, perfect squares: `ceil(spam number / 2)`
        * Numbers can be counted as base 2 and base 10 palindromes regardless of the base they're typed in
        * Numbers are palindromic base 10 if their base 10 representation with no leading zeros is longer than 1 character and is equal to its digits in reversed order
        * Numbers are palindromic base 2 if their base 2 representation in byte format (with enough leading zeros to increase the digit length of the number to a multiple of 8) is equal to its digits in reversed order
    * Numbers fitting a modified Thue-Morse sequence: `ceil(spam number / 1.5)`
        * The modified Thue-Morse sequence contains each integer whose binary representation is the first n bits of the full Thue-Morse sequence, where n is a positive integer. 
