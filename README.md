This is the Terra API.

## Requirements

On Ubuntu, do not use the system packages, which are too old.
* **docker-ce**: https://docs.docker.com/install/linux/docker-ce/ubuntu/
* **docker-compose**: `sudo pip3 install docker-compose`


## Usage

### First launch
Create a docker.env file:
* `mv docker.env.dist docker.env`
* Edit the settings

### Running the project
`docker-compose up`

### Applying Django migrations
`docker-compose run --rm django /code/venv/bin/python3.6 ./manage.py migrate`
