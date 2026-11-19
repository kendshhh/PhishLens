export default [
  { ignores: ["extension/vendor/**", "extension/model-assets/**", "web/dist/**"] },
  {
    files: ["extension/js/**/*.js", "extension/*.js", "extension/ai/*.mjs"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        document: "readonly",
        console: "readonly",
        fetch: "readonly",
        AbortSignal: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly", chrome: "readonly", crypto: "readonly",
        URL: "readonly", TextDecoder: "readonly", performance: "readonly",
        self: "readonly", navigator: "readonly", Worker: "readonly",
        Response: "readonly", ReadableStream: "readonly", setInterval: "readonly", clearInterval: "readonly"
      }
    },
    rules: {
      "no-undef": "error",
      "no-unused-vars": "error",
      "no-unreachable": "error",
      "no-dupe-keys": "error",
      "valid-typeof": "error",
      "eqeqeq": ["error", "always", { null: "ignore" }]
    }
  },
  {
    // The web app runs the shared modules in a normal page instead of an extension.
    files: ["web/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { queueMicrotask: "readonly", structuredClone: "readonly", sessionStorage: "readonly", URL: "readonly" }
    },
    rules: { "no-undef": "error", "no-unused-vars": "error", "eqeqeq": ["error", "always", { null: "ignore" }] }
  },
  {
    files: ["web/tests/*.mjs", "scripts/build_web.mjs", "scripts/serve_web.mjs"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { console: "readonly", process: "readonly", setTimeout: "readonly", URL: "readonly" }
    },
    rules: { "no-undef": "error", "no-unused-vars": "error" }
  },
  {
    // The observation sorter intentionally omits priority from the public result.
    files: ["extension/ai/observations.mjs"],
    rules: { "no-unused-vars": ["error", { "varsIgnorePattern": "^priority$", "argsIgnorePattern": "^priority$" }] }
  }
];
