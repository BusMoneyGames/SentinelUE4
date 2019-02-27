# SentinelUE4Component
UE4 Component for the Sentinel pipeline tool

## Client and server Build
Bulids both the client executable and the server executable and outputs them into the Sentinel Artifacts folder

pipenv run .\SentinelUE4Component.py -build -build_preset "default" "server"



## Compile Blueprints and Resave Packages
Runs two maintainance commandlets back to back and saves their output into the Sentinel Artifacts folder

pipenv run .\SentinelUE4Component.py -validate -validation_tasks "Compile-Blueprints" "Resave-Packages"

# Inspects all the packages
Runs the package inspection that checks the project infrastructure

pipenv run .\SentinelUE4Component.py -validate -validation_inspect

