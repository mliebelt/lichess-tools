# Claude instructions

When using the Lichess API, there will be from time to time the necessity to have an API token given. We have to find a solution that allows

* to call the scripts locally, with a defined API token as environment variable in the command line then and
* to call the scripts/tests on the Github server, when doing a build that does some tests then. Github should allow to do that as well.

## Rules

* All scripts are developed in Python, with a minimal need for additional libraries.
* All scripts should run on Linux (my computer), Windows (a lot of users) and Mac the same way.
* All scripts should have meaningful names, that are short and easy to remember.
* All scripts have to have a command line interface, that allows to
  * get information by using either `--help` or `-h` as only parameter. This will display a help text that explains how the scripts work, with enough information about each option, and some typical examples how to use them.
  * get an meaningful error message in all cases.
  * get some additional information to then define the missing `LICHESS_PAT` by the user. There is some documentation available about it here: https://github.com/lichess-org/api-demo/tree/master/example/oauth-personal-token
* Get all information about Lichess API only from the authorative resource: https://lichess.org/api Don't search anywhere else for information about the Lichess API.

## Flow of Control

* Work on ideas that are saved in Github tickets on a 1 by 1 case only.
* Create for each ticket in the folder plans a new file named `ticket-<NR>.md` where we collect how we want to develop the ticket then.
* We will work together on those files.
* When we agree on the plan, then the implementation starts done by an LLM.
* For each new feature, we want to create fitting unit tests (run locally without network access necessary, if possible) and feature tests that use the centrally available `LICHESS_PAT` of the user to test some functionality when running a build system.
* I want to run all tests locally, before I commit something, especially before I push something.
