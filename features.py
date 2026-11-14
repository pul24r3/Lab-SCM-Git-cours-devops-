import ipaddress
import argparse
import json
from awsip import download_aws_ip_set, find_aws_ip

#Sous-feature 1 : lire et valider les IPs

def parse_ips(values=None, file=None):

    """Lit des IPs depuis une liste de chaînes et/ou un fichier (une IP par ligne)."""
   
    raw = list(values or [])
    if file:
        with open(file, encoding="utf-8") as f:
            raw += [line.strip() for line in f]

    ips, invalid = set(), []
    for item in raw:
        if not item or item.startswith("#"):  # lignes vides / commentaires
            continue
        try:
            ips.add(ipaddress.ip_address(item))
        except ValueError:
            invalid.append(item)

    """ValueError si impossible de les mettre dans un même sous-réseau """
    if not ips:
        raise ValueError("Aucune IP valide fournie")
    if len({ip.version for ip in ips}) > 1:
        raise ValueError("Impossible de mélanger IPv4 et IPv6 dans un même groupe")

    return sorted(ips), invalid


#Sous-feature 2 : calculer le plus petit sous-réseau commun 

def smallest_subnet(ips):
    """ Calcul le plus petit sous-réseau contenant toutes les adresses ip fournit """

    if not ips:
        raise ValueError("La liste d'addresses IP ne peut pas être vide.")

    ip_objects = [ipaddress.ip_address(ip) for ip in ips]

    versions = {ip.version for ip in ip_objects}

    if len(versions) > 1:
        raise ValueError("On ne peut pas mélanger IPv4 et IPv6.")

    lo = min(ip_objects)
    hi = max(ip_objects)

    host_bits = (int(lo) ^ int(hi)).bit_length()
    prefix = lo.max_prefixlen - host_bits

    return ipaddress.ip_network((lo, prefix), strict=False)


# Sous-feature 3 : croiser avec les plages AWS 


def aws_coverage(network, aws_prefixes):
    """Indique si `network` est couvert par les plages AWS.

    `aws_prefixes` : la liste renvoyée par download_aws_ip_set()
    (dicts avec 'ip_prefix' ou 'ipv6_prefix', 'region', 'service').

    Retourne un dict :
      {"status": "totale" | "partielle" | "aucune",
       "matches": [{"prefix", "region", "service", "type"}, ...]}
    """
    network = ipaddress.ip_network(network, strict=False)
    matches = []
    for entry in aws_prefixes:
        cidr = entry.get("ip_prefix") or entry.get("ipv6_prefix")
        prefix = ipaddress.ip_network(cidr)
        if prefix.version != network.version:  # subnet_of() refuse de mélanger v4/v6
            continue
        if network.subnet_of(prefix):
            kind = "totale"
        elif network.overlaps(prefix):
            kind = "partielle"
        else:
            continue
        matches.append(
            {
                "prefix": cidr,
                "region": entry.get("region"),
                "service": entry.get("service"),
                "type": kind,
            }
        )

    if any(m["type"] == "totale" for m in matches):
        status = "totale"
    elif matches:
        status = "partielle"
    else:
        status = "aucune"
    return {"status": status, "matches": matches}


# Sous-feature 4 


def run_check(ip):
    result = find_aws_ip(download_aws_ip_set(), ip)
    print(json.dumps(result, indent=2))


def run_group(ips_raw=None, file=None):
    """
    Analyse un groupe d'adresse IP
    """
    try:
        ips, invalid = parse_ips(ips_raw, file)

        network = smallest_subnet(ips)

        aws_prefixes = download_aws_ip_set()

        coverage = aws_coverage(network, aws_prefixes)

        print("\n========== GROUP IP ANALYSIS ==========")
        print(f"IPs analysées       : {len(ips)}")

        if invalid:
            print(f"Invalides IPs ignorées: {len(invalid)}")

        print(f"Plus petit réseau    : {network}")
        print(f"Capacité du réseau   : {network.num_addresses} addresses")
        print(f"AWS coverage       : {coverage['status']}")

        for match in coverage["matches"]:
            print(
                f" - {match['service']} / {match['region']} "
                f"({match['prefix']}) : {match['type']}"
            )

    except (ValueError, OSError) as error:
        print(f"Error: {error}")


def interactive_menu():
    """
    Afficher un menu interractif pour chhoisir le mode 
    """

    print("\n========== AWS IP ANALYZER ==========")
    print("1. Check a single IP address")
    print("2. Analyze a group of IP addresses")

    choice = input("\nYour choice: ").strip()

    if choice == "1":
        ip = input("Enter an IP address: ").strip()
        run_check(ip)

    elif choice == "2":
        values = input(
            "Enter IP addresses separated by spaces: "
        ).split()

        run_group(values)

    else:
        print("Invalid choice.")


def main():

    parser = argparse.ArgumentParser(
        description="AWS IP Address Analyzer"
    )

    subparsers = parser.add_subparsers(
        dest="mode"
    )

    # Mode classique
    check_parser = subparsers.add_parser(
        "check",
        help="Check a single IP address"
    )

    check_parser.add_argument("ip")

    # Mode analyse de groupe
    group_parser = subparsers.add_parser(
        "group",
        help="Analyze a group of IP addresses"
    )

    group_parser.add_argument(
        "ips",
        nargs="*",
        help="IP addresses to analyze"
    )

    group_parser.add_argument(
        "--file",
        help="File containing IP addresses"
    )

    args = parser.parse_args()

    if args.mode == "check":
        run_check(args.ip)

    elif args.mode == "group":
        run_group(args.ips, args.file)

    else:
        interactive_menu()


if __name__ == "__main__":
    main()