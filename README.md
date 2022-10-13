<h1>Cloud Foundry Footprint</h1> 

Python3 script that estimates the carbon footprint of all Cloud Foundry (CF) applications of an organization.
The script uses basic 'cf cli' commands to count the number of running containers per space. This is then multiplied by
an estimated average energy consumption.

IBM reported that on average their CF servers use 400 Watt and that a single cloud server can support 30-100 containers
depending on the container size. Here we simply assume 65 (100+30/2) containers per server. The footprint of services
(databases, redis, etc.) is ignored because 1) we have no power consumption information of that and 2) it will
probably be much less that the consumption of all containers.

At the moment the number of services in each space is counted, but this is not included in the carbon footprint
calculations as we don't know anything about the exact impact.

The script assumes you are logged into Cloud Foundry already using CF CLI v6.x (using v1.0 of this software) or CF CLI
v8.x (with v1.1). Alternatively you can use the login_cf function to do that.

- For more information about cf cli see https://docs.cloudfoundry.org/cf-cli/install-go-cli.html
- For more information about carbon intensity of electricity see https://en.wikipedia.org/wiki/Emission_intensity

Usage:

    python3 cf_footprint.py [-h] [-y] [-c CARBON] [-s SPACE] [-v]

    optional arguments:
    -h, --help            show this help message and exit
    -y, --year            estimate electricity footprint per year (in kWh/year)
    -c CARBON, --carbon CARBON
                          estimate carbon footprint per year (in kg CO2e/year).
                          CARBON is the carbon intensity of the energy mix used
                          by the servers (in gram), e.g. 600 gram CO2e/kWh. This
                          option ignores -y
    -s SPACE, --space SPACE
                          estimate only for the provided space
    -v, --verbose         verbose output

Example usage:

    cf_footprint.py -c 441 -s production

  This calculates the footprint per year of all active instances in a space called 'production', assuming the carbon
  intensity of the energy mix is 441 CO2e / kWh
     

<h2>Version history:</h2>
  - Version 1.1: supports CF CLI v8.x
  - Version 1.0: supports CF CLI v6.x
