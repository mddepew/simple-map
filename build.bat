cd ~%dp0
pipenv run pyinstaller simple-map.spec
pipenv run pyinstaller admin_client.py
pipenv run pyinstaller map_builder.py