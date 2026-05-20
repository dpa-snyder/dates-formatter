// The user manual is served as a static asset embedded in the binary.
// Rendering it in an iframe gives it full CSS isolation — it looks exactly
// as it does in a standalone browser, with its own fonts and design system.
export default function Manual() {
  return (
    <iframe
      className="manual-frame"
      src="/user-manual.html"
      title="Date Formatter User Manual"
    />
  )
}
