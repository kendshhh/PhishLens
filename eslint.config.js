export default [
  { ignores: ["extension/vendor/**", "extension/model-assets/**"] },
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
    // Preserve the byte-identical benchmark explanation module. Its destructuring
    // intentionally omits priority from the public result.
    files: ["extension/ai/observations.mjs"],
    rules: { "no-unused-vars": ["error", { "varsIgnorePattern": "^priority$", "argsIgnorePattern": "^priority$" }] }
  }
];
