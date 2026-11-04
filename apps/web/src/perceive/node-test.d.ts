/* Minimal node:test / node:assert typings for the perceive test only.
   @types/node is intentionally NOT a dependency (browser-first bundle);
   this shim covers exactly what events.test.ts uses. If @types/node is
   ever added, delete this file to avoid duplicate declarations. */

declare module "node:test" {
  export function describe(name: string, fn: () => void): void;
  export function it(name: string, fn: () => void): void;
}

declare module "node:assert/strict" {
  const assert: {
    (value: unknown, message?: string): void;
    ok(value: unknown, message?: string): void;
    equal(actual: unknown, expected: unknown, message?: string): void;
    deepEqual(actual: unknown, expected: unknown, message?: string): void;
  };
  export default assert;
}
