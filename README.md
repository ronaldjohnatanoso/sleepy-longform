# Sleepy Longform Script Automation

Run chrome_binary_dl.sh inside chrome_binary_setup folder to setup the browser binary to use

## Put a credentials.json from google sheets api service

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

## SOME TROUBLE SHOOTING

when you change profile make sure the clipboard is enabled and port does collide
