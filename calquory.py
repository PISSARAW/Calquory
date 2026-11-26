"""Construire un dossier minimal pour un double enregistrement de livraison."""
import argparse
import json
from pathlib import Path
from evidence_bundle import pack, replay_evidence

EVENTS = {"created", "delivered", "retry"}


def duplicate_delivery(rows):
    delivered = set()
    for row in rows:
        reference = row.get("order_id")
        if reference and row.get("event") == "delivered":
            if reference in delivered:
                return True
            delivered.add(reference)
    return False


def project(rows, policy):
    permitted = policy["allow"]
    if not isinstance(permitted, list) or not set(permitted) <= {"order_id", "event"}:
        raise ValueError("politique inconnue")
    aliases = {}
    sanitized = []
    for row in rows:
        ref, event = row["order_id"], row["event"]
        if not isinstance(ref, str) or not ref or event not in EVENTS:
            raise ValueError("événement ou référence invalide")
        alias = aliases.setdefault(ref, f"order-{len(aliases) + 1}")
        safe = {"order_id": alias, "event": event}
        sanitized.append({field: safe[field] for field in permitted})
    return sanitized


def reduce_case(rows, policy):
    if not isinstance(rows, list):
        raise ValueError("liste d'événements requise")
    safe = project(rows, policy)
    if not duplicate_delivery(rows):
        return {"status": "not_reproduced"}
    if not duplicate_delivery(safe):
        return {"status": "blocked_by_policy"}
    # Réduction gloutonne. Retirer toute ligne restante ferait disparaître le doublon.
    i = 0
    while i < len(safe):
        candidate = safe[:i] + safe[i + 1:]
        if duplicate_delivery(candidate):
            safe = candidate
        else:
            i += 1
    # Réattribuer les alias pour que leur numérotation ne révèle pas la taille du dossier.
    safe = project(safe, policy)
    return {"status": "ready", "oracle": "duplicate_delivery_v1", "events": safe}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    reduce = sub.add_parser("reduce")
    reduce.add_argument("events", type=Path)
    reduce.add_argument("policy", type=Path)
    replay = sub.add_parser("replay")
    replay.add_argument("bundle", type=Path)
    export = sub.add_parser("pack-timeline")
    export.add_argument("timeline", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "reduce":
            result = reduce_case(json.loads(args.events.read_text()), json.loads(args.policy.read_text()))
        elif args.command == "pack-timeline":
            print(json.dumps(pack(json.loads(args.timeline.read_text())), indent=2))
            raise SystemExit(0)
        else:
            bundle = json.loads(args.bundle.read_text())
            if bundle.get("schema") == "bundle.v1":
                print(json.dumps(replay_evidence(bundle), indent=2))
                raise SystemExit(0)
            if bundle.get("status") != "ready" or bundle.get("oracle") != "duplicate_delivery_v1":
                raise ValueError("dossier ou oracle inconnu")
            reproduced = duplicate_delivery(bundle["events"])
            result = {"status": "reproduced" if reproduced else "not_reproduced"}
    except (OSError, ValueError, KeyError, AttributeError, TypeError):
        parser.exit(2, "Format de dossier ou de politique invalide.\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["status"] in ("ready", "reproduced") else 1)


if __name__ == "__main__":
    main()
