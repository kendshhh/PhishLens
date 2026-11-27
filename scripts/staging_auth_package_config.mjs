import { runInNewContext } from 'node:vm';

const CONFIG_SOURCE_RE =
  /^export const AUTH_CONFIGS = Object\.freeze\((.*)\);\s*export const AUTH_CONFIG = AUTH_CONFIGS\.staging;\s*$/s;

export function readStagingAuthConfig(source) {
  const match = CONFIG_SOURCE_RE.exec(source);
  if (!match) {
    throw new Error('Staging archive must export AUTH_CONFIGS and default to its staging Auth config.');
  }
  const configurations = runInNewContext(`(${match[1]})`, Object.create(null), { timeout: 1000 });
  if (!configurations || typeof configurations !== 'object' ||
      !Object.hasOwn(configurations, 'staging')) {
    throw new Error('Staging archive Auth configuration map is invalid.');
  }
  return configurations.staging;
}
