"""Context features for the text-only candidate shared with the extension."""

import math
import re


FEATURES = ("secret_disclosure", "unsafe_entry", "redirected_payment",
            "unverified_app_access", "account_notification", "address_confirmation")


class ContextPolicy:
    def __init__(self, spec):
        if spec["version"] != 1 or tuple(spec["features"]) != FEATURES:
            raise ValueError("Unsupported context feature specification")
        self.weights = tuple(spec["weights"])
        if len(self.weights) != len(FEATURES) or not all(map(math.isfinite, self.weights)):
            raise ValueError("Invalid context coefficients")
        self.terms = {
            name: re.compile(pattern, re.IGNORECASE | re.ASCII)
            for name, pattern in spec["patterns"].items()
        }

    def features(self, text):
        terms = self.terms
        clauses = terms["clause_boundary"].split(text)

        def directed(action, target):
            for clause in clauses:
                for match in terms[action].finditer(clause):
                    if terms["negated_prefix"].search(clause[:match.start()]):
                        continue
                    if terms[target].search(clause[match.end():match.end() + 90]):
                        return True
            return False

        attribution = bool(terms["unverified_context"].search(text))
        secret = directed("disclosure_action", "secret")
        unsafe_entry = not secret and attribution and directed("entry_action", "secret")
        payment = attribution and directed("payment_action", "payment_target")
        app_access = (
            attribution and bool(terms["app"].search(text)) and
            directed("permission_action", "permission_target")
        )
        has_risky_action = secret or unsafe_entry or payment or app_access
        confirmation = (
            not has_risky_action and bool(terms["registration"].search(text)) and
            bool(terms["address"].search(text)) and bool(terms["confirm_address"].search(text))
        )
        notice = (
            not has_risky_action and not confirmation and bool(terms["account_topic"].search(text)) and
            bool(terms["account_event"].search(text))
        )
        return secret, unsafe_entry, payment, app_access, notice, confirmation

    def correction(self, text):
        return sum(weight for weight, active in zip(self.weights, self.features(text), strict=True) if active)
