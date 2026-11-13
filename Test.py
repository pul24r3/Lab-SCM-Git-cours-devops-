"""Tests unitaires des fonctions de A : parse_ips et aws_coverage.

Lancer :  python -m unittest test_awsip_group_a -v
"""

import ipaddress
import os
import tempfile
import unittest

from features import aws_coverage, parse_ips

# Faux extrait de ip-ranges.json : les tests n'ont pas besoin d'Internet,
# et le résultat ne change pas quand AWS met à jour ses plages.
# Le /26 EC2 est volontairement inclus dans le /24 AMAZON (comme dans la vraie liste).
FAKE_PREFIXES = [
    {"ip_prefix": "52.95.110.0/24", "region": "eu-west-3", "service": "AMAZON"},
    {"ip_prefix": "52.95.110.0/26", "region": "eu-west-3", "service": "EC2"},
    {"ip_prefix": "3.5.140.0/22", "region": "ap-northeast-2", "service": "S3"},
]


class TestParseIps(unittest.TestCase):
    """Sous-feature 1 : lecture et validation des IPs."""

    def test_valid_sorted_dedup(self):
        # Cas nominal : 3 IPs valides dont un doublon, données dans le désordre.
        # On vérifie que le doublon est supprimé, que la liste est triée,
        # et qu'on obtient des objets ip_address (pas des chaînes).
        ips, invalid = parse_ips(["10.0.0.5", "10.0.0.1", "10.0.0.5"])
        self.assertEqual(
            ips, [ipaddress.ip_address("10.0.0.1"), ipaddress.ip_address("10.0.0.5")]
        )
        # Aucune entrée n'a été rejetée.
        self.assertEqual(invalid, [])

    def test_invalid_are_reported(self):
        # Mélange d'une IP valide et de deux entrées invalides
        # (du texte, et une IP dont un octet dépasse 255).
        # Les invalides ne doivent pas faire planter : elles sont mises de côté.
        ips, invalid = parse_ips(["10.0.0.1", "pas_une_ip", "999.1.1.1"])
        # Seule l'IP valide est gardée...
        self.assertEqual(len(ips), 1)
        # ...et les invalides sont renvoyées, dans l'ordre, pour pouvoir les afficher.
        self.assertEqual(invalid, ["pas_une_ip", "999.1.1.1"])

    def test_from_file(self):
        # Lecture depuis un fichier : on crée un fichier temporaire contenant
        # un commentaire, deux IPs et une ligne vide.
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
            f.write("# commentaire\n10.0.0.1\n\n10.0.0.2\n")
        try:
            ips, invalid = parse_ips(file=f.name)
            # Les 2 IPs sont lues...
            self.assertEqual(len(ips), 2)
            # ...et le commentaire / la ligne vide sont ignorés, pas comptés invalides.
            self.assertEqual(invalid, [])
        finally:
            # On supprime le fichier temporaire, même si le test échoue.
            os.remove(f.name)

    def test_no_valid_ip(self):
        # Si aucune IP n'est valide, il n'y a rien à analyser :
        # la fonction doit lever une ValueError au lieu de renvoyer une liste vide.
        with self.assertRaises(ValueError):
            parse_ips(["abc"])

    def test_mixed_versions(self):
        # Une IPv4 et une IPv6 ne peuvent pas être dans le même sous-réseau :
        # la fonction doit refuser ce mélange avec une ValueError.
        with self.assertRaises(ValueError):
            parse_ips(["10.0.0.1", "::1"])


class TestAwsCoverage(unittest.TestCase):
    """Sous-feature 3 : croisement d'un réseau avec les plages AWS."""

    def test_total(self):
        # 52.95.110.0/28 (16 adresses) est entièrement contenu dans le /24 AMAZON
        # et dans le /26 EC2 : la couverture est "totale".
        r = aws_coverage("52.95.110.0/28", FAKE_PREFIXES)
        self.assertEqual(r["status"], "totale")
        # Les deux plages emboîtées sont trouvées (le /24 AMAZON et le /26 EC2).
        self.assertEqual(len(r["matches"]), 2)

    def test_partial(self):
        # 52.95.0.0/16 est beaucoup plus grand que les plages AWS de la liste :
        # il les chevauche sans être contenu dedans, donc couverture "partielle".
        r = aws_coverage("52.95.0.0/16", FAKE_PREFIXES)
        self.assertEqual(r["status"], "partielle")

    def test_none(self):
        # 10.0.0.0/8 est un réseau privé, sans aucun lien avec AWS :
        # statut "aucune" et liste de correspondances vide.
        r = aws_coverage("10.0.0.0/8", FAKE_PREFIXES)
        self.assertEqual(r["status"], "aucune")
        self.assertEqual(r["matches"], [])

    def test_ipv6_ignored_against_ipv4_prefixes(self):
        # Un réseau IPv6 comparé à des plages IPv4 : subnet_of() lèverait
        # une TypeError. On vérifie que la fonction ignore ces plages
        # au lieu de planter, et renvoie "aucune".
        r = aws_coverage("2001:db8::/64", FAKE_PREFIXES)
        self.assertEqual(r["status"], "aucune")


if __name__ == "__main__":
    # Permet aussi de lancer le fichier directement : python test_awsip_group_a.py
    unittest.main()
