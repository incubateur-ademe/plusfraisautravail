/**
 * Type declarations for .publicodes file imports.
 *
 * These are handled by the publicodes Vite plugin which returns
 * their content as raw strings.
 */
declare module '*.publicodes' {
  const content: string
  export default content
}
