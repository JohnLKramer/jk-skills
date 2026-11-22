/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    { name: "no-circular", severity: "error", from: {}, to: { circular: true } },
    {
      name: "components-not-features",
      comment: "Global UI primitives must not know about features.",
      severity: "error",
      from: { path: "^src/components" },
      to: { path: "^src/features" },
    },
    {
      name: "app-not-api-client",
      comment: "Routes call feature api.ts, never the base client.",
      severity: "error",
      from: { path: "^src/app" },
      to: { path: "^src/lib/api-client" },
    },
    {
      name: "feature-isolation",
      comment: "A feature reaches another feature only through its index.ts.",
      severity: "error",
      from: { path: "^src/features/([^/]+)/" },
      to: {
        path: "^src/features/",
        pathNot: ["^src/features/$1/", "^src/features/[^/]+/index\\.ts$"],
      },
    },
  ],
  options: {
    tsConfig: { fileName: "tsconfig.json" },
    doNotFollow: { path: "node_modules" },
    exclude: { path: "\\.test\\.tsx?$|^src/generated" },
  },
};
