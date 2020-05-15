# Kumi
### Team Messaging Web Application.

Instant messaging applications have been a big part of our current social networking methods, both in social and professional settings. We designed a smart, sleek, and efficient messaging application where members can communicate in real time. Having a convenient messaging medium enables teams to communicate easily and effectively which in turn helps organizations function efficiently. We developed a web based application with the help of Materialize CSS and jQuery library for the front-end, Python - Flask as the back-end and PostgreSQL to store data.


[Live Demo - http://kumix.herokuapp.com/](http://kumix.herokuapp.com/)

## Known Issue

*Dated May 15, 2020, Mac and iPhone Safari's browser is having compatility issue that prevent web socket to properly connect using Gunicorn version 18.0.0 on Heroku server. Running test on localhost should work without this issue.*


## Getting Started

Make sure you have Python version 3.6 with pip installed on your computer to setup a localhost web server for development purpose.

More information can be found here:

[How do you set up a local testing server?]( https://developer.mozilla.org/en-US/docs/Learn/Common_questions/set_up_a_local_testing_server)

### Prerequisites

Python 3.6 with pip

Required packages: 
1.	Flask
2.	Flask-Heroku
3.	Flask-Login
4.	Flask-SQLAlchemy
5.	Flask-WTF
6.	Gunicorn (only required on Heroku)
7.	psycopg2 binary (only required on Heroku)
8.	SQLAlchemy
9. ...

See the most updated complete list [requirements.txt](https://github.com/Winternight5/Kumi/blob/master/requirements.txt)

### Installation

Clone this git repo then install the required packages. 
Use the terminal: *(For Window, make sure to “Run as administrator”)*
```
git clone git@github.com:Winternight5/Kumi.git
```

Example of installing individual package:

```
pip install Flask
```
For Mac:
```
pip3 install Flask
```
All packages listed in the requirements text file are required to run the application.


## Deployment

This repo is built with Heroku package and is ready for deployment. Please see Heroku official website for more information.
[GitHub Integration (Heroku GitHub Deploys)]( https://devcenter.heroku.com/articles/github-integration)


## Built With

* [Python](https://www.python.org/) - An interpreted, high-level, general-purpose programming language.
* [JQuery](https://www.jquery.com) - A fast, small, and feature-rich JavaScript library.
* [MaterializeCSS](https://materializecss.com/) - A modern responsive front-end framework based on Material Design.


## Authors, *Initial work*

* **Tai Huynh** - *Project Manager*
* **Daniel Saneel** - *UI/UX Engineer*
* **Tatsuya Hayashi** - *Front-End Engineer*
* **Nathaniel Wallace** - *Devops/Infrastucture Engineer*

List of [contributors]( https://github.com/Winternight5/Kumi/graphs/contributors)


## License

This project is licensed under the MIT License.
