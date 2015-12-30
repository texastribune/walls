[![Code Issues](https://www.quantifiedcode.com/api/v1/project/6ace56537d544b3cba66e6731d715b9e/badge.svg)](https://www.quantifiedcode.com/app/project/6ace56537d544b3cba66e6731d715b9e)

# walls

This queries Salesforce for opportunity information. Massages it into a nice JSON format and then stores it in S3 where it will ultimately be access by browsers/web app(s). 

### testing

`make test`

### run it

Configure `env` file with Salesforce anw AWS variables.

`make`
