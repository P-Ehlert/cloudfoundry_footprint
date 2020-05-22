<h1>Cloud Foundry Footprint</h1> 

Python script that estimates the carbon footprint of all Cloud Foundry (CF) applications of an organization.
The script uses basic 'cf cli' commands to count the number of running containers per space. This is then multiplied by
an estimated average energy consumption.

IBM reported that on average their CF servers use 400 Watt and that a single cloud server can support 30-100 containers
depending on the container size. Here we simply assume 65 (100+30/2) containers per server. The footprint of services
(databases, redis, etc.) is ignored because 1) we have no power consumption information of that and 2) it will
probably be much less that the consumption of all containers.

The script assumes you are logged into Cloud Foundry already. Alternatively you can use the login_cf function to do that

For more information about cf cli see https://docs.cloudfoundry.org/cf-cli/install-go-cli.html
For more information about carbon intensity of electricity see https://en.wikipedia.org/wiki/Emission_intensity

Usage:

    cf_footprint.py [-h] [-y] [-c CARBON] [-s SPACE] [-v]

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
     