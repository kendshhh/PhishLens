export default [
  {
    files: ["extension/js/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        document: "readonly",
        console: "readonly",
        fetch: "readonly",
        AbortSignal: "readonly",
        setTimeout: "readonly"
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
  }
];