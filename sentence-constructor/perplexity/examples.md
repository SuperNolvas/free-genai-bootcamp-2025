Note: Good, each state is shown by the LLM, Setup, Attempt eg. Output is poor though. If I question the output as wrong, it is ignored. Will rework prompt with a <query> input. This query addition did work for the second attempt, although the output was still poor. Free model seems to give low quality ouput for this task

## First Attempt after initial testing

### Input

Hello my name is John

State: Setup
Okay, the sentence we'll work with is: "Hello, my name is John."

Here's a vocabulary table to get you started:

| Russian      | Transliteration | English |
|-------------|----------------|---------|
| здравствуйте | zdravstvuyte   | hello   |
| имя         | imya           | name    |
| звать       | zvat'          | to call |
| я           | ya             | I       |


Here's a possible sentence structure to guide you:

Hello, I [verb: to call] name John.
Here are some things to consider:
Think about the correct form of the verb "to call" to use in this context (hint: it needs to be conjugated).
Consider the case of "name"
"Hello" has a formal and informal version. Which do you want to use?
What is the next step? Try to assemble the sentence using the words and the structure provided. Don't worry about being wrong, that is part of learning!

## Second Attempt

Output is still incorrect. Prompt revision for query did work 

<query>Is this beginner A1 level? Shouldn't the word list you provided allow for this sentence? Привет, меня зовут Джон.

### Answer
You're absolutely right, and I apologize for the oversight. You've made an excellent point, and I appreciate you bringing this to my attention. Let me correct my approach to better align with the A1 level and provide a more appropriate response.

### State: Setup (Revised)
You're correct. For an A1 level learner, we should indeed provide a simpler and more direct vocabulary list that allows for the construction of the sentence "Привет, меня зовут Джон." Thank you for pointing this out. Let's revise the information to be more suitable for a beginner level:

| Russian  | Transliteration | English |
|----------|----------------|---------|
| привет   | privet         | hello   |
| меня     | menya          | me      |
| зовут    | zovut          | call    |
