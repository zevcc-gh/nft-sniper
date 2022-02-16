# NFT sniper : Find the rariest NFT

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)

[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


Basic Commands
--------------
### Local Test
- Start the env
  
      $ docker-compose -f local.yml up

- DB Migration (only need to run one time)
- 
      $ docker-compose -f local.yml run --rm django python manage.py makemigrations
      $ docker-compose -f local.yml run --rm django python manage.py migrate

- Fetch NFT and rank!
    - Must provided: **uri**, **number_of_nfts**
    - Optional : **workers** (controlling how many threads)
    - E.g
  
          $ docker-compose -f local.yml run --rm django python manage.py fetch_nfts --uri https://nft-api.avgle.com/a/ --number_of_nfts=10000
