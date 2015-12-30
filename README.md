# walls

This queries Salesforce for opportunity information. Massages it into a nice JSON format and then stores it in S3 where it will ultimately be access by browsers/web app(s). 

### testing

`make test`

### run it

Configure `env` file with Salesforce anw AWS variables.

`make`
