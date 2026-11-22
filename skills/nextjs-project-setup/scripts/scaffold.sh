#!/usr/bin/env bash
# Scaffold a Next.js BFF project managed by mise.
# Usage: bash scaffold.sh <target-dir>
# Writes only inside <target-dir>. Installs Node and pnpm through mise using the
# caller's mise settings; set MISE_DATA_DIR etc. to sandbox that.
set -euo pipefail

target="${1:?usage: scaffold.sh <target-dir>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
templates="$here/../templates"

command -v mise >/dev/null || { echo "mise is not installed" >&2; exit 1; }
[ -e "$target" ] && [ -n "$(ls -A "$target")" ] && { echo "$target exists and is not empty" >&2; exit 1; }

mkdir -p "$target"
target="$(cd "$target" && pwd)"

node_version="$(mise latest node@lts)"
pnpm_version="$(mise latest pnpm@10)"
echo "node $node_version, pnpm $pnpm_version"

# create-next-app refuses a directory holding mise.toml, so scaffold first and
# write mise.toml afterwards.
cd "$target"
mise exec "node@$node_version" "pnpm@$pnpm_version" -- \
  pnpm dlx create-next-app@latest . --ts --eslint --app --src-dir --tailwind \
  --import-alias "@/*" --use-pnpm --disable-git --yes

sed -e "s/__NODE__/$node_version/" -e "s/__PNPM__/$pnpm_version/" \
  "$templates/mise.toml" > mise.toml
mise trust --yes mise.toml 2>/dev/null || mise trust mise.toml
mise install

run() { mise exec -- "$@"; }

run pnpm add zod server-only @t3-oss/env-nextjs
node_major="${node_version%%.*}"
run pnpm add -D "@types/node@^$node_major" prettier prettier-plugin-tailwindcss eslint-plugin-simple-import-sort \
  typescript-eslint dependency-cruiser knip vitest @vitejs/plugin-react jsdom \
  @testing-library/react @testing-library/jest-dom @testing-library/user-event msw \
  @playwright/test @axe-core/playwright lefthook

cp "$templates/eslint.config.mjs" eslint.config.mjs
cp "$templates/.dependency-cruiser.cjs" .dependency-cruiser.cjs
cp "$templates/knip.json" knip.json
cp "$templates/lefthook.yml" lefthook.yml
cp "$templates/.prettierrc.json" .prettierrc.json
cp "$templates/.prettierignore" .prettierignore
cp "$templates/vitest.config.mts" vitest.config.mts
cp "$templates/playwright.config.ts" playwright.config.ts
mkdir -p e2e src/lib src/test src/features src/components src/generated
cp "$templates/e2e/home.spec.ts" e2e/
cp "$templates/src/lib/"* src/lib/
cp "$templates/src/test/"* src/test/
touch src/features/.gitkeep src/components/.gitkeep src/generated/.gitkeep
cat "$templates/AGENTS.section.md" >> AGENTS.md
printf '# Base URL of the backend service (server-side only)\nBACKEND_URL=http://localhost:8080\n' > .env.example
cp .env.example .env.local
grep -q '^!.env.example' .gitignore || printf '!.env.example\n' >> .gitignore
grep -qE '^/?playwright-report' .gitignore || printf 'playwright-report/\ntest-results/\n' >> .gitignore

# tsconfig flags and package.json fields; JSON is edited with node, not sed.
run node - <<EOF
const fs = require("node:fs");
const tsconfig = JSON.parse(fs.readFileSync("tsconfig.json", "utf8"));
Object.assign(tsconfig.compilerOptions, {
  noUncheckedIndexedAccess: true,
  noImplicitReturns: true,
  noFallthroughCasesInSwitch: true,
  noImplicitOverride: true,
  verbatimModuleSyntax: true,
});
fs.writeFileSync("tsconfig.json", JSON.stringify(tsconfig, null, 2) + "\n");
const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
pkg.engines = { node: ">=$node_major" };
pkg.packageManager = "pnpm@$pnpm_version";
pkg.scripts.lint = "eslint . --max-warnings 0";
fs.writeFileSync("package.json", JSON.stringify(pkg, null, 2) + "\n");
EOF

# Sort imports in the generated files, then format.
run pnpm exec eslint . --fix >/dev/null || true
run pnpm exec prettier --write . >/dev/null
[ -d .git ] && run pnpm exec lefthook install

echo "Scaffolded $target. Next: cd $target && mise run check"
