const featureNames = [
  'secret_disclosure', 'unsafe_entry', 'redirected_payment',
  'unverified_app_access', 'account_notification', 'address_confirmation',
];
const compiledPolicies = new WeakMap();

export function loadContextPolicy(spec) {
  if (compiledPolicies.has(spec)) return compiledPolicies.get(spec);
  if (spec.version !== 1 || JSON.stringify(spec.features) !== JSON.stringify(featureNames) ||
      spec.weights?.length !== featureNames.length || !spec.weights.every(Number.isFinite)) {
    throw new Error('Invalid context model');
  }
  const terms = Object.fromEntries(
    Object.entries(spec.patterns).map(([name, source]) => [name, new RegExp(source, 'i')]),
  );

  function correction(text) {
    const clauses = text.split(terms.clause_boundary);
    function directed(action, target) {
      const verbs = new RegExp(terms[action].source, 'gi');
      for (const clause of clauses) {
        for (const match of clause.matchAll(verbs)) {
          if (terms.negated_prefix.test(clause.slice(0, match.index))) continue;
          const end = match.index + match[0].length;
          const following = Array.from(clause.slice(end)).slice(0, 90).join('');
          if (terms[target].test(following)) return true;
        }
      }
      return false;
    }
    const attribution = terms.unverified_context.test(text);
    const secret = directed('disclosure_action', 'secret');
    const unsafeEntry = !secret && attribution && directed('entry_action', 'secret');
    const payment = attribution && directed('payment_action', 'payment_target');
    const appAccess = attribution && terms.app.test(text) &&
      directed('permission_action', 'permission_target');
    const hasRiskyAction = secret || unsafeEntry || payment || appAccess;
    const confirmation = !hasRiskyAction && terms.registration.test(text) &&
      terms.address.test(text) && terms.confirm_address.test(text);
    const notice = !hasRiskyAction && !confirmation &&
      terms.account_topic.test(text) && terms.account_event.test(text);
    const flags = [secret, unsafeEntry, payment, appAccess, notice, confirmation];
    return spec.weights.reduce((sum, weight, index) => sum + (flags[index] ? weight : 0), 0);
  }

  compiledPolicies.set(spec, correction);
  return correction;
}
