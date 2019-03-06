[![Requirements Status](https://requires.io/github/texastribune/walls/requirements.svg?branch=master)](https://requires.io/github/texastribune/walls/requirements/?branch=master)

# walls

This queries Salesforce for opportunity information, massages it into a nice JSON format and then stores it in S3 where it will ultimately be accessed by browsers/web app(s). 

### testing

`make test`

### run it

Configure `env` file with Salesforce anw AWS variables.

`make`

### License

This project is licensed under the terms of the MIT license.
