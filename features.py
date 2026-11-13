import ipaddress

# --- Sous-feature 1 : lire et valider les IPs ---------------------------------


def parse_ips(values=None, file=None):
    """Lit des IPs depuis une liste de chaînes et/ou un fichier (une IP par ligne).

    Retourne un tuple (ips, invalides) :
      - ips : liste triée, sans doublons, d'objets IPv4Address ou IPv6Address
      - invalides : liste des chaînes rejetées
    Lève ValueError si aucune IP valide, ou si IPv4 et IPv6 sont mélangées
    (impossible de les mettre dans un même sous-réseau).
    """
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

    if not ips:
        raise ValueError("Aucune IP valide fournie")
    if len({ip.version for ip in ips}) > 1:
        raise ValueError("Impossible de mélanger IPv4 et IPv6 dans un même groupe")

    return sorted(ips), invalid


# --- Sous-feature 3 : croiser avec les plages AWS -----------------------------


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
