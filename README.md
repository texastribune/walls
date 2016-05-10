[![Code Issues](https://www.quantifiedcode.com/api/v1/project/6ace56537d544b3cba66e6731d715b9e/badge.svg)](https://www.quantifiedcode.com/app/project/6ace56537d544b3cba66e6731d715b9e)
[![Requirements Status](https://requires.io/github/texastribune/walls/requirements.svg?branch=master)](https://requires.io/github/texastribune/walls/requirements/?branch=master)
[![wercker status](https://app.wercker.com/status/3248476a5b668c63d8231ed2bf3b1e47/m "wercker status")](https://app.wercker.com/project/bykey/3248476a5b668c63d8231ed2bf3b1e47)

# walls

This queries Salesforce for opportunity information, massages it into a nice JSON format and then stores it in S3 where it will ultimately be accessed by browsers/web app(s). 

### testing

`make test`

### run it

Configure `env` file with Salesforce anw AWS variables.

`make`

### License

This project is licensed under the terms of the MIT license.
