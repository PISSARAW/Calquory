"""Projection partageable de la chronologie privée et relecture des constats."""
import re


def check_id(key):
    if not isinstance(key, str) or not re.fullmatch(r"(revaskel|mandoryve)-[1-9][0-9]*", key):
        raise ValueError("identifiant interne inattendu")
    return key


def document_facts(key, expected, observed):
    for digest in [expected] + ([] if observed is None else [observed]):
        if not isinstance(digest, str) or not re.fullmatch("[a-f0-9]{64}", digest):
            raise ValueError("empreinte invalide")
    # Symboles locaux au constat. Seules l'égalité et l'absence sont conservées.
    return {"id": key, "kind": "document", "expected": 1,
            "observed": None if observed is None else 1 if observed == expected else 2}


def project_facts(event):
    key = check_id(event["id"])
    kind = event["kind"]
    facts = event["facts"]
    if key.startswith("revaskel-") != (kind == "document"):
        raise ValueError("producteur incompatible")
    if kind in ("verified", "unavailable") and facts == {}:
        return {"id": key, "kind": kind}
    expected, observed = facts["expected"], facts["observed"]
    if kind == "document":
        return document_facts(key, expected, observed)
    if kind != "access":
        raise ValueError("droits invalides")
    return access_facts(key, expected, observed)


def access_facts(key, expected, observed):
    if any(x is not None and type(x) is not int for x in (expected, observed)):
        raise ValueError("droits invalides")
    values = sorted({x for x in (expected, observed) if x is not None})
    ranks = {x: i for i, x in enumerate(values, 1)}
    return {"id": key, "kind": "access", "expected": ranks.get(expected), "observed": ranks.get(observed)}


def ordering(relations, ids):
    result = []
    seen = set()
    for relation in relations:
        if "before" in relation:
            a, b = relation["before"], relation["after"]
            public = {"before": a, "after": b}
        else:
            a, b = relation["undetermined"]
            public = {"undetermined": [a, b]}
        pair = frozenset((a, b))
        if len(pair) != 2 or not pair <= ids or pair in seen:
            raise ValueError("relation invalide")
        seen.add(pair)
        result.append(public)
    if len(seen) != len(ids) * (len(ids) - 1) // 2:
        raise ValueError("chronologie incomplète")
    return result


def pack(timeline):
    if timeline["schema"] != "timeline.v1" or timeline["timeline"]["status"] != "consistent":
        raise ValueError("chronologie incompatible")
    rows = [project_facts(event) for event in timeline["events"]]
    keys = {row["id"] for row in rows}
    if len(keys) != len(rows) or not keys:
        raise ValueError("observations vides ou dupliquées")
    relations = ordering(timeline["timeline"]["relations"], keys)
    return {"schema": "bundle.v1", "observations": rows, "relations": relations}


def verdict(row):
    kind = row["kind"]
    if kind in ("unavailable", "verified"):
        return "unknown" if kind == "unavailable" else "clear"
    expected, observed = row["expected"], row["observed"]
    if any(x is not None and (type(x) is not int or x not in (1, 2)) for x in (expected, observed)):
        raise ValueError("valeur projetée invalide")
    if kind == "document":
        return document_result(expected, observed)
    if kind != "access":
        raise ValueError("type inconnu")
    return access_result(expected, observed)


def document_result(expected, observed):
    if expected != 1:
        raise ValueError("document attendu invalide")
    if observed is None:
        return "missing_document"
    return "clear" if expected == observed else "digest_mismatch"


def access_result(expected, observed):
    if expected == observed:
        return "clear"
    if expected is None:
        return "extra_access"
    if observed is None:
        return "missing_access"
    return "longer_access" if observed > expected else "shorter_access"


def replay_evidence(bundle):
    if bundle["schema"] != "bundle.v1":
        raise ValueError("version incompatible")
    rows = bundle["observations"]
    results = {check_id(row["id"]): verdict(row) for row in rows}
    if not results or len(rows) != len(results):
        raise ValueError("observations vides ou dupliquées")
    relations = ordering(bundle["relations"], set(results))
    return {"schema": "review-input.v1", "observations": [
        {"id": key, "result": value} for key, value in results.items()], "relations": relations}
