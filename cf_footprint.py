#!/usr/bin/python
"""
Python script that estimates the carbon footprint of all Cloud Foundry (CF) applications of an organization.
The script uses basic cf cli commands to count the number of running containers per space. This is then multiplied by
an estimated average energy consumption.

IBM reported that on average their CF servers use 400 Watt and that a single cloud server can support 30-100 containers
depending on the container size. Here we simply assume 65 (100+30/2) containers per server. The footprint of services
(databases, redis, etc.) is ignored because 1) we have no power consumption information of that and 2) it will
probably be much less that the consumption of all containers.

At the moment the number of services in each space is counted, but this is not included in the carbon footprint
calculations as we don't know anything about the exact impact.

The script assumes you are logged into Cloud Foundry already using CF CLI v6.x. Alternatively you can use the
login_cf function to do that.

For more information about cf cli see https://docs.cloudfoundry.org/cf-cli/install-go-cli.html
For more information about carbon intensity of electricity see https://en.wikipedia.org/wiki/Emission_intensity
"""

import argparse, os, re

# Constants
WATT_PER_SERVER = 400
INSTANCES_PER_SERVER = 65
HOURS_PER_YEAR = 365.25 * 24
TOTAL = "TOTAL"

# Global variables
verbose = False


def login_cf(cf_api, cf_user, cf_pwd, cf_org, cf_space):
    """
    Login to Cloud Foundry
    :param cf_api: string, CF API endpoint
    :param cf_user: string, CF user name
    :param cf_pwd: string, CF user password
    :param cf_org: string, CF organization
    :param cf_space: string, CF space to log into
    :raises: RuntimeError when the expected output is not found
    """
    if verbose: print("Logging into {} as user {}...".format(cf_api, cf_user), end='')
    login = "cf login -a {}, -u {}, -p {}, -o {}, -s {}".format(cf_api, cf_user, cf_pwd, cf_org, cf_space)
    login_output = os.popen(login).read
    if "API endpoint:" in login_output:
        if verbose: print("ok")
    else:
        raise RuntimeError("Error logging into Cloud Foundry:", login_output)


def get_cf_spaces():
    """
    Read all available Cloud Foundry spaces
    :return: list of all CF spaces
    :raises: RuntimeError when the expected output (header line) is not found
    """
    if verbose: print("Retrieving spaces...", end='')
    spaces_output = os.popen("cf spaces").read()
    if ("name\n" in spaces_output):
        spaces = spaces_output.split("name\n",1)[1].splitlines()
        if verbose:
            print("ok")
            print("Found {} spaces: {}".format(str(len(spaces)), spaces))
        return spaces
    else:
        raise RuntimeError("Error retrieving Cloud Foundry spaces:", spaces_output)


def switch_to_cf_space(space):
    """
    Switch to a particular Cloud Foundry space
    :param space: string, the CF space to switch to
    :raises: RuntimeError when the expected output is not found
    """
    if verbose: print("Switching to space {}...".format(space), end='')
    switch_output = os.popen("cf target -s " + space).read()
    if ("API endpoint" in switch_output):
        if verbose: print("ok")
    else:
        raise RuntimeError("Error switching to space:", switch_output)


def get_active_instances():
    """
    Get the active instances/containers in the current CF space
    :return: integer, number of active app instances in the current CF space
    :raises: RuntimeError when the expected output is not found
    """
    instances = 0
    if verbose: print("Retrieving applications data...", end='')
    apps_output = os.popen("cf apps").read().splitlines()
    if ("No apps found" in apps_output):
        if verbose:
            print("ok")
            print("No apps found")
        return 0
    elif apps_output[2].startswith("name"):
        # iterate over lines and find applications that are 'started'
        if verbose: print("ok");
        for line in list(apps_output):
            match_obj = re.search(r"\sstarted\s*web:([0-9]?[0-9])/[0-9]?[0-9]", line)
            if match_obj:
                instances += int(match_obj.group(1))

        if verbose: print("Found {} active instances ".format(instances))
        return instances
    else:
        raise RuntimeError("Error retrieving applications data", apps_output)

def get_services():
    """
    Get the services in the current CF space
    :return: integer, number of services the current CF space
    :raises: RuntimeError when the expected output is not found
    """
    services = 0
    if verbose: print("Retrieving applications services...", end='')
    services_output = os.popen("cf services").read().splitlines()
    if ("No services found" in services_output):
        if verbose: print("Found 0 services")
        return 0;
    if verbose: print("ok");
    for svs in services_output:
        if svs:
            services +=1
    # each line is a service, but we should substract 2 for the header lines
    services = services - 2
    if verbose: print("Found {} services".format(services))
    return services


def calculate_footprint(active_instances):
    """
    Calculates current energy consumption
    :param active_instances: integer, the number of active server instances/containers
    :return: float, current energy consumption of all active CF instances (in Watt)
    """
    return (active_instances/ INSTANCES_PER_SERVER) * WATT_PER_SERVER


def calculate_footprint_per_year(active_instances):
    """
    Given the number of instances, calculates how much kWh per year they will consume (if they keep running all year)
    :param active_instances: integer, the number of active server instances/containers
    :return: float, energy consumption per year of all active CF instances (in kWh/year)
    """
    return calculate_footprint(active_instances) * HOURS_PER_YEAR / 1000


def calculate_carbon_footprint_per_year(active_instances, carbon_intensity):
    """
    Given the number of instances and the carbon intensity of the local energy mix used by the server(s),
    calculates the carbon footprint per year (if they keep running all year)
    :param active_instances: integer, the number of active instances/containers
    :param carbon_intensity: integer, amount of CO2e released for producing 1 kWh
    :return: float, carbon footprint per year of all active CF instances (in kg CO2e/year)
    """
    return calculate_footprint_per_year(active_instances) * carbon_intensity / 1000


def process_arguments():
    """"
    Define and process all supported command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-y", "--year", help="estimate electricity footprint per year (in kWh/year)", action="store_true")
    parser.add_argument("-c", "--carbon", help="estimate carbon footprint per year (in kg CO2e/year). " +\
        "CARBON is the carbon intensity of the energy mix used by the servers (in gram), e.g. 600 gram CO2e/kWh. " +\
        "This option ignores -y")
    parser.add_argument("-s", "--space", help="estimate only for the provided space")
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        global verbose
        verbose = True
    return args


def print_footprint(args, name, active_instances):
    """
    Output footprint information for a particular space or for all spaces
    :param args: command-line arguments
    :param name: string, either 'TOTAL' (for all spaces) or name of a particular space
    :param active_instances: integer, number of active CF instances/containers
    """
    if (name == TOTAL):
        _name = TOTAL + ":"
    else:
        _name = "Space {}:".format(name)

    if (args.carbon):
        print("{} {} kg CO2e per year".format(_name, round(calculate_carbon_footprint_per_year(
            active_instances, int(args.carbon)))))
    elif (args.year):
        print("{} {} kWh per year".format(_name, round(calculate_footprint_per_year(active_instances))))
    else:
        print("{} {} Watt".format(_name, round(calculate_footprint(active_instances))))


def main(args):
    """
    Either get all CF spaces and calculate footprint for all active instances on those space , or switch to a particular
    space and calculate footprint for that.
    """
    total_instances = 0;
    # login_cf("https://mycf.paas.org", "username", "password","organisation", "space")
    if args.space:
        switch_to_cf_space(args.space)
        print_footprint(args, args.space, get_active_instances())
        get_services()
    else:
        spaces = get_cf_spaces()
        for space in spaces:
            switch_to_cf_space(space)
            active_instances = get_active_instances()
            total_instances += active_instances
            print_footprint(args, space, active_instances)

        print_footprint(args, TOTAL, total_instances)


if __name__ == "__main__":
    main(process_arguments())
