#!/bin/bash
git clone https://git.doit.wisc.edu/cdis/cs/courses/cs544/misc/calculator.git
cd calculator
echo "Read following code diff:" > prompt.txt
git diff main origin/fix >> prompt.txt
echo "Summarize the code changes in 1 sentence, without repeating actual lines of code." >> prompt.txt
