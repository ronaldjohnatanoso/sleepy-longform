# SCRIPT GENERATION

## Overview

This module requires a Title String

* Use the Title as topic from master
* open chagpt and use script1_outline and append topic
* we expect an outline json of section summaries
* the serial part is over, we now use several accounts to dispatch
    for parallel section generation
* we concat all sections into 1 json

## Workflow

The main entry point is the main
It runs a profile worker
this profile worker accepts a function that will
define how it navigates and works on a page
get_outline is for navigating chatgpt
you should get a outline.json
use this to dispatch the workers and get individual sections
