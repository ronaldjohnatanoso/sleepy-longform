# Sleepy Longform Script Automation

1. get the structured script from chatgpt
    - the vid is so long that we cant just get the script in one prompt
    - we have to automate scraping it
    - we need to inject the img prompts timing too (lets make the img/effect embedding dynamic for later use)

Challenges:
    - how should we structure the script to include the img prompts

## Google Sheets

Name a sheet 'Google Accounts'

- This stores prepared google account for parallel use
- Accounts there should only be put after they have been manually prepared and zip with their according identifier in the zip/folder

## Prepare the Topic Titles (TODO, we do manual adding of title in the sheets)

- We can generate some titles and put it in sheets named 'Titles'
- You could also just directly access the sheet and add your own entry
- In the pipeline, we retrieve a title here in different method (random, order)
- There should also be an option for a custom on the spot title in the creation that doesn't use this

## Load an Available Title or Pick your own
