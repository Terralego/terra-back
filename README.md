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

### Build Container
`docker-compose build`

### Running the project
`docker-compose up`

`docker-compose down`

`docker-compose up` (postgres image)

### Running tests

`docker-compose exec django bash`

`django@container_id:/code$ source venv/bin/activate`

`(venv) django@353cfc271a48:/code$ tox` (global)

`(venv) django@353cfc271a48:/code$ tox terracommon.terra` (pour terra)

### Applying Django migrations
`docker-compose run --rm django /code/venv/bin/python3.6 ./manage.py migrate`
